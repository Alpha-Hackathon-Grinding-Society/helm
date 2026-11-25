// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

import { Test } from "forge-std/Test.sol";
import { IPayable } from "@reactive/src/interfaces/IPayable.sol";
import { IERC20 } from "@openzeppelin/token/ERC20/IERC20.sol";
import { HelmVault, ILendingPool, ILpPool } from "../src/HelmVault.sol";
import { MockERC20 } from "../src/mocks/MockERC20.sol";
import { MockEthUsdcPool } from "../src/mocks/MockEthUsdcPool.sol";
import { MockLendingPool } from "../src/mocks/MockLendingPool.sol";

/// @notice The vault's own money paths: the deposit, the withdrawal and the pause.
/// @dev The reactive suite exercises the vault through callbacks. This suite covers the paths the
///      owner drives directly, because those are the branches a value-moving table has to account
///      for and they were not covered by a test of their own.
contract HelmVaultTest is Test {
    address internal constant PROXY = 0x476F44b11F5C942c58f4c8E3d0300E5710743585;

    address internal owner = makeAddr("owner");
    address internal stranger = makeAddr("stranger");
    address internal helm = makeAddr("helm");

    MockERC20 internal usd;
    MockEthUsdcPool internal lpPool;
    MockLendingPool internal lendingPool;
    HelmVault internal vault;

    uint256 internal constant START_PRICE = 2000e18;

    function setUp() public {
        vm.warp(1_700_000_000);

        usd = new MockERC20("Helm USD", "HUSD", owner);
        lpPool = new MockEthUsdcPool(usd, START_PRICE);
        lendingPool = new MockLendingPool(usd, 300, 240);

        vault = new HelmVault(
            IPayable(payable(PROXY)),
            helm,
            IERC20(address(usd)),
            ILendingPool(address(lendingPool)),
            ILpPool(address(lpPool)),
            owner
        );

        vm.prank(owner);
        usd.mint(owner, 1_000e18);
        vm.prank(owner);
        usd.approve(address(vault), type(uint256).max);
    }

    function _deposit(uint256 amount) internal {
        vm.prank(owner);
        vault.deposit(amount);
    }

    function test_TheOwnerCanDepositAndTheFundsAreLentOut() public {
        _deposit(1_000e18);
        assertEq(lendingPool.balanceOf(address(vault)), 1_000e18, "the deposit is supplied to the lending market");
        assertEq(vault.totalValueUsd(), 1_000e18, "the vault counts the supplied balance");
        assertEq(vault.asset().balanceOf(address(vault)), 0, "no idle balance is left behind");
    }

    function test_TheOwnerCanWithdrawPartOfTheVault() public {
        _deposit(1_000e18);
        vm.prank(owner);
        vault.withdraw(400e18, owner);
        assertEq(usd.balanceOf(owner), 400e18, "the owner received the withdrawal");
        assertEq(vault.totalValueUsd(), 600e18, "the vault is worth what is left");
    }

    function test_TheOwnerCanWithdrawEverything() public {
        _deposit(1_000e18);
        vm.prank(owner);
        vault.withdraw(1_000e18, owner);
        assertEq(usd.balanceOf(owner), 1_000e18, "the owner got the whole balance back");
        assertEq(vault.totalValueUsd(), 0, "the vault is empty");
    }

    function test_WithdrawingMoreThanTheVaultHoldsReverts() public {
        _deposit(1_000e18);
        vm.prank(owner);
        vm.expectRevert();
        vault.withdraw(1_000e18 + 1, owner);
    }

    function test_AStrangerCannotDepositOrWithdraw() public {
        vm.prank(owner);
        usd.mint(stranger, 1e18);
        vm.startPrank(stranger);
        usd.approve(address(vault), 1e18);
        vm.expectRevert();
        vault.deposit(1e18);
        vm.expectRevert();
        vault.withdraw(1, stranger);
        vm.stopPrank();
    }

    function test_APausedVaultRefusesDepositsAndCallbacksButLetsTheOwnerLeave() public {
        _deposit(500e18);

        vm.prank(owner);
        vault.setPaused(true);

        // A deposit is a new risk; a paused vault refuses it.
        vm.prank(owner);
        vm.expectRevert();
        vault.deposit(100e18);

        // So is a callback that would move the position.
        vm.prank(helm);
        vm.expectRevert();
        vault.rebalance(helm, 1, 4_000, 4_000, 0, 0);

        // Leaving is not. The owner can always get their money out: the pause is a brake on the
        // agent, not a lock on the user.
        uint256 before = usd.balanceOf(owner);
        vm.prank(owner);
        vault.withdraw(500e18, owner);
        assertEq(usd.balanceOf(owner), before + 500e18, "the owner withdrew while paused");
        assertEq(vault.totalValueUsd(), 0, "the vault is empty");
    }

    function test_PausingEmitsThePauseEvent() public {
        vm.expectEmit(true, false, false, true);
        emit HelmVault.Paused(owner, true);
        vm.prank(owner);
        vault.setPaused(true);
        assertTrue(vault.paused());
    }
}
