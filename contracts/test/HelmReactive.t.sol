// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

import { Test } from "forge-std/Test.sol";
import { Vm } from "forge-std/Vm.sol";
import { IERC20 } from "@openzeppelin/token/ERC20/IERC20.sol";
import { IPayable } from "@reactive/src/interfaces/IPayable.sol";
import { IReactive } from "@reactive/src/interfaces/IReactive.sol";
import { HelmReactive, HelmReject } from "../src/HelmReactive.sol";
import { HelmVault, ILendingPool, ILpPool } from "../src/HelmVault.sol";
import { HelmClamp, HelmAction } from "../src/HelmTypes.sol";
import { MockERC20 } from "../src/mocks/MockERC20.sol";
import { MockEthUsdcPool } from "../src/mocks/MockEthUsdcPool.sol";
import { MockLendingPool } from "../src/mocks/MockLendingPool.sol";
import { MockSystem } from "./MockSystem.sol";

/// @notice Test harness for the Helm reactive contract.
/// @dev The Reactive network is simulated: the test calls `react()` as the system contract and feeds it
///      the log records the network would have delivered. The callback proxy is simulated too: the
///      vault is deployed with the reactive contract as its callback sender, so a test can stand in
///      for the proxy and check that the vault only moves money when the reactive contract says so.
contract HelmReactiveTest is Test {
    address internal constant SYSTEM = 0x8888888888888888888888888888888888888888;
    address internal constant LEGACY_SYSTEM_ADDR = 0x0000000000000000000000000000000000fffFfF;
    address internal constant PROXY = 0x476F44b11F5C942c58f4c8E3d0300E5710743585;

    address internal owner = makeAddr("owner");
    address internal agent = makeAddr("agent");
    address internal stranger = makeAddr("stranger");

    MockSystem internal system;
    MockERC20 internal usd;
    MockEthUsdcPool internal lpPool;
    MockLendingPool internal lendingPool;
    HelmVault internal vault;
    HelmReactive internal helm;

    uint256 internal constant START_PRICE = 2000e18;

    function helmCronTopic() internal pure returns (uint256) {
        return 0xf02d6ea5c22a71cffe930a4523fcb4f129be6c804db50e4202fb4e0b07ccb514;
    }

    function setUp() public {
        vm.warp(1_700_000_000);

        // The reactive system contract lives at a fixed address; give it a body the tests can read.
        system = new MockSystem();
        vm.etch(SYSTEM, address(system).code);

        usd = new MockERC20("Helm USD", "HUSD", owner);
        lpPool = new MockEthUsdcPool(usd, START_PRICE);
        lendingPool = new MockLendingPool(usd, 300, 240);

        helm = new HelmReactive(owner, helmCronTopic());
        vault = new HelmVault(
            IPayable(payable(PROXY)),
            address(helm),
            IERC20(address(usd)),
            ILendingPool(address(lendingPool)),
            ILpPool(address(lpPool)),
            owner
        );

        vm.prank(owner);
        helm.configure(address(vault), address(lpPool), address(lendingPool));

        // A market maker seeds the pool so that price impact and fees behave like a real venue.
        vm.prank(owner);
        usd.mint(owner, 10_000e18);
        vm.startPrank(owner);
        usd.approve(address(lpPool), 10_000e18);
        lpPool.depositLiquidity(10_000e18, 10_000, owner);
        vm.stopPrank();

        vm.prank(owner);
        vault.setAgent(agent);
        // mirror the agent registration to the reactive contract
        _deliverAgentChanged(agent);
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                       Helpers                                                    */
    /* ------------------------------------------------------------------------------------------- */

    function _log(address contractAddress, uint256 topic0, uint256 topic1, uint256 topic2, bytes memory data)
        internal
        view
        returns (IReactive.LogRecord memory)
    {
        return IReactive.LogRecord({
            chainId: 84532,
            contractAddress: contractAddress,
            topic0: topic0,
            topic1: topic1,
            topic2: topic2,
            topic3: 0,
            data: data,
            blockNumber: block.number,
            opCode: 0,
            blockHash: 0,
            txHash: 0,
            logIndex: 0
        });
    }

    function _cron() internal view returns (IReactive.LogRecord memory) {
        // cron events are emitted by the legacy cron emitter
        return _log(LEGACY_SYSTEM_ADDR, helm.cronTopic(), 0, 0, "");
    }

    function _swap(uint256 price, uint256 usdcIn) internal view returns (IReactive.LogRecord memory) {
        return _log(address(lpPool), helm.TOPIC_SWAP(), 0, 0, abi.encode(price, usdcIn, int256(0)));
    }

    function _rate(uint256 rate) internal view returns (IReactive.LogRecord memory) {
        return _log(address(lendingPool), helm.TOPIC_RATE(), 0, 0, abi.encode(rate, rate * 8 / 10));
    }

    function _feeRate(uint256 fee) internal view returns (IReactive.LogRecord memory) {
        return _log(address(lpPool), helm.TOPIC_FEE_RATE(), 0, 0, abi.encode(fee));
    }

    function _limits(
        uint256 lpMin,
        uint256 lpMax,
        uint256 rangeMin,
        uint256 rangeMax,
        uint256 cooldown,
        uint256 volExit,
        uint256 minTrade,
        uint256 freshness
    ) internal view returns (IReactive.LogRecord memory) {
        return _log(
            address(vault),
            helm.TOPIC_LIMITS(),
            0,
            0,
            abi.encode(lpMin, lpMax, rangeMin, rangeMax, cooldown, volExit, minTrade, freshness)
        );
    }

    function _proposal(address proposer, uint256 cid, uint256 lp, uint256 rangeWidth, uint256 fVol, uint256 fRate)
        internal
        view
        returns (IReactive.LogRecord memory)
    {
        return _log(
            address(vault),
            helm.TOPIC_PROPOSAL(),
            uint256(uint160(proposer)),
            cid,
            abi.encode(lp, rangeWidth, fVol, fRate, block.timestamp)
        );
    }

    function _deliver(IReactive.LogRecord memory l) internal {
        vm.prank(SYSTEM);
        helm.react(l);
    }

    function _deliverAgentChanged(address newAgent) internal {
        _deliver(_log(address(vault), helm.TOPIC_AGENT(), uint256(uint160(agent)), uint256(uint160(newAgent)), ""));
    }

    function _setLimits(
        uint256 lpMin,
        uint256 lpMax,
        uint256 rangeMin,
        uint256 rangeMax,
        uint256 cooldown,
        uint256 volExit,
        uint256 minTrade,
        uint256 freshness
    ) internal {
        _deliver(_limits(lpMin, lpMax, rangeMin, rangeMax, cooldown, volExit, minTrade, freshness));
    }

    /// @dev Trade on the pool for real, then deliver the log the Reactive network would have delivered.
    function _trade(uint256 usdcIn) internal {
        vm.prank(owner);
        usd.mint(owner, usdcIn);
        vm.startPrank(owner);
        usd.approve(address(lpPool), usdcIn);
        lpPool.swap(usdcIn);
        vm.stopPrank();
        _deliver(_swap(lpPool.priceE18(), usdcIn));
    }

    /// @dev Deliver a price print and a fee-paying swap so the contract has a measured fee edge.
    function _observeHealthyMarket() internal {
        _deliver(_swap(START_PRICE, 0));
        _trade(50e18);
        vm.warp(block.timestamp + 600);
        _deliver(_rate(10));
    }

    function _fundVault(uint256 amount) internal {
        vm.prank(owner);
        usd.mint(owner, amount);
        vm.startPrank(owner);
        usd.approve(address(vault), amount);
        vault.deposit(amount);
        vm.stopPrank();
    }

    /// @dev Stand in for the callback proxy: deliver the rebalance the reactive contract asked for.
    function _executeVaultRebalance(uint256 cid, uint256 lp, uint256 rangeWidth, uint8 action, uint8 mask) internal {
        vm.prank(address(helm));
        vault.rebalance(address(helm), cid, lp, rangeWidth, action, mask);
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                  Market and vault plumbing                                     */
    /* ------------------------------------------------------------------------------------------- */

    function test_LimitsAreMirroredFromTheVault() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1500, 200, 600);
        assertTrue(helm.limitsSet());
        (uint256 lpMin, uint256 lpMax,,, , uint256 volExit,,) = helm.limits();
        assertEq(lpMin, 1000);
        assertEq(lpMax, 6000);
        assertEq(volExit, 1500);
    }

    function test_CronOpensACycle() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1500, 200, 600);
        _deliver(_cron());
        assertEq(helm.cycleId(), 1);
        assertEq(helm.pendingCycleId(), 1);
        assertGt(helm.pendingRequestedAt(), 0);
    }

    function test_CronHonoursTheCooldown() public {
        _setLimits(1000, 6000, 500, 4000, 3600, 1500, 200, 600);
        _deliver(_cron());
        assertEq(helm.cycleId(), 1);
        vm.warp(block.timestamp + 60);
        _deliver(_cron());
        assertEq(helm.cycleId(), 1, "a second cycle opened inside the cooldown");
        vm.warp(block.timestamp + 3600);
        _deliver(_cron());
        assertEq(helm.cycleId(), 2);
    }

    /// @dev The fee yield is measured over the period the contract was actually watching the
    ///      market. An idle spell before the first swap must not dilute the measurement for ever.
    function test_TheFeeWindowStartsWithTheFirstFeeTheContractSees() public {
        assertFalse(helm.feeEdgeMeasured(), "the contract measured an edge before it saw a swap");
        assertEq(helm.periodStart(), 0);

        // a long idle spell, then the market starts moving
        vm.warp(block.timestamp + 100_000);
        _deliver(_swap(START_PRICE, 0));
        _trade(50e18);
        assertEq(helm.periodStart(), block.timestamp, "the window did not start with the first fee");

        vm.warp(block.timestamp + 300);
        assertTrue(helm.feeEdgeMeasured());
        assertGt(helm.feeAprBps(), 0);
    }

    /// @dev The network charges lREACT for every call and drops the subscription when the contract
    ///      cannot pay, so the operator needs to see the call count and the runway.
    function test_TheNetworkCallCounterMoves() public {
        uint256 before = helm.reactCount();
        _deliver(_cron());
        assertEq(helm.reactCount(), before + 1);
        _deliver(_cron());
        assertEq(helm.reactCount(), before + 2);
        assertEq(helm.lastReactAt(), block.timestamp);
    }

    function test_FundingTheReserveIsVisible() public {
        vm.deal(address(this), 5 ether);
        vm.prank(address(this));
        helm.fund{ value: 3 ether }();
        assertEq(address(helm).balance, 3 ether);
        assertGt(helm.reserveCallsRemaining(), 0);
        assertTrue(helm.reserveHealthy());
    }

    /// @dev A cycle the model never answered must not freeze the fund manager. The owner needs a
    ///      way out that does not depend on the network calling the contract again.
    function test_TheOwnerCanExpireAPendingCycle() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1500, 200, 600);
        _deliver(_cron());
        assertEq(helm.pendingCycleId(), 1);

        vm.prank(owner);
        helm.expirePendingCycle();
        assertEq(helm.pendingCycleId(), 0, "the pending cycle was not written off");

        vm.warp(block.timestamp + 3600);
        _deliver(_cron());
        assertEq(helm.cycleId(), 2, "a new cycle did not open after the write-off");
    }

    /// @dev The freshness window is what makes a late proposal a rejection. Once it has closed, the
    ///      cron tick must write the cycle off so the next one can open.
    function test_AnUnansweredCycleIsWrittenOffWhenItsFreshnessWindowCloses() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1500, 200, 600);
        _deliver(_cron());
        assertEq(helm.pendingCycleId(), 1);

        vm.warp(block.timestamp + 601);
        _deliver(_cron());
        assertEq(helm.cycleId(), 2);
        assertEq(helm.pendingCycleId(), 2);
    }

    function test_RateAndPriceAreObserved() public {
        _deliver(_rate(450));
        _deliver(_swap(START_PRICE + 1e18, 0));
        assertEq(helm.rateBps(), 450);
        assertEq(helm.lastPriceE18(), START_PRICE + 1e18);
    }

    function test_CronRequestsADecisionCallbackWithTheInjectionSlot() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1500, 200, 600);
        MockSystem live = MockSystem(SYSTEM);
        uint256 before = live.requestCount();
        _deliver(_cron());

        assertEq(live.requestCount(), before + 1);
        (uint256 chainId, address recipient,, bytes memory args) = live.requestAt(before);
        assertEq(chainId, 84532);
        assertEq(recipient, address(vault));

        // the first word must be the reserved address slot the callback proxy overwrites
        (address slot, uint256 cbCycle, uint256 cbPrice, uint256 cbRate, uint256 cbVol) =
            abi.decode(args, (address, uint256, uint256, uint256, uint256));
        assertEq(slot, address(0));
        assertEq(cbCycle, 1);
        assertEq(cbPrice, 0);
        assertEq(cbRate, 0);
        assertEq(cbVol, 0);

        assertEq(live.payloadSelector(before), HelmVault.requestDecision.selector);
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                 Proposal acceptance rules                                      */
    /* ------------------------------------------------------------------------------------------- */

    function test_ProposalFromTheRegisteredAgentIsAccepted() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _observeHealthyMarket();
        _deliver(_cron());

        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalEvaluated(1, 3000, 3000, 1000, 1000, HelmClamp.NONE, block.timestamp);
        _deliver(_proposal(agent, 1, 3000, 1000, 100, 300));

        assertEq(helm.currentLpShareBps(), 3000);
        assertEq(helm.pendingCycleId(), 0);
        assertTrue(helm.executedCycles(1));
    }

    function test_ProposalFromAStrangerIsRejected() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _observeHealthyMarket();
        _deliver(_cron());

        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalRejected(1, HelmReject.UNKNOWN_AGENT, stranger);
        _deliver(_proposal(stranger, 1, 3000, 1000, 100, 300));

        assertEq(helm.currentLpShareBps(), 0);
        assertFalse(helm.executedCycles(1));
    }

    function test_ProposalForTheWrongCycleIsRejected() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _observeHealthyMarket();
        _deliver(_cron());

        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalRejected(7, HelmReject.CYCLE_MISMATCH, agent);
        _deliver(_proposal(agent, 7, 3000, 1000, 100, 300));
    }

    function test_StaleProposalIsRejected() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _observeHealthyMarket();
        _deliver(_cron());
        vm.warp(block.timestamp + 601);

        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalRejected(1, HelmReject.STALE, agent);
        _deliver(_proposal(agent, 1, 3000, 1000, 100, 300));
    }

    function test_ProposalPreparedBeforeTheCycleOpenedIsRejected() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _observeHealthyMarket();
        _deliver(_cron());
        vm.warp(block.timestamp + 10);

        IReactive.LogRecord memory l = _proposal(agent, 1, 3000, 1000, 100, 300);
        l.data = abi.encode(3000, 1000, 100, 300, block.timestamp - 300);
        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalRejected(1, HelmReject.BAD_INPUT, agent);
        _deliver(l);
    }

    function test_ReplayIsRejected() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _observeHealthyMarket();
        _deliver(_cron());
        _deliver(_proposal(agent, 1, 3000, 1000, 100, 300));

        // The cycle is spent, so the replay no longer answers an open cycle.
        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalRejected(1, HelmReject.CYCLE_MISMATCH, agent);
        _deliver(_proposal(agent, 1, 3000, 1000, 100, 300));
        assertTrue(helm.executedCycles(1));
    }

    function test_ProposalWithoutLimitsIsRejected() public {
        _deliver(_cron());
        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalRejected(1, HelmReject.NO_LIMITS, agent);
        _deliver(_proposal(agent, 1, 3000, 1000, 100, 300));
    }

    function test_PausedVaultRejectsProposals() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _deliver(_log(address(vault), helm.TOPIC_PAUSED(), 0, 0, abi.encode(true)));
        _deliver(_cron());

        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalRejected(1, HelmReject.PAUSED, agent);
        _deliver(_proposal(agent, 1, 3000, 1000, 100, 300));
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                   Clamping rules                                               */
    /* ------------------------------------------------------------------------------------------- */

    function test_LpShareAboveTheMaximumIsClamped() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _observeHealthyMarket();
        _deliver(_cron());

        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalEvaluated(1, 9000, 6000, 1000, 1000, HelmClamp.LP_ABOVE_MAX, block.timestamp);
        _deliver(_proposal(agent, 1, 9000, 1000, 100, 300));
        assertEq(helm.currentLpShareBps(), 6000);
    }

    function test_LpShareBelowTheMinimumIsClamped() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _observeHealthyMarket();
        _deliver(_cron());

        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalEvaluated(1, 100, 1000, 1000, 1000, HelmClamp.LP_BELOW_MIN, block.timestamp);
        _deliver(_proposal(agent, 1, 100, 1000, 100, 300));
        assertEq(helm.currentLpShareBps(), 1000);
    }

    function test_RangeWidthIsClampedOnBothSides() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _observeHealthyMarket();
        _deliver(_cron());

        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalEvaluated(1, 3000, 3000, 9000, 4000, HelmClamp.RANGE_ABOVE_MAX, block.timestamp);
        _deliver(_proposal(agent, 1, 3000, 9000, 100, 300));

        vm.warp(block.timestamp + 3600);
        _deliver(_cron());
        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalEvaluated(2, 3000, 3000, 100, 500, HelmClamp.RANGE_BELOW_MIN, block.timestamp);
        _deliver(_proposal(agent, 2, 3000, 100, 100, 300));
    }

    function test_MultipleClampsAreCombined() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _observeHealthyMarket();
        _deliver(_cron());

        uint8 expected = HelmClamp.LP_ABOVE_MAX | HelmClamp.RANGE_ABOVE_MAX;
        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalEvaluated(1, 9000, 6000, 9000, 4000, expected, block.timestamp);
        _deliver(_proposal(agent, 1, 9000, 9000, 100, 300));
    }

    function test_NoTradeBelowTheMinimumTradeSizeIsSkipped() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _observeHealthyMarket();
        _deliver(_cron());
        _deliver(_proposal(agent, 1, 3000, 1000, 100, 300));
        assertEq(helm.currentLpShareBps(), 3000);

        vm.warp(block.timestamp + 3600);
        _deliver(_cron());
        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.NoTrade(2, 3000, 3100, HelmClamp.NONE);
        _deliver(_proposal(agent, 2, 3100, 1000, 100, 300));

        assertEq(helm.currentLpShareBps(), 3000, "the position moved when it should not have");
        assertTrue(helm.executedCycles(2));
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                          Autonomous exit and the economic veto                                */
    /* ------------------------------------------------------------------------------------------- */

    function test_AutonomousExitWhenVolatilityBreaksTheExitLevel() public {
        _setLimits(1000, 6000, 500, 4000, 60, 100, 200, 600);
        _observeHealthyMarket();
        _deliver(_cron());
        _deliver(_proposal(agent, 1, 3000, 1000, 100, 300));
        assertEq(helm.currentLpShareBps(), 3000);

        // a violent move: the price jumps by a third in one print
        uint256 violentPrice = lpPool.priceE18() * 130 / 100;
        vm.recordLogs();
        _deliver(_swap(violentPrice, 0));

        assertEq(helm.currentLpShareBps(), 0, "the contract did not pull out of LP by itself");
        assertEq(helm.lastExecutedCycleId(), 2);

        // the exit is on the record
        Vm.Log[] memory logs = vm.getRecordedLogs();
        bool found;
        for (uint256 i = 0; i < logs.length; i++) {
            if (logs[i].emitter == address(helm) && logs[i].topics[0] == HelmReactive.AutonomousExit.selector) {
                found = true;
                assertEq(uint256(logs[i].topics[1]), 2);
                assertGt(abi.decode(logs[i].data, (uint256)), 100); // the volatility that triggered it
            }
        }
        assertTrue(found, "no AutonomousExit event was emitted");
    }

    function test_EconomicVetoKeepsTheVaultOutOfLp() public {
        // lending at 500bps and no fee flow the contract can measure
        _setLimits(0, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _deliver(_rate(500));
        _deliver(_cron());

        uint8 expected = HelmClamp.ECONOMIC_VETO;
        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalEvaluated(1, 3000, 0, 1000, 1000, expected, block.timestamp);
        _deliver(_proposal(agent, 1, 3000, 1000, 100, 300));
        assertEq(helm.currentLpShareBps(), 0);
    }

    function test_EconomicVetoDoesNotFireWhenFeesBeatLending() public {
        _setLimits(0, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _observeHealthyMarket();
        assertGt(helm.feeEdgeBps(), helm.minFeeEdgeBps(), "the contract did not measure a fee edge");
        _deliver(_cron());

        uint8 expected = HelmClamp.NONE;
        vm.expectEmit(true, true, true, true, address(helm));
        emit HelmReactive.ProposalEvaluated(1, 3000, 3000, 1000, 1000, expected, block.timestamp);
        _deliver(_proposal(agent, 1, 3000, 1000, 100, 300));
        assertEq(helm.currentLpShareBps(), 3000);
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                    Forecast grading                                            */
    /* ------------------------------------------------------------------------------------------- */

    function test_ForecastIsGradedOnTheNextCycle() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _observeHealthyMarket();
        _deliver(_cron());
        // the model forecasts 400 bps of volatility and a 250 bps fee yield
        _deliver(_proposal(agent, 1, 3000, 1000, 400, 250));

        vm.warp(block.timestamp + 3600);
        _deliver(_rate(350));
        _deliver(_cron());

        assertEq(helm.gradedForecasts(), 1);

        // the volatility error is measured against the volatility the contract observed
        uint256 realizedVol = helm.volEwmaQ() / 1e4;
        uint256 expectedVolErr = 400 > realizedVol ? 400 - realizedVol : realizedVol - 400;
        assertEq(helm.volMaeAccum(), expectedVolErr);
        assertEq(helm.volMaeBps(), expectedVolErr);

        // the yield error is measured against the fee yield the market actually paid
        uint256 realizedYield = helm.feeAprBps();
        uint256 expectedYieldErr = 250 > realizedYield ? 250 - realizedYield : realizedYield - 250;
        assertEq(helm.yieldMaeAccum(), expectedYieldErr);
        assertEq(helm.yieldMaeBps(), expectedYieldErr);
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                      End to end                                                */
    /* ------------------------------------------------------------------------------------------- */

    function test_EndToEndMoveMovesRealFunds() public {
        _setLimits(1000, 6000, 500, 4000, 60, 1_000_000, 200, 600);
        _fundVault(100e18);
        _observeHealthyMarket();

        _deliver(_cron());
        _deliver(_proposal(agent, 1, 3000, 1000, 100, 300));

        // the reactive contract asked for this rebalance; deliver it as the proxy would
        _executeVaultRebalance(1, 3000, 1000, HelmAction.FROM_MODEL, HelmClamp.NONE);

        uint256 total = vault.totalValueUsd();
        assertApproxEqAbs(total, 100e18, 1e16, "the vault lost value");
        assertApproxEqAbs(vault.lpShareBps(), 3000, 5, "the LP share is not 30%");
        assertGt(lpPool.lpValue(address(vault)), 0, "no liquidity was actually supplied");
    }

    function test_AutonomousExitMovesRealFundsOutOfThePool() public {
        _setLimits(1000, 6000, 500, 4000, 60, 100, 200, 600);
        _fundVault(100e18);
        _observeHealthyMarket();

        _deliver(_cron());
        _deliver(_proposal(agent, 1, 3000, 1000, 100, 300));
        _executeVaultRebalance(1, 3000, 1000, HelmAction.FROM_MODEL, HelmClamp.NONE);
        assertGt(lpPool.lpValue(address(vault)), 0);

        _deliver(_swap(START_PRICE * 130 / 100, 0));
        _executeVaultRebalance(2, 0, 1000, HelmAction.AUTONOMOUS_EXIT, HelmClamp.VOLATILITY_EXIT);

        assertEq(lpPool.lpValue(address(vault)), 0, "the LP position was not closed");
        assertApproxEqAbs(vault.lendingShareBps(), 10_000, 5, "the funds did not go back to lending");
    }

    /// @dev The live envelope: a 100,000 USD vault, a 40% cap and a 4,000 bps band. This is the
    ///      exact shape the testnet run used, and the exact shape that silently failed when the
    ///      callback gas limit was too low: the rebalance reverted inside the callback, the vault
    ///      never took the position, and the chain showed a rebalance request with no funds moved.
    function test_TheLiveEnvelopeRebalanceFitsInsideTheCallbackGasLimit() public {
        _setLimits(0, 4000, 500, 4000, 20, 1200, 1000, 600);
        _fundVault(100_000e18);
        _observeHealthyMarket();

        _deliver(_cron());
        // the model asks for 71%, the envelope caps it at 40%
        _deliver(_proposal(agent, 1, 7102, 4000, 100, 300));

        uint256 before = gasleft();
        _executeVaultRebalance(1, 4000, 4000, HelmAction.FROM_MODEL, HelmClamp.LP_ABOVE_MAX);
        uint256 used = before - gasleft();

        assertLt(used, helm.CALLBACK_GAS_LIMIT(), "the rebalance does not fit in the callback budget");
        assertApproxEqAbs(vault.lpShareBps(), 4000, 5, "the LP share is not 40%");
        assertGt(lpPool.lpValue(address(vault)), 0, "no liquidity was actually supplied");
        assertGt(vault.lendingShareBps(), 0, "the rest of the vault is not in lending");
    }
}
