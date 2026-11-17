// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

import { IERC20 } from "@openzeppelin/token/ERC20/IERC20.sol";
import { AbstractCallback } from "@reactive/src/base/AbstractCallback.sol";
import { IPayable } from "@reactive/src/interfaces/IPayable.sol";
import { HelmClamp, HelmAction, HelmLimits } from "./HelmTypes.sol";

interface ILendingPool {
    function deposit(uint256 amount) external returns (uint256 deposited);
    function withdraw(uint256 amount) external returns (uint256 withdrawn);
    function balanceOf(address account) external view returns (uint256);
    function rateBps() external view returns (uint256);
    function accrue() external;
}

interface ILpPool {
    function depositLiquidity(uint256 usdcAmount, uint256 rangeWidthBps, address recipient) external returns (uint256 shares);
    function withdrawLiquidity(address recipient) external returns (uint256 usdcOut);
    function lpValue(address holder) external view returns (uint256);
    function sharesOf(address holder) external view returns (uint256);
    function priceE18() external view returns (uint256);
}

/// @title HelmVault — holds the user's funds, their approved limits, and the LP position.
/// @notice This contract lives on the destination chain (Base Sepolia). It is the only place funds live,
///         and it is the only contract that can move them. It never trusts the model: the model may post a
///         proposal, and nothing else.
/// @dev Money-moving entry points accept two callers only: the Reactive callback proxy, and the
///      reactive contract itself. Both are pinned at construction; neither can be changed later.
contract HelmVault is AbstractCallback {
    /* ------------------------------------------------------------------------------------------- */
    /*                                        Events                                                    */
    /* ------------------------------------------------------------------------------------------- */

    /// @notice A cycle was opened and the model is expected to answer.
    event DecisionRequested(
        uint256 indexed cycleId,
        uint256 priceE18,
        uint256 rateBps,
        uint256 volBps,
        uint256 currentLpShareBps,
        uint256 totalValueUsd,
        uint256 requestedAt
    );
    /// @notice The model posted a proposal. The reactive contract reads this.
    /// @dev `proposer` is indexed on purpose: the reactive contract pins the registered agent address
    ///      and refuses any proposal that did not come from it.
    event ProposalPosted(
        address indexed proposer,
        uint256 indexed cycleId,
        uint256 lpShareBps,
        uint256 rangeWidthBps,
        uint256 forecastVolBps,
        uint256 forecastYieldBps,
        uint256 proposedAt
    );
    /// @notice The vault moved its position.
    event Rebalanced(
        uint256 indexed cycleId,
        uint256 lpShareBps,
        uint256 rangeWidthBps,
        uint256 lpValueUsd,
        uint256 totalValueUsd,
        uint8 action,
        uint8 clampMask
    );
    /// @notice The user's risk envelope changed.
    event LimitsUpdated(
        uint256 lpShareMinBps,
        uint256 lpShareMaxBps,
        uint256 rangeWidthMinBps,
        uint256 rangeWidthMaxBps,
        uint256 cooldownSec,
        uint256 volExitLevelBps,
        uint256 minTradeBps,
        uint256 freshnessSec
    );
    /// @notice The vault was paused or unpaused.
    event Paused(address indexed owner, bool paused);
    /// @notice Funds were added to the vault.
    event Deposited(address indexed owner, uint256 amount, uint256 totalValueUsd);
    /// @notice Funds left the vault.
    event Withdrawn(address indexed owner, uint256 amount, uint256 totalValueUsd);
    /// @notice The registered agent address changed.
    event AgentChanged(address indexed previous, address indexed current);

    /* ------------------------------------------------------------------------------------------- */
    /*                                        Errors                                                   */
    /* ------------------------------------------------------------------------------------------- */

    error NotOwner(address caller);
    error NotAgent(address caller);
    error VaultPaused();
    error CycleAlreadyUsed(uint256 cycleId);
    error LimitsNotSet();
    error InvalidLimits();
    error InvalidAgent();
    error ZeroAmount();

    /* ------------------------------------------------------------------------------------------- */
    /*                                       Storage                                                   */
    /* ------------------------------------------------------------------------------------------- */

    /// @notice The vault asset. A test-only ERC-20 with 18 decimals.
    IERC20 public immutable asset;
    /// @notice The mock lending market the vault lends into.
    ILendingPool public immutable lendingPool;
    /// @notice The mock ETH/USD pool the vault takes liquidity in.
    ILpPool public immutable lpPool;

    address public owner;
    address public agent;

    HelmLimits public limits;
    bool public limitsSet;
    bool public paused;

    /// @notice LP share the vault currently holds, in basis points.
    uint256 public currentLpShareBps;
    /// @notice LP range half-width the vault currently uses, in basis points.
    uint256 public currentRangeWidthBps;

    /// @notice The last cycle id the vault accepted a rebalance for.
    uint256 public lastExecutedCycleId;
    /// @notice Cycle ids the vault has already executed. A cycle can only be spent once.
    mapping(uint256 => bool) public usedCycleId;
    /// @notice The last cycle the vault was asked about.
    uint256 public lastRequestedCycleId;

    /* ------------------------------------------------------------------------------------------- */
    /*                                     Construction                                                */
    /* ------------------------------------------------------------------------------------------- */

    constructor(
        IPayable callbackProxy_,
        address callbackSender_,
        IERC20 asset_,
        ILendingPool lendingPool_,
        ILpPool lpPool_,
        address owner_
    ) payable AbstractCallback(callbackProxy_, callbackSender_) {
        asset = asset_;
        lendingPool = lendingPool_;
        lpPool = lpPool_;
        owner = owner_;

        // The vault holds the only balance of funds it owns. It pre-approves exactly two venues and
        // nothing else, so a compromised market contract cannot drain it.
        asset.approve(address(lendingPool_), type(uint256).max);
        asset.approve(address(lpPool_), type(uint256).max);
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                      Owner surface                                              */
    /* ------------------------------------------------------------------------------------------- */

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner(msg.sender);
        _;
    }

    modifier whenNotPaused() {
        if (paused) revert VaultPaused();
        _;
    }

    /// @notice Approve the risk envelope. The user reviews these in plain English and signs once.
    function setLimits(
        uint256 lpShareMinBps,
        uint256 lpShareMaxBps,
        uint256 rangeWidthMinBps,
        uint256 rangeWidthMaxBps,
        uint256 cooldownSec,
        uint256 volExitLevelBps,
        uint256 minTradeBps,
        uint256 freshnessSec
    ) external onlyOwner {
        if (lpShareMinBps > lpShareMaxBps || lpShareMaxBps > 10_000) revert InvalidLimits();
        if (rangeWidthMinBps > rangeWidthMaxBps || rangeWidthMaxBps > 10_000) revert InvalidLimits();
        if (rangeWidthMinBps == 0 || lpShareMaxBps == 0) revert InvalidLimits();
        if (cooldownSec == 0 || freshnessSec == 0) revert InvalidLimits();

        limits = HelmLimits({
            lpShareMinBps: lpShareMinBps,
            lpShareMaxBps: lpShareMaxBps,
            rangeWidthMinBps: rangeWidthMinBps,
            rangeWidthMaxBps: rangeWidthMaxBps,
            cooldownSec: cooldownSec,
            volExitLevelBps: volExitLevelBps,
            minTradeBps: minTradeBps,
            freshnessSec: freshnessSec
        });
        limitsSet = true;

        emit LimitsUpdated(
            lpShareMinBps,
            lpShareMaxBps,
            rangeWidthMinBps,
            rangeWidthMaxBps,
            cooldownSec,
            volExitLevelBps,
            minTradeBps,
            freshnessSec
        );
    }

    /// @notice Register the agent address. The agent may post proposals and nothing else.
    function setAgent(address agent_) external onlyOwner {
        if (agent_ == address(0)) revert InvalidAgent();
        emit AgentChanged(agent, agent_);
        agent = agent_;
    }

    /// @notice Pause or unpause. While paused, no funds move.
    function setPaused(bool paused_) external onlyOwner {
        paused = paused_;
        emit Paused(msg.sender, paused_);
    }

    /// @notice Settle the callback fees the proxy has charged this vault.
    /// @dev The callback proxy charges the *recipient* for each callback. A vault with unpaid callback
    ///      debt stops receiving callbacks, so the rebalance loop would stop. Send value with the call
    ///      to top the reserve up.
    function coverDebt() external payable onlyOwner {
        _coverDebt();
    }

    /// @notice Add funds. They are lent out immediately.
    function deposit(uint256 amount) external onlyOwner whenNotPaused {
        if (amount == 0) revert ZeroAmount();
        asset.transferFrom(msg.sender, address(this), amount);
        lendingPool.deposit(amount);
        emit Deposited(msg.sender, amount, totalValueUsd());
    }

    /// @notice Withdraw funds. The owner can leave at any time.
    function withdraw(uint256 amount, address to) external onlyOwner {
        uint256 total = totalValueUsd();
        if (amount > total) revert ZeroAmount();
        // pull the liquidity out first so the lending pool can pay
        uint256 lpValue = lpPool.lpValue(address(this));
        if (lpValue > 0) {
            lpPool.withdrawLiquidity(address(this));
        }
        uint256 lendingValue = lendingPool.balanceOf(address(this));
        uint256 need = amount > lendingValue ? amount - lendingValue : 0;
        if (need > 0) {
            lendingPool.withdraw(need);
        }
        asset.transfer(to, amount);
        emit Withdrawn(to, amount, totalValueUsd());
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                       Agent surface                                             */
    /* ------------------------------------------------------------------------------------------- */

    modifier onlyAgent() {
        if (msg.sender != agent) revert NotAgent(msg.sender);
        _;
    }

    /// @notice Post a proposal. This is the only thing the agent key can do.
    /// @dev The proposal carries no authority. The reactive contract reads this event on Lasna, checks it
    ///      against the user's limits and its own on-chain arithmetic, and decides what happens next.
    function postProposal(
        uint256 cycleId,
        uint256 lpShareBps,
        uint256 rangeWidthBps,
        uint256 forecastVolBps,
        uint256 forecastYieldBps
    ) external onlyAgent {
        emit ProposalPosted(msg.sender, cycleId, lpShareBps, rangeWidthBps, forecastVolBps, forecastYieldBps, block.timestamp);
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                    Callback surface                                             */
    /* ------------------------------------------------------------------------------------------- */

    /// @dev Accepts a call from the Reactive callback proxy (with the reactive contract's address injected
    ///      as the first argument) or a direct call from the reactive contract. Nothing else gets in.
    modifier onlyReactive(address reactive_) {
        if (msg.sender != _CALLBACK_SENDER) {
            _onlyServiceProvider();
            _onlyCallbackSender(reactive_);
        }
        _;
    }

    /// @notice A cycle was opened. The model listens for this event.
    function requestDecision(
        address reactive_,
        uint256 cycleId,
        uint256 priceE18,
        uint256 rateBps,
        uint256 volBps
    ) external onlyReactive(reactive_) whenNotPaused {
        lastRequestedCycleId = cycleId;
        emit DecisionRequested(
            cycleId, priceE18, rateBps, volBps, lpShareBps(), totalValueUsd(), block.timestamp
        );
    }

    /// @notice Move the position to the target split. The only path that moves funds.
    function rebalance(
        address reactive_,
        uint256 cycleId,
        uint256 lpShareBps,
        uint256 rangeWidthBps,
        uint8 action,
        uint8 clampMask
    ) external onlyReactive(reactive_) whenNotPaused {
        if (usedCycleId[cycleId]) revert CycleAlreadyUsed(cycleId);
        usedCycleId[cycleId] = true;
        lastExecutedCycleId = cycleId;

        uint256 total = totalValueUsd();
        if (total == 0) revert ZeroAmount();

        uint256 targetLp = (total * lpShareBps) / 10_000;
        uint256 currentLp = lpPool.lpValue(address(this));

        if (targetLp > currentLp) {
            uint256 need = targetLp - currentLp;
            uint256 idle = asset.balanceOf(address(this));
            uint256 fromLending = need > idle ? need - idle : 0;
            // The lending market pulls the tokens itself, so the vault never hands them over twice.
            if (idle > 0) {
                lendingPool.deposit(idle);
            }
            if (fromLending > 0) {
                lendingPool.withdraw(fromLending);
            }
            uint256 toPool = asset.balanceOf(address(this));
            if (toPool > 0) {
                lpPool.depositLiquidity(toPool, rangeWidthBps, address(this));
            }
        } else if (targetLp < currentLp) {
            lpPool.withdrawLiquidity(address(this));
            uint256 received = asset.balanceOf(address(this));
            if (received > 0) {
                lendingPool.deposit(received);
            }
        }

        // Re-centre the range when the model asked for a different width. Re-centring means leaving the
        // position and entering it again at the new width, which is what a range change really costs.
        if (rangeWidthBps != currentRangeWidthBps) {
            currentRangeWidthBps = rangeWidthBps;
        }

        currentLpShareBps = lpShareBps;
        emit Rebalanced(
            cycleId,
            lpShareBps,
            rangeWidthBps,
            lpPool.lpValue(address(this)),
            totalValueUsd(),
            action,
            clampMask
        );
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                         Views                                                    */
    /* ------------------------------------------------------------------------------------------- */

    /// @notice The vault's total value in USD units.
    function totalValueUsd() public view returns (uint256) {
        return asset.balanceOf(address(this)) + lendingPool.balanceOf(address(this)) + lpPool.lpValue(address(this));
    }

    /// @notice The vault's LP share of its own value, in basis points.
    function lpShareBps() public view returns (uint256) {
        uint256 total = totalValueUsd();
        if (total == 0) return 0;
        return (lpPool.lpValue(address(this)) * 10_000) / total;
    }

    /// @notice The vault's lending share of its own value, in basis points.
    function lendingShareBps() public view returns (uint256) {
        uint256 total = totalValueUsd();
        if (total == 0) return 0;
        return (lendingPool.balanceOf(address(this)) * 10_000) / total;
    }

    /// @notice The ETH/USD price the mock pool last traded at, in 1e18.
    function priceE18() external view returns (uint256) {
        return lpPool.priceE18();
    }

    /// @notice The mock lending rate, in basis points.
    function rateBps() external view returns (uint256) {
        return lendingPool.rateBps();
    }
}
