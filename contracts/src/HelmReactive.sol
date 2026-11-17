// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

import { AbstractReactive } from "@reactive/src/base/AbstractReactive.sol";
import { ISystemContract } from "@reactive/src/interfaces/ISystemContract.sol";
import { HelmClamp, HelmAction, HelmLimits } from "./HelmTypes.sol";

/// @dev The slice of the vault this contract is allowed to call. The first argument of every payload
///      is reserved for the callback proxy to inject the calling reactive contract's address.
interface IHelmVaultCallback {
    function requestDecision(
        address reactive_,
        uint256 cycleId,
        uint256 priceE18,
        uint256 rateBps,
        uint256 volBps
    ) external;

    function rebalance(
        address reactive_,
        uint256 cycleId,
        uint256 lpShareBps,
        uint256 rangeWidthBps,
        uint8 action,
        uint8 clampMask
    ) external;
}

/// @notice Reasons a proposal was thrown away without touching the user's money.
library HelmReject {
    uint8 internal constant NONE = 0;
    /// @notice The proposal did not come from the registered agent.
    uint8 internal constant UNKNOWN_AGENT = 1 << 0;
    /// @notice The proposal answered a cycle that is not the open one.
    uint8 internal constant CYCLE_MISMATCH = 1 << 1;
    /// @notice The proposal arrived after the freshness window closed.
    uint8 internal constant STALE = 1 << 2;
    /// @notice The user has not approved a risk envelope yet.
    uint8 internal constant NO_LIMITS = 1 << 3;
    /// @notice The vault is paused.
    uint8 internal constant PAUSED = 1 << 4;
    /// @notice The cycle was already spent.
    uint8 internal constant REPLAY = 1 << 5;
    /// @notice The proposal itself was malformed, or was prepared before the cycle opened.
    uint8 internal constant BAD_INPUT = 1 << 6;
}

/// @title HelmReactive — the on-chain risk enforcer for the Helm vault.
/// @notice This contract lives on Reactive Lasna. It watches the destination chain (Base Sepolia),
///         opens a cycle, accepts exactly one proposal per cycle from the registered agent, and then
///         decides what the vault is allowed to do. The model has no authority here: it can propose,
///         and the envelope decides.
///
/// @dev Three independent layers stand between the model's proposal and the user's money:
///
///        1. **The user's envelope.** `LimitsUpdated` is mirrored from the vault, and every proposal
///           is clamped into `[lpShareMinBps, lpShareMaxBps]` and `[rangeWidthMinBps, rangeWidthMaxBps]`.
///        2. **On-chain volatility exit.** The contract derives realized volatility from the price
///           path it observes itself. Above the user's exit level it pulls the vault to 0% LP without
///           asking the model anything. This is the only direction the contract may move on its own,
///           and it only ever moves toward safety.
///        3. **On-chain economic veto.** The contract annualises the fee flow it observes in the pool
///           and compares it with the lending rate it observes. If liquidity provision does not beat
///           lending by the required margin, the vault is not put into LP at all.
///
///      Every rejection and every clamp is an event, so the whole decision is auditable from the
///      Reactive scan alone.
contract HelmReactive is AbstractReactive {
    /* ------------------------------------------------------------------------------------------- */
    /*                                       Configuration                                              */
    /* ------------------------------------------------------------------------------------------- */

    /// @notice Base Sepolia, the chain the vault and the markets live on.
    uint256 public constant DEST_CHAIN_ID = 84532;

    /// @notice The legacy system contract that emits the cron events.
    /// @dev Cron events do not come from the reactive system contract at 0x8888...88. They come
    ///      from the legacy cron emitter, and a subscription has to name it explicitly.
    address internal constant LEGACY_SYSTEM_ADDR = 0x0000000000000000000000000000000000fffFfF;

    /// @notice Every block on Lasna. The demo runs cycles on this cadence.
    uint256 public constant CRON_TOPIC_1 = 0xf02d6ea5c22a71cffe930a4523fcb4f129be6c804db50e4202fb4e0b07ccb514;

    /// @notice Every ten blocks on Lasna. One cycle a minute: the production cadence.
    uint256 public constant CRON_TOPIC_10 = 0x04463f7c1651e6b9774d7f85c85bb94654e3c46ca79b0c16fb16d4183307b687;

    /// @notice The lREACT the contract must keep to keep answering the network.
    uint256 public constant RESERVE_FLOOR = 1e17;

    /// @notice What the network charges for one call, in wei of lREACT.
    /// @dev Measured on Lasna: a cron tick costs 0.0125157 lREACT. The estimate is deliberately a
    ///      little pessimistic, so the runway number is never optimistic.
    uint256 public constant REACT_CHARGE_WEI = 1.3e16;

    /// @notice Gas forwarded with a callback to the vault.
    /// @dev The rebalance callback is the expensive one: it withdraws from lending, opens a
    ///      liquidity position, and settles the fee index, which measured 356,775 gas on the
    ///      testnet. Four hundred thousand left no room for the network's own callback
    ///      machinery, and the rebalance silently reverted. Two million is comfortable.
    uint64 public constant CALLBACK_GAS_LIMIT = 2_000_000;

    uint256 public constant TOPIC_SWAP = uint256(keccak256("Swap(uint256,uint256,uint256)"));
    uint256 public constant TOPIC_RATE = uint256(keccak256("RateUpdated(uint256,uint256)"));
    uint256 public constant TOPIC_FEE_RATE = uint256(keccak256("FeeRateUpdated(uint256)"));
    uint256 public constant TOPIC_PROPOSAL = uint256(keccak256("ProposalPosted(address,uint256,uint256,uint256,uint256,uint256,uint256)"));
    uint256 public constant TOPIC_LIMITS = uint256(keccak256("LimitsUpdated(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256)"));
    uint256 public constant TOPIC_PAUSED = uint256(keccak256("Paused(address,bool)"));
    uint256 public constant TOPIC_AGENT = uint256(keccak256("AgentChanged(address,address)"));

    /// @notice Owner of this contract. It can wire the vault and tune the economic parameters.
    address public owner;

    /// @notice The cron topic that opens cycles. Every block for the demo, every ten for production.
    uint256 public cronTopic;

    /// @notice The Helm vault on Base Sepolia.
    address public vault;
    /// @notice The ETH/USD pool on Base Sepolia.
    address public lpPool;
    /// @notice The lending market on Base Sepolia.
    address public lendingPool;

    /// @notice The registered agent. Mirrored from the vault's `AgentChanged` event.
    address public agent;

    /// @notice How much better liquidity provisioning must beat lending by, in basis points.
    uint256 public minFeeEdgeBps = 50;
    /// @notice How long the contract must observe the market before it trusts its own fee estimate.
    uint256 public minObservationSec = 300;
    /// @notice How long one fee observation window runs before it rolls over.
    uint256 public observationWindowSec = 3600;

    /* ------------------------------------------------------------------------------------------- */
    /*                                         Events                                                   */
    /* ------------------------------------------------------------------------------------------- */

    event VaultConfigured(address vault, address lpPool, address lendingPool);
    event LimitsMirrored(
        uint256 lpShareMinBps,
        uint256 lpShareMaxBps,
        uint256 rangeWidthMinBps,
        uint256 rangeWidthMaxBps,
        uint256 cooldownSec,
        uint256 volExitLevelBps,
        uint256 minTradeBps,
        uint256 freshnessSec
    );
    event AgentMirrored(address agent);
    event PausedMirrored(bool paused);
    event Funded(address indexed from, uint256 amount, uint256 newBalance);
    event CycleOpened(uint256 indexed cycleId, uint256 priceE18, uint256 rateBps, uint256 volBps, uint256 openedAt);
    event CycleExpired(uint256 indexed cycleId, uint256 waitedSec);
    event ProposalEvaluated(
        uint256 indexed cycleId,
        uint256 modelLpShareBps,
        uint256 finalLpShareBps,
        uint256 modelRangeWidthBps,
        uint256 finalRangeWidthBps,
        uint8 clampMask,
        uint256 evaluatedAt
    );
    event RebalanceRequested(
        uint256 indexed cycleId, uint256 lpShareBps, uint256 rangeWidthBps, uint8 action, uint8 clampMask, uint256 requestedAt
    );
    event ProposalRejected(uint256 indexed cycleId, uint8 reason, address proposer);
    event NoTrade(uint256 indexed cycleId, uint256 currentLpShareBps, uint256 targetLpShareBps, uint8 clampMask);
    event AutonomousExit(uint256 indexed cycleId, uint256 volBps, uint256 rangeWidthBps, uint256 exitedAt);
    event ForecastGraded(
        uint256 indexed cycleId, uint256 volErrBps, uint256 rateErrBps, uint256 realizedVolBps, uint256 realizedRateBps
    );
    event MarketObserved(uint256 priceE18, uint256 volBps, uint256 rateBps, uint256 feeAprBps);

    /* ------------------------------------------------------------------------------------------- */
    /*                                          Errors                                                  */
    /* ------------------------------------------------------------------------------------------- */

    error NotOwner(address caller);
    error AlreadyConfigured();
    error NotConfigured();

    /* ------------------------------------------------------------------------------------------- */
    /*                                        Storage                                                  */
    /* ------------------------------------------------------------------------------------------- */

    /// @notice The user's risk envelope, mirrored from the vault.
    HelmLimits public limits;
    /// @notice Whether the envelope has been mirrored yet.
    bool public limitsSet;
    /// @notice Whether the vault is paused.
    bool public paused;

    /// @notice Last observed ETH/USD price, in 1e18.
    uint256 public lastPriceE18;
    /// @notice Whether a price has been observed yet.
    bool public hasPrice;
    /// @notice EWMA of absolute returns, in bps scaled by 1e4.
    uint256 public volEwmaQ;
    /// @notice Number of price observations folded into the volatility estimate.
    uint256 public volSamples;
    /// @notice How many times the Reactive network has called this contract.
    /// @dev The network charges lREACT for every call and drops the subscription when the contract
    ///      cannot pay, so this counter is the health check for the whole loop.
    uint256 public reactCount;
    /// @notice When the network last called this contract.
    uint256 public lastReactAt;
    /// @notice Number of fee-paying swaps folded into the fee estimate.
    uint256 public feeSamples;
    /// @notice Observed lending rate, in basis points.
    uint256 public rateBps;
    /// @notice Observed swap fee rate, in basis points.
    uint256 public feeRateBps = 30;
    /// @notice Fees observed in the current window, in USD units.
    uint256 public periodFeeUsd;
    /// @notice Start of the current observation window.
    /// @dev Zero until the contract sees its first fee-paying swap. The window measures the fee
    ///      yield over the period the contract was actually watching the market, not over the time
    ///      since deployment, so an idle start does not dilute the measurement for ever.
    uint256 public periodStart;
    /// @notice Virtual book depth, derived from the price impact of the swaps we observe.
    uint256 public virtualLiquidityUsd;

    /// @notice The current cycle counter.
    uint256 public cycleId;
    /// @notice The cycle that is waiting for a proposal. Zero means none is open.
    uint256 public pendingCycleId;
    /// @notice When the open cycle was requested.
    uint256 public pendingRequestedAt;
    /// @notice When the last cycle was opened.
    uint256 public lastCycleAt;
    /// @notice LP share the vault currently holds, in basis points.
    uint256 public currentLpShareBps;
    /// @notice LP range width the vault currently uses, in basis points.
    uint256 public currentRangeWidthBps;
    /// @notice The last cycle that produced a position change.
    uint256 public lastExecutedCycleId;
    /// @notice Cycles that have already been spent.
    mapping(uint256 => bool) public executedCycles;

    /// @notice Running sum of absolute volatility forecast errors, in basis points.
    uint256 public volMaeAccum;
    /// @notice Running sum of absolute rate forecast errors, in basis points.
    uint256 public yieldMaeAccum;
    /// @notice Number of graded forecasts.
    uint256 public gradedForecasts;

    /// @notice The forecast waiting to be graded, and when it was made.
    uint256 public pendingForecastVolBps;
    uint256 public pendingForecastYieldBps;
    uint256 public pendingForecastCycleId;
    uint256 public pendingForecastAt;

    /* ------------------------------------------------------------------------------------------- */
    /*                                      Construction                                               */
    /* ------------------------------------------------------------------------------------------- */

    constructor(address owner_, uint256 cronTopic_) payable {
        owner = owner_;
        cronTopic = cronTopic_;
        // The cron tick is what opens a cycle. Cron events are emitted by the legacy cron
        // emitter, not by the reactive system contract, so that is the address to subscribe to.
        SYSTEM.subscribe(
            block.chainid, LEGACY_SYSTEM_ADDR, cronTopic_, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE
        );
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner(msg.sender);
        _;
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                       Owner surface                                             */
    /* ------------------------------------------------------------------------------------------- */

    /// @notice Point the contract at the vault and its markets, and subscribe to their events.
    /// @dev The subscriptions are pinned to these exact addresses. A proposal from any other contract
    ///      can never reach this code path.
    function configure(address vault_, address lpPool_, address lendingPool_) external onlyOwner {        if (vault != address(0)) revert AlreadyConfigured();
        if (vault_ == address(0) || lpPool_ == address(0) || lendingPool_ == address(0)) revert NotConfigured();

        vault = vault_;
        lpPool = lpPool_;
        lendingPool = lendingPool_;

        SYSTEM.subscribe(DEST_CHAIN_ID, lpPool_, TOPIC_SWAP, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        SYSTEM.subscribe(DEST_CHAIN_ID, lpPool_, TOPIC_FEE_RATE, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        SYSTEM.subscribe(DEST_CHAIN_ID, lendingPool_, TOPIC_RATE, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        SYSTEM.subscribe(DEST_CHAIN_ID, vault_, TOPIC_PROPOSAL, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        SYSTEM.subscribe(DEST_CHAIN_ID, vault_, TOPIC_LIMITS, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        SYSTEM.subscribe(DEST_CHAIN_ID, vault_, TOPIC_PAUSED, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        SYSTEM.subscribe(DEST_CHAIN_ID, vault_, TOPIC_AGENT, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);

        emit VaultConfigured(vault_, lpPool_, lendingPool_);
    }

    /// @notice Change the cycle cadence.
    /// @dev Every cron tick costs lREACT, so a slower topic keeps the contract running for longer.
    function setCronTopic(uint256 cronTopic_) external onlyOwner {
        SYSTEM.unsubscribe(
            block.chainid, LEGACY_SYSTEM_ADDR, cronTopic, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE
        );
        cronTopic = cronTopic_;
        SYSTEM.subscribe(
            block.chainid, LEGACY_SYSTEM_ADDR, cronTopic_, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE
        );
    }

    /// @notice Withdraw part of the lREACT reserve, leaving the floor intact.
    /// @dev The owner can recover funds when shutting Helm down, but cannot drain the contract below
    ///      the reserve that keeps the loop alive.
    function withdrawReserve(address payable to, uint256 amount) external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance - amount >= RESERVE_FLOOR, "reserve floor");
        (bool ok,) = to.call{value: amount}("");
        require(ok, "transfer failed");
    }

    /// @notice Settle the outstanding charge the Reactive network has against this contract.
    /// @dev A reactive contract that owes the system contract is not called again, so the loop stops.
    ///      This pays the debt with the lREACT held here. Send value with the call to top it up.
    function coverDebt() external payable onlyOwner {
        _coverDebt();
    }

    /// @notice Top the lREACT reserve up. The network charges for every call, so the reserve is fuel.
    /// @dev This is the single most important operational fact about a Reactive contract: when the
    ///      balance runs out the network stops calling it, and the subscription is not restored by
    ///      paying later. The counter and the balance are the two numbers to watch.
    function fund() external payable {
        emit Funded(msg.sender, msg.value, address(this).balance);
    }

    /// @notice Write off the cycle that is waiting for a proposal, so a new one can open.
    /// @dev The cron tick expires an unanswered cycle on its own once the freshness window closes.
    ///      This is the owner's manual escape hatch for the case where the network stopped calling
    ///      the contract while a cycle was open.
    function expirePendingCycle() external onlyOwner {
        if (pendingCycleId == 0) return;
        emit CycleExpired(pendingCycleId, block.timestamp - pendingRequestedAt);
        pendingCycleId = 0;
    }

    /// @notice Whether the contract still has enough lREACT to keep answering the network.
    /// @dev Below the floor the network drops the subscription, so this is a page-me-now number.
    function reserveHealthy() external view returns (bool) {
        return address(this).balance >= RESERVE_FLOOR;
    }

    /// @notice How many more calls the reserve can pay for at the network's current charge.
    /// @dev The network charges roughly `REACT_CHARGE_WEI` per call, so this is the number of calls
    ///      left before the subscription is dropped. It is an estimate and it is labelled as one.
    function reserveCallsRemaining() external view returns (uint256) {
        return address(this).balance / REACT_CHARGE_WEI;
    }

    /// @notice Tune the economic guard rails.
    /// @param minFeeEdgeBps_ How much better liquidity provisioning must beat lending by.
    /// @param minObservationSec_ How long the contract must observe the market before it trusts its
    ///        own fee estimate.
    /// @param observationWindowSec_ How long one fee observation window runs before it rolls over.
    function setEconomicParams(uint256 minFeeEdgeBps_, uint256 minObservationSec_, uint256 observationWindowSec_)
        external
        onlyOwner
    {
        minFeeEdgeBps = minFeeEdgeBps_;
        minObservationSec = minObservationSec_;
        observationWindowSec = observationWindowSec_;
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                    Reactive entry point                                         */
    /* ------------------------------------------------------------------------------------------- */

    /// @notice Entry point for the Reactive network. Only the system contract may call it.
    function react(LogRecord calldata log_) external override onlySystem {
        reactCount += 1;
        lastReactAt = block.timestamp;

        // Settle any outstanding charge first. A reactive contract with debt is not called again, so
        // this is what keeps the loop alive.
        _coverDebt();

        uint256 t0 = log_.topic0;
        if (t0 == TOPIC_SWAP) {
            _onSwap(log_);
        } else if (t0 == TOPIC_RATE) {
            _onRate(log_);
        } else if (t0 == TOPIC_FEE_RATE) {
            _onFeeRate(log_);
        } else if (t0 == TOPIC_PROPOSAL) {
            _onProposal(log_);
        } else if (t0 == TOPIC_LIMITS) {
            _onLimits(log_);
        } else if (t0 == TOPIC_PAUSED) {
            _onPaused(log_);
        } else if (t0 == TOPIC_AGENT) {
            _onAgent(log_);
        } else if (t0 == cronTopic) {
            _onCron(log_);
        }
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                    Market observation                                           */
    /* ------------------------------------------------------------------------------------------- */

    /// @dev A swap moved the price. Update volatility, account for fees, and check the exit rule.
    function _onSwap(LogRecord calldata log_) internal {
        (uint256 price, uint256 usdcIn,) = abi.decode(log_.data, (uint256, uint256, uint256));
        if (price == 0) return;

        uint256 prevPrice = lastPriceE18;
        uint256 volBps = _updateVol(price);

        if (usdcIn > 0 && prevPrice > 0 && price > prevPrice) {
            // Derive the virtual book depth from the price impact of the swap itself:
            // P1 = P0 * (S + in) / S  =>  S = P1 * in / (P1 - P0).
            uint256 depth = (price * usdcIn) / (price - prevPrice);
            if (depth > 0) virtualLiquidityUsd = depth;
            // The observation window starts with the first fee the contract actually sees, and rolls
            // forward once it is older than the window itself.
            if (periodStart == 0) {
                periodStart = block.timestamp;
                periodFeeUsd = 0;
                feeSamples = 0;
            } else if (block.timestamp - periodStart > observationWindowSec) {
                periodStart = block.timestamp;
                periodFeeUsd = 0;
                feeSamples = 0;
            }
            periodFeeUsd += (usdcIn * feeRateBps) / 10_000;
            feeSamples += 1;
        }

        emit MarketObserved(price, volBps, rateBps, feeAprBps());

        // Layer 2: the contract acts on its own, without the model, when the market gets violent.
        if (limitsSet && !paused && volBps > limits.volExitLevelBps && currentLpShareBps > 0) {
            _autonomousExit(volBps);
        }
    }

    /// @dev Realized volatility as a smoothed mean of absolute returns, one sample per observed move.
    ///      The first ten samples are averaged (no warm-up bias), after that it is an EWMA with
    ///      alpha = 1/10.
    function _updateVol(uint256 price) internal returns (uint256 volBps) {
        if (!hasPrice || lastPriceE18 == 0) {
            lastPriceE18 = price;
            hasPrice = true;
            return volEwmaQ / 1e4;
        }
        uint256 diff = price > lastPriceE18 ? price - lastPriceE18 : lastPriceE18 - price;
        uint256 retQ = ((diff * 10_000) / lastPriceE18) * 1e4;
        volSamples += 1;
        uint256 n = volSamples < 10 ? volSamples : 10;
        volEwmaQ = (volEwmaQ * (n - 1) + retQ) / n;
        lastPriceE18 = price;
        return volEwmaQ / 1e4;
    }

    /// @dev The lending market published a new rate.
    function _onRate(LogRecord calldata log_) internal {
        (uint256 rate,) = abi.decode(log_.data, (uint256, uint256));
        rateBps = rate;
    }

    /// @dev The pool published a new fee rate.
    function _onFeeRate(LogRecord calldata log_) internal {
        (uint256 fee) = abi.decode(log_.data, (uint256));
        feeRateBps = fee;
    }

    /// @notice The annualised fee yield of the pool, derived from the swaps this contract observed.
    /// @dev `feeAprBps = fees observed / window / depth, annualised`. The contract does not trust a
    ///      pool-reported APR: it measures the flow itself.
    function feeAprBps() public view returns (uint256) {
        if (virtualLiquidityUsd == 0 || periodFeeUsd == 0 || periodStart == 0) return 0;
        uint256 elapsed = block.timestamp > periodStart ? block.timestamp - periodStart : 0;
        if (elapsed == 0) return 0;
        // fees * seconds-per-year * 10000 / (depth * elapsed)
        return (periodFeeUsd * 365 days * 10_000) / (virtualLiquidityUsd * elapsed);
    }

    /// @notice Whether the contract has enough fee evidence to make an economic call.
    /// @dev Below the observation floor the contract does not claim an edge it cannot measure, and it
    ///      takes the safe side: it does not put money into LP.
    function feeEdgeMeasured() public view returns (bool) {
        if (feeSamples == 0 || periodStart == 0 || virtualLiquidityUsd == 0) return false;
        uint256 elapsed = block.timestamp > periodStart ? block.timestamp - periodStart : 0;
        return elapsed >= minObservationSec;
    }

    /// @notice The fee edge over lending that the contract is willing to act on, in basis points.
    /// @dev Zero when the edge has not been measured yet: an unmeasured edge is not a positive edge.
    function feeEdgeBps() public view returns (uint256) {
        if (!feeEdgeMeasured()) return 0;
        uint256 apr = feeAprBps();
        return apr > rateBps ? apr - rateBps : 0;
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                     Vault state mirrors                                         */
    /* ------------------------------------------------------------------------------------------- */

    function _onLimits(LogRecord calldata log_) internal {
        (
            uint256 lpShareMinBps,
            uint256 lpShareMaxBps,
            uint256 rangeWidthMinBps,
            uint256 rangeWidthMaxBps,
            uint256 cooldownSec,
            uint256 volExitLevelBps,
            uint256 minTradeBps,
            uint256 freshnessSec
        ) = abi.decode(log_.data, (uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256));

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

        emit LimitsMirrored(
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

    function _onPaused(LogRecord calldata log_) internal {
        (bool paused_) = abi.decode(log_.data, (bool));
        paused = paused_;
        emit PausedMirrored(paused_);
    }

    function _onAgent(LogRecord calldata log_) internal {
        agent = address(uint160(log_.topic2));
        emit AgentMirrored(agent);
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                      Cycle lifecycle                                            */
    /* ------------------------------------------------------------------------------------------- */

    /// @dev Cron tick: open a cycle if the user has approved an envelope and the cooldown is over.
    function _onCron(LogRecord calldata) internal {
        if (vault == address(0) || !limitsSet || paused) return;
        if (pendingCycleId != 0) {
            // A cycle the model never answered must not freeze the fund manager. When its freshness
            // window closes, the cycle is written off and a new one is opened.
            if (block.timestamp <= pendingRequestedAt + limits.freshnessSec) return;
            emit CycleExpired(pendingCycleId, block.timestamp - pendingRequestedAt);
            pendingCycleId = 0;
        }
        if (block.timestamp < lastCycleAt + limits.cooldownSec) return;

        // The forecast made last cycle is now gradeable against what actually happened.
        _gradePendingForecast();

        uint256 cid = ++cycleId;
        pendingCycleId = cid;
        pendingRequestedAt = block.timestamp;
        lastCycleAt = block.timestamp;

        uint256 volBps = volEwmaQ / 1e4;
        emit CycleOpened(cid, lastPriceE18, rateBps, volBps, block.timestamp);
        _requestDecision(cid, lastPriceE18, rateBps, volBps);
    }

    /// @dev The first rule a proposal breaks, in priority order. Zero means it passed every rule.
    function _rejectReason(uint256 cid, address proposer, uint256 lpShareBps, uint256 rangeWidthBps, uint256 proposedAt)
        internal
        view
        returns (uint8)
    {
        if (!limitsSet) return HelmReject.NO_LIMITS;
        if (paused) return HelmReject.PAUSED;
        if (agent == address(0) || proposer != agent) return HelmReject.UNKNOWN_AGENT;
        if (pendingCycleId == 0 || cid != pendingCycleId) return HelmReject.CYCLE_MISMATCH;
        if (executedCycles[cid]) return HelmReject.REPLAY;
        if (block.timestamp > pendingRequestedAt + limits.freshnessSec) return HelmReject.STALE;
        if (lpShareBps > 10_000 || rangeWidthBps == 0 || rangeWidthBps > 10_000) return HelmReject.BAD_INPUT;
        // A proposal prepared before the cycle opened was not an answer to this cycle.
        if (proposedAt + 60 < pendingRequestedAt) return HelmReject.BAD_INPUT;
        return HelmReject.NONE;
    }

    /// @dev The model posted a proposal. Check it against every rule, then execute what is allowed.
    function _onProposal(LogRecord calldata log_) internal {
        address proposer = address(uint160(log_.topic1));
        uint256 cid = log_.topic2;
        (uint256 lpShareBps, uint256 rangeWidthBps, uint256 forecastVolBps, uint256 forecastYieldBps, uint256 proposedAt) =
            abi.decode(log_.data, (uint256, uint256, uint256, uint256, uint256));

        // The first rule that fires is the reason. One reason per rejection keeps the dashboard honest.
        uint8 reason = _rejectReason(cid, proposer, lpShareBps, rangeWidthBps, proposedAt);
        if (reason != HelmReject.NONE) {
            emit ProposalRejected(cid, reason, proposer);
            return;
        }

        // ---- Layer 1: the user's envelope ------------------------------------------------------------
        uint256 finalLp = lpShareBps;
        uint256 finalRange = rangeWidthBps;
        uint8 clampMask = HelmClamp.NONE;

        if (finalLp > limits.lpShareMaxBps) {
            finalLp = limits.lpShareMaxBps;
            clampMask |= HelmClamp.LP_ABOVE_MAX;
        }
        if (finalLp < limits.lpShareMinBps) {
            finalLp = limits.lpShareMinBps;
            clampMask |= HelmClamp.LP_BELOW_MIN;
        }
        if (finalRange > limits.rangeWidthMaxBps) {
            finalRange = limits.rangeWidthMaxBps;
            clampMask |= HelmClamp.RANGE_ABOVE_MAX;
        }
        if (finalRange < limits.rangeWidthMinBps) {
            finalRange = limits.rangeWidthMinBps;
            clampMask |= HelmClamp.RANGE_BELOW_MIN;
        }

        // ---- Layer 2: on-chain volatility exit ---------------------------------------------------------
        uint256 volBps = volEwmaQ / 1e4;
        if (volBps > limits.volExitLevelBps) {
            finalLp = 0;
            clampMask |= HelmClamp.VOLATILITY_EXIT;
        }

        // ---- Layer 3: on-chain economic veto -----------------------------------------------------------
        // The contract only moves money into LP when it has measured, on chain, that the fee edge beats
        // lending by the required margin. An edge it has not measured is not a positive edge.
        uint256 edge = feeEdgeBps();
        if (finalLp > 0 && edge < minFeeEdgeBps) {
            finalLp = 0;
            clampMask |= HelmClamp.ECONOMIC_VETO;
        }

        // ---- Is the move worth its gas? ---------------------------------------------------------------
        uint256 delta = finalLp > currentLpShareBps ? finalLp - currentLpShareBps : currentLpShareBps - finalLp;
        emit ProposalEvaluated(
            cid, lpShareBps, finalLp, rangeWidthBps, finalRange, clampMask, block.timestamp
        );
        if (delta < limits.minTradeBps) {
            executedCycles[cid] = true;
            pendingCycleId = 0;
            emit NoTrade(cid, currentLpShareBps, finalLp, clampMask);
            _storeForecast(cid, forecastVolBps, forecastYieldBps);
            return;
        }

        // ---- Execute -----------------------------------------------------------------------------------
        executedCycles[cid] = true;
        pendingCycleId = 0;
        lastExecutedCycleId = cid;
        currentLpShareBps = finalLp;
        currentRangeWidthBps = finalRange;

        _storeForecast(cid, forecastVolBps, forecastYieldBps);

        _requestRebalance(cid, finalLp, finalRange, HelmAction.FROM_MODEL, clampMask);
    }

    /// @dev The market got violent enough that the contract pulls the vault out of LP by itself.
    function _autonomousExit(uint256 volBps) internal {
        uint256 cid = ++cycleId;
        pendingCycleId = 0;
        executedCycles[cid] = true;
        lastExecutedCycleId = cid;
        currentLpShareBps = 0;

        emit AutonomousExit(cid, volBps, currentRangeWidthBps, block.timestamp);
        _requestRebalance(cid, 0, currentRangeWidthBps, HelmAction.AUTONOMOUS_EXIT, HelmClamp.VOLATILITY_EXIT);
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                    Forecast grading                                             */
    /* ------------------------------------------------------------------------------------------- */

    function _storeForecast(uint256 cid, uint256 vol, uint256 yieldBps) internal {
        pendingForecastVolBps = vol;
        pendingForecastYieldBps = yieldBps;
        pendingForecastCycleId = cid;
        pendingForecastAt = block.timestamp;
    }

    /// @dev Grade the previous cycle's forecast against what the chain actually did.
    ///
    ///      The volatility forecast is graded against the volatility the contract measured itself.
    ///      The yield forecast is graded against the fee yield the market actually paid, because
    ///      that is the quantity the allocation decision actually turns on: a model that cannot
    ///      forecast the fee yield cannot claim it can forecast the market. Grading the yield
    ///      against the lending rate instead would be a grade against a number nobody forecasts.
    function _gradePendingForecast() internal {
        if (pendingForecastCycleId == 0) return;
        uint256 realizedVol = volEwmaQ / 1e4;
        uint256 realizedYield = feeAprBps();
        uint256 volErr = pendingForecastVolBps > realizedVol
            ? pendingForecastVolBps - realizedVol
            : realizedVol - pendingForecastVolBps;
        uint256 yieldErr = pendingForecastYieldBps > realizedYield
            ? pendingForecastYieldBps - realizedYield
            : realizedYield - pendingForecastYieldBps;
        volMaeAccum += volErr;
        yieldMaeAccum += yieldErr;
        gradedForecasts += 1;
        emit ForecastGraded(pendingForecastCycleId, volErr, yieldErr, realizedVol, realizedYield);
        pendingForecastCycleId = 0;
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                     Callback requests                                           */
    /* ------------------------------------------------------------------------------------------- */

    /// @dev Ask the vault to open the cycle. The first payload word is reserved for the proxy to
    ///      inject this contract's address, which is how the vault authenticates the callback.
    function _requestDecision(uint256 cid, uint256 price, uint256 rate, uint256 vol) internal {
        bytes memory payload = abi.encodeWithSelector(
            IHelmVaultCallback.requestDecision.selector, address(0), cid, price, rate, vol
        );
        SYSTEM.requestCallbackV_1_0(
            ISystemContract.CallbackConfiguration_V_1_0({
                chainId: DEST_CHAIN_ID,
                recipient: vault,
                gasLimit: CALLBACK_GAS_LIMIT,
                payload: payload
            })
        );
    }

    /// @dev Tell the vault what it is allowed to hold now.
    function _requestRebalance(uint256 cid, uint256 lpShareBps, uint256 rangeWidthBps, uint8 action, uint8 clampMask)
        internal
    {
        bytes memory payload = abi.encodeWithSelector(
            IHelmVaultCallback.rebalance.selector, address(0), cid, lpShareBps, rangeWidthBps, action, clampMask
        );
        SYSTEM.requestCallbackV_1_0(
            ISystemContract.CallbackConfiguration_V_1_0({
                chainId: DEST_CHAIN_ID,
                recipient: vault,
                gasLimit: CALLBACK_GAS_LIMIT,
                payload: payload
            })
        );
        emit RebalanceRequested(cid, lpShareBps, rangeWidthBps, action, clampMask, block.timestamp);
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                         Views                                                   */
    /* ------------------------------------------------------------------------------------------- */

    /// @notice Mean absolute error of the volatility forecast, in basis points.
    function volMaeBps() external view returns (uint256) {
        if (gradedForecasts == 0) return 0;
        return volMaeAccum / gradedForecasts;
    }

    /// @notice Mean absolute error of the rate forecast, in basis points.
    function yieldMaeBps() external view returns (uint256) {
        if (gradedForecasts == 0) return 0;
        return yieldMaeAccum / gradedForecasts;
    }

    /// @notice Everything a dashboard needs to render one cycle.
    function state()
        external
        view
        returns (
            uint256 cycleId_,
            uint256 pendingCycleId_,
            uint256 currentLpShareBps_,
            uint256 volBps_,
            uint256 rateBps_,
            uint256 feeAprBps_,
            uint256 lastExecutedCycleId_,
            uint256 gradedForecasts_,
            bool limitsSet_,
            bool paused_
        )
    {
        return (
            cycleId,
            pendingCycleId,
            currentLpShareBps,
            volEwmaQ / 1e4,
            rateBps,
            feeAprBps(),
            lastExecutedCycleId,
            gradedForecasts,
            limitsSet,
            paused
        );
    }
}
