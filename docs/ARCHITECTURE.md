# Helm architecture
Helm is a testnet fund-management loop split across two chains. The allocation model proposes a stablecoin split; `HelmReactive` decides whether that split is allowed; `HelmVault` is the only contract that moves funds. The agent's signing key can call `postProposal` and nothing else.

## 1. Architecture and data flow

The trust boundary is deliberately narrow:

- The model supplies an allocation, a range width, a volatility forecast, and a fee-yield forecast.
- The agent turns those outputs into a proposal and records its own view of the decision.
- `HelmReactive` on Reactive Lasna checks the proposal, clamps it to the user's envelope, applies the volatility exit and economic veto, and decides the executable allocation.
- `HelmVault` on Base Sepolia accepts a rebalance only from the callback proxy with the enforcer's address injected, or directly from the pinned enforcer. It then moves funds between the lending market and the liquidity pool.

```text
 Reactive Lasna (5318007)                         Base Sepolia (84532)
 ------------------------------                   -------------------------------
 legacy cron emitter
        | cron topic
        v
 Reactive system contract
        | react(LogRecord)
        v
 HelmReactive.react()
        |
        | _onCron(): open cycle
        | _requestDecision(): requestCallbackV_1_0
        v
 Callback proxy  <------------------------------  HelmVault.requestDecision()
        | injects the enforcer address               | emits DecisionRequested
        |                                                v
        |                                      Helm agent polls Base logs
        |                                                |
        |                                                | model + policy
        |                                                v
        |                                      HelmVault.postProposal()
        |                                                | emits ProposalPosted
        |                                                v
        | Reactive subscription <---------------------- event on Base Sepolia
        |
        | _onProposal(): reject, clamp, veto, or request rebalance
        | _requestRebalance(): requestCallbackV_1_0
        v
 Callback proxy  <------------------------------  HelmVault.rebalance()
        |                                                |
        |                                                +--> lending market
        |                                                +--> LP pool
        v
 Reactive events + vault events
        |                                                |
        +------------------ agent reconciliation --------+
                                  |
                                  v
                    agent/ledger/cycles.jsonl

 LP pool events, fee-rate events, lending-rate events,
 limits, pause state, agent address and proposal events
       |
       v
 Reactive subscriptions -> HelmReactive.react()

 Dashboard server reads live chain state and committed JSONL/JSON/Markdown files
```

A normal cycle is therefore:

1. The legacy cron emitter sends the configured cron topic on Lasna. The Reactive network delivers it to `HelmReactive.react`, which calls `_coverDebt` before handling the log.
2. `_onCron` opens one cycle, emits `CycleOpened`, and `_requestDecision` asks the Reactive system for a callback to the vault on chain `84532`.
3. The callback proxy on Base Sepolia injects the enforcer address and calls `HelmVault.requestDecision`. The vault emits `DecisionRequested`.
4. The agent polls for that event, reads the vault and enforcer state, builds live features, runs the allocation model, and computes an off-chain expectation of the contract's decision.
5. `HelmVault.postProposal` posts the model's allocation unchanged. This is the agent key's only mutating operation.
6. The vault emits `ProposalPosted`. The Reactive subscription delivers that log to Lasna, where `_onProposal` rejects or enforces it.
7. If execution is allowed, `_requestRebalance` sends another cross-chain callback. `HelmVault.rebalance` spends each cycle once, moves the position, and emits `Rebalanced`.
8. The agent reads the enforcer's verdict on Lasna and the vault's execution on Base Sepolia, then completes its ledger record.

There is a second, model-free path. `_onSwap` updates the volatility estimate; if it is above the approved exit level, `_autonomousExit` pulls the vault out of LP and asks for a rebalance without a proposal.

## 2. Component structure

- **Enforcer:** `contracts/src/HelmReactive.sol`. It subscribes to events, mirrors vault state, opens cycles, evaluates proposals, measures volatility and fee flow, grades forecasts, and requests cross-chain callbacks.
- **Vault:** `contracts/src/HelmVault.sol`. It stores the user's envelope, accepts only an agent proposal, authenticates the enforcer callback, and holds the LP position and lending balance.
- **Shared contract types:** `contracts/src/HelmTypes.sol` defines `HelmLimits`, `HelmProposal`, `HelmSnapshot`, `HelmClamp`, and `HelmAction`.
- **Agent runtime:** `agent/helm_agent/listener.py` owns the answer-once loop; `chain.py` contains the small JSON-RPC client; `policy.py` builds the proposal and mirrors the contract rules; `llm.py` supplies an optional explanation with a deterministic fallback.
- **Model:** `agent/helm_agent/model.py` implements a three-headed multilayer perceptron directly on NumPy. Its heads are allocation, volatility, and fee yield.
- **Training and market data:** `features.py`, `data.py`, `backtest.py`, and `train.py` build the dataset, train the model, and score it against four baselines on held-out Base mainnet history.
- **Evidence and dashboard:** `scripts/collect-evidence.py` joins events from both chains; the Next.js dashboard reads live chain state plus committed files.

## 3. File structure

```text
contracts/
  src/HelmReactive.sol
  src/HelmVault.sol
  src/HelmTypes.sol
  test/HelmReactive.t.sol
  lib/reactive-lib-omni/src/base/AbstractReactive.sol
  lib/reactive-lib-omni/src/base/AbstractPayer.sol
  lib/reactive-lib-omni/src/base/AbstractCallback.sol
agent/
  helm_agent/cli.py
  helm_agent/listener.py
  helm_agent/chain.py
  helm_agent/policy.py
  helm_agent/model.py
  helm_agent/features.py
  helm_agent/data.py
  helm_agent/backtest.py
  helm_agent/train.py
  helm_agent/replay.py
  helm_agent/llm.py
  ledger/cycles.jsonl
  ledger/chain-events.jsonl
  models/metrics.json
dashboard/
  src/app/page.tsx
  src/app/cycles/page.tsx
  src/app/policy/page.tsx
  src/app/backtest/page.tsx
  src/app/api/state/route.ts
  src/app/proof.json/route.ts
  src/lib/chain.ts
  src/lib/deployment.ts
  src/components/split-bar.tsx
scripts/
  collect-evidence.py
  claims.py
  verify-deployment.sh
deployments/base-sepolia.json
docs/ARCHITECTURE.md
```

The ledger is appended when a proposal is posted and rewritten after reconciliation; `chain-events.jsonl` is generated rather than written by the agent.

## 4. Data model

There is no database. Helm has four durable kinds of state: contract storage, the agent's JSONL ledger, the generated chain-events JSONL, and files read by the dashboard.

### On-chain storage

`HelmVault` stores its owner and agent, `limits`, `limitsSet`, `paused`, the current LP share and range width, `lastExecutedCycleId`, `lastRequestedCycleId`, and the `usedCycleId` mapping. The asset, lending pool, and LP pool are immutable addresses. The actual funds are represented by the vault's token balance, its lending-market balance, and its LP position; `totalValueUsd` adds those three values.

`HelmReactive` stores its owner, cron topic, vault and market addresses, registered agent, economic parameters, the mirrored `limits` and `limitsSet`, `paused`, observed price and volatility state, fee-flow state, the current and pending cycle, the last executed cycle, the `executedCycles` mapping, forecast errors, and the pending forecast. `reactCount` and `lastReactAt` are the enforcer's network-call health counters.

### Agent ledger record

`agent/ledger/cycles.jsonl` contains one JSON object per line. Its field-level shape is:

```text
{
  cycleId: number,
  openedAt: number,
  decisionRequestTx: string,
  decisionRequestBlock: number,
  market: {
    priceE18: number, rateBps: number, volBps: number,
    currentLpShareBps: number, totalValueUsd: number
  },
  model: {
    allocation: number, forecastVolBps: number, forecastYieldBps: number,
    features: Record<string, number>, historyBars: number, lastBarTs: number
  },
  proposal: {
    cycleId: number, lpShareBps: number, rangeWidthBps: number,
    forecastVolBps: number, forecastYieldBps: number,
    modelAllocationBps: number, rationale: string,
    expectedLpShareBps: number, expectedRangeWidthBps: number,
    expectedClampMask: number, expectedClampMaskName: string[],
    expectedNoTrade: boolean, source: string
  },
  explanation: {
    text: string, source: string, model: string, costUsd: number,
    paymentTx: string, latencyMs: number, error: string
  },
  posted: { txHash: string, at: number, agent: string },
  chain: {
    evaluated?: {
      modelLpShareBps: number, finalLpShareBps: number,
      modelRangeWidthBps: number, finalRangeWidthBps: number,
      clampMask: number, evaluatedAt: number, txHash: string, blockNumber: number
    },
    rejected?: {
      reason: number, reasonName: string, proposer: string,
      txHash: string, blockNumber: number
    },
    noTrade?: {
      currentLpShareBps: number, targetLpShareBps: number,
      clampMask: number, txHash: string, blockNumber: number
    },
    rebalance?: {
      cycleId: number, lpShareBps: number, rangeWidthBps: number,
      lpValueUsd: number, totalValueUsd: number, action: number,
      clampMask: number, blockNumber: number, transactionHash: string
    }
  },
  latency?: { openToPostMs?: number | null, openToEvaluatedMs?: number }
}
```

The `chain` object is initially empty. Reconciliation fills it from chain logs and adds `latency`.

### Chain-events record

`scripts/collect-evidence.py` joins Lasna and Base Sepolia events by `cycleId` and writes `agent/ledger/chain-events.jsonl`:

```text
{
  cycleId: number,
  outcome: string,
  fullCycle: boolean,
  opened?: { priceE18, rateBps, volBps, openedAt, blockNumber, txHash },
  expired?: { waitedSec, blockNumber, txHash },
  requested?: {
    priceE18, rateBps, volBps, currentLpShareBps, totalValueUsd,
    requestedAt, blockNumber, txHash
  },
  posted?: {
    proposer, lpShareBps, rangeWidthBps, forecastVolBps,
    forecastYieldBps, proposedAt, blockNumber, txHash
  },
  evaluated?: {
    modelLpShareBps, finalLpShareBps, modelRangeWidthBps, finalRangeWidthBps,
    clampMask, clampNames, evaluatedAt, blockNumber, txHash
  },
  rejected?: { reason, reasonNames, proposer, blockNumber, txHash },
  noTrade?: {
    currentLpShareBps, targetLpShareBps, clampMask, clampNames,
    blockNumber, txHash
  },
  rebalanceRequested?: {
    lpShareBps, rangeWidthBps, action, clampMask, requestedAt, blockNumber, txHash
  },
  rebalanced?: {
    lpShareBps, rangeWidthBps, lpValueUsd, totalValueUsd, action,
    clampMask, clampNames, blockNumber, txHash, timestamp?
  },
  autonomousExit?: { volBps, rangeWidthBps, exitedAt, blockNumber, txHash },
  forecastGraded?: {
    volErrBps, rateErrBps, realizedVolBps, realizedRateBps, blockNumber, txHash
  }
}
```

`outcome` is one of `autonomous_exit`, `rebalanced`, `rebalance_requested`, `rejected`, `no_trade`, `evaluated`, `expired`, or `open`. `fullCycle` is true only when the record contains the opening, request, proposal, judgement, and final result legs.

### Dashboard file reads

| Loader | Repository path | Use |
| --- | --- | --- |
| `loadDeployment` | `deployments/base-sepolia.json` | Addresses, chain IDs, RPCs, explorers, limits |
| `loadCycles` | `agent/ledger/cycles.jsonl` | The agent's per-cycle ledger |
| `loadChainCycles` | `agent/ledger/chain-events.jsonl` | Events joined from both chains |
| `loadMetrics` | `agent/models/metrics.json` | Model and backtest metrics |

The dashboard module also defines `docs/BENCHMARK.md` as `BENCHMARK_PATH`, but the current pages do not load it. Missing ledger or evidence files produce empty arrays; malformed individual JSONL lines are skipped.

## 5. API design

### `python -m helm_agent.cli`

This is the agent's programmatic runtime. It loads the deployment and trained model, polls Base Sepolia for `DecisionRequested`, answers each cycle once, posts the proposal, reconciles the verdict from both chains, and updates `agent/ledger/cycles.jsonl`.

| Flag | Type and default | Effect |
| --- | --- | --- |
| `--deployment` | path, deployment default | Deployment record to load |
| `--history` | path, `agent/data/base_eth_usdc_15m.jsonl` default | Market history |
| `--model` | path, `agent/models/model.npz` default | Trained model |
| `--ledger` | path, `agent/ledger/cycles.jsonl` default | Ledger to load and write |
| `--cycles` | integer, `0` | Cycles to answer; `0` means forever |
| `--poll` | float, `4.0` | Seconds between polls |
| `--reconcile-wait` | float, `45.0` | Seconds to wait for each chain verdict |
| `--lending-rate-bps` | float, `300.0` | Rate used by the agent's local mirror |
| `--min-fee-edge-bps` | integer, `50` | Economic threshold used by the local mirror |
| `--no-llm` | flag | Use only the deterministic explanation |
| `--llm-timeout` | float, `10.0` | Wait for the paid explanation before using the fallback |
| `--no-sync` | flag | Do not refresh market history from Base mainnet |
| `--status` | flag | Print the loaded deployment as JSON and exit |

Without `--status`, the command prints progress and a final per-cycle summary. The summary gives the cycle id, model-to-enforced allocation or rejection reason, and the proposal or rebalance transaction hash. A judge can compare those hashes and allocations with the two chains. With `--status`, the JSON fields are `chainId`, `baseRpc`, `baseExplorer`, `lasnaRpc`, `lasnaExplorer`, `lasnaChainId`, `deployer`, `agent`, `token`, `lpPool`, `lendingPool`, `vault`, `reactive`, and `limits`.

### `GET /api/state`

`dashboard/src/app/api/state/route.ts` returns:

```text
{
  fetchedAt: number,
  vault: VaultState | null,
  reactive: ReactiveState | null,
  errors: string[]
}
```

`VaultState` contains the vault address, owner, agent, pause and limits flags, total value, LP and lending shares, current LP share and range width, last requested and executed cycle ids, price, rate, and the eight limit fields. `ReactiveState` contains the enforcer address, cycle and pending-cycle ids, current LP share, volatility, rate, fee APR, last executed cycle id, graded-forecast count, limits and pause flags, fee-edge-measured flag, and fee edge. The response has `cache-control: no-store`.

A judge can compare the same fields with `cast call` or direct JSON-RPC calls to Base Sepolia and Lasna. `errors` names the chain that could not be read; the corresponding state object is `null`.

### `GET /proof.json`

The route is implemented by `dashboard/src/app/proof.json/route.ts`. It returns one JSON document with:

- `generatedAt`, `project`, and `tagline`;
- `deployment`, the contents of `deployments/base-sepolia.json`;
- `live`, the same snapshot shape as `/api/state`;
- `cycles.count`, `cycles.clampedCount`, `cycles.executedCount`, and the agent-ledger `cycles.log`;
- `onChain.cycles`, `fullCycles`, `clampedCount`, `economicVetoCount`, `rejectedCount`, `autonomousExitCount`, `rebalanceCount`, and the chain-events `onChain.log`;
- `backtest`, including the training window, dataset split, report, and strategy summaries, or `null` when metrics are absent.

Every transaction hash in the two logs can be opened through the Base Sepolia or Lasna explorer named in `deployment`. The route also has `cache-control: no-store`.

### The three scripts

| Command | Inputs | Output and chain check |
| --- | --- | --- |
| `scripts/collect-evidence.py` | `--deployment`, `--out`, `--markdown`, `--lasna-blocks` (`60000`), `--base-blocks` (`250000`) | Reads both chains, writes `agent/ledger/chain-events.jsonl` and `docs/EVIDENCE.md`, and prints cycle, full-cycle, and clamped counts. Each emitted `txHash` can be checked against the source event log. |
| `scripts/claims.py` | `--out`, `--skip-tests` | Generates `docs/CLAIMS.md` from `agent/models/metrics.json`, both JSONL ledgers, `deployments/base-sepolia.json`, the Foundry settings, the test suites, and the repository revision. It prints `claims written to ...`. Each row names the artifact from which it was read. |
| `scripts/verify-deployment.sh` | optional `BASE_RPC`, `LASNA_RPC`, and `PYTHON` environment variables | Checks addresses and code, enforcer wiring, agreement between vault and enforcer limits, deployed bytecode, callback funding and debt, enforcer lREACT health, the cron subscription, and the evidence gates. It prints a section for each check and exits non-zero if any check fails. |

## 6. Caching

There is no web or API cache layer. `readChainState` creates a viem public client for each read, uses a `20_000` ms transport timeout and `retryCount: 2`, and `readChainStateWithTimeout` applies a `20_000` ms overall deadline. The chain RPC is contacted server-side; the browser receives only the derived JSON response.

The dashboard's other inputs are committed files read from disk on each server render. They are not API-cache entries and are not silently replaced by fixtures. The agent's market-history JSONL is a separate resumable on-disk cache managed by `helm_agent.data`; it is not a dashboard cache.

Both JSON routes use these exact settings:

```ts
export const dynamic = "force-dynamic";
export const revalidate = 0;
```

The same settings are present on all four dashboard pages. The routes also return `cache-control: no-store`.

## 7. UI architecture

| Route | Reads | Purpose |
| --- | --- | --- |
| `/` | Deployment, live vault and enforcer state, agent ledger, model metrics | Current position, latest cycle, recent cycles, backtest headline, and deployment addresses |
| `/cycles` | Deployment, agent ledger, chain-events ledger | Detailed agent decisions beside the independently collected chain record |
| `/policy` | Deployment and live chain state | The three enforcement layers, live envelope, rejection rules, agent permissions, and contract addresses |
| `/backtest` | `agent/models/metrics.json` | Held-out equity curves, strategy table, loss analysis, and run metadata |

The visual direction is a greyscale instrument panel: dense, numeric, and explicit about the source of each value. There are no gradients, glow effects, or decorative motion. Colour carries meaning:

- amber (`--clamp`) means the contract changed the model's number;
- red (`--veto`) means the contract refused the trade;
- blue (`--lp`) means the liquidity position;
- green (`--lending`) means the lending position;
- the remaining interface is built from greys.

The split bar runs from 0% LP at the left to 100% LP at the right. Blue is the enforced LP allocation, green is the remainder in lending, the amber band is the portion removed by the contract, the amber line is the model's raw number, and the white line is the enforced number. The overview can also show ticks for the live LP-share floor and ceiling. Its `role="img"` label states both percentages.

There is no route-specific loading component. The pages are server components and wait for their reads; the stylesheet defines a reduced-motion-aware skeleton, but the current pages do not instantiate one. Empty states cover an empty agent ledger, an absent chain-events file, a missing metrics file, missing strategies, and an unread vault or enforcer. Chain failures are reported as errors rather than as stale live values.

Responsive rules reduce the two-, three-, and four-column grids to two columns below `860px` and to one column below `560px`. The overview hero also becomes one column below `860px`; navigation and legends wrap; tables use horizontal overflow rather than forcing the page wider.

## 8. Sponsor technology use, and why it is essential

Reactive Network supplies the cross-chain control plane. A plain Solidity contract could implement the same arithmetic on one chain, but it could not by itself provide Helm's cross-chain subscription and authenticated callback model.

- **Cron emitter and reactive subscriptions.** The constructor subscribes on Lasna to the legacy cron emitter at `0x0000000000000000000000000000000000fffFfF`. `configure` subscribes to the LP pool's swap and fee-rate events, the lending pool's rate event, and the vault's proposal, limits, pause, and agent events on chain `84532`. Logs arrive through `react(LogRecord)` without a relayer choosing what the contract sees.
- **Cron cadence.** `CRON_TOPIC_1` opens a cycle every block for the demo; `CRON_TOPIC_10` is the ten-block cadence described as the production cadence. The deployment record uses `CRON_TOPIC_10`.
- **Callback proxy on the destination chain.** `SYSTEM.requestCallbackV_1_0` targets the vault on Base Sepolia. The proxy injects the calling reactive contract's address into the first payload slot. `HelmVault.onlyReactive` checks that the caller is the immutable callback proxy and that the injected address equals the immutable `_CALLBACK_SENDER`.
- **Cross-chain callback.** `_requestDecision` and `_requestRebalance` both use `CallbackConfiguration_V_1_0` with chain id `84532`, the vault recipient, and a `2_000_000` gas limit. The address slot is encoded as zero and reserved for proxy injection.
- **One-second blocks.** Lasna's one-second blocks make a cron-driven cycle prompt and keep the Reactive decision leg close to the market event that opened it.
- **lREACT fuel model.** The network charges the reactive contract for calls. `HelmReactive` keeps a `1e17` reserve floor, uses `1.3e16` wei as a deliberately pessimistic per-call estimate, pays outstanding debt before handling a log, and exposes `reserveHealthy` and `reserveCallsRemaining`. The source records a measured cron-tick cost of `0.0125157` lREACT. A contract that cannot pay stops being called, so lREACT is operating fuel rather than an incidental balance.

A conventional contract would need an oracle, keeper, relayer, and separate authentication scheme to emulate this flow. Those components would add off-chain trust and would not provide the Reactive system's contract-owned cross-chain callback.

## 9. The reactive rules, in order

Items 12 to 18 follow the exact rejection priority in `_rejectReason`; items 20 to 26 follow the order in `_onProposal`.

1. **Mirror the approved envelope.** `_onLimits` copies all eight `HelmLimits` fields and sets `limitsSet`. Test: `test_LimitsAreMirroredFromTheVault`.
2. **Open a cycle on cron.** `_onCron` requires configuration, limits, and an unpaused vault, increments `cycleId`, and sets `pendingCycleId`. Test: `test_CronOpensACycle`.
3. **Honour the cooldown.** `_onCron` refuses a new cycle until `limits.cooldownSec` has elapsed. Test: `test_CronHonoursTheCooldown`.
4. **Expire an unanswered cycle.** `_onCron` writes off a pending cycle after `freshnessSec` and allows the next cycle to open. Test: `test_AnUnansweredCycleIsWrittenOffWhenItsFreshnessWindowCloses`.
5. **Allow the owner to clear a pending cycle.** `expirePendingCycle` emits `CycleExpired` and clears `pendingCycleId`. Test: `test_TheOwnerCanExpireAPendingCycle`.
6. **Ask the vault about the open cycle.** `_requestDecision` targets chain `84532`, the vault, the reserved address slot, and `requestDecision`. Test: `test_CronRequestsADecisionCallbackWithTheInjectionSlot`.
7. **Observe the market.** `_onSwap`, `_onRate`, and `_onFeeRate` update price, volatility, lending rate, and fee rate. Test: `test_RateAndPriceAreObserved`.
8. **Start the fee window with the first observed fee.** `_onSwap` starts `periodStart` with the first fee-paying swap and rolls the window after `observationWindowSec`. Test: `test_TheFeeWindowStartsWithTheFirstFeeTheContractSees`.
9. **Accept calls only from the Reactive system and settle debt first.** `react` is guarded by `onlySystem`, increments `reactCount`, records `lastReactAt`, and calls `_coverDebt`. Test: `test_TheNetworkCallCounterMoves`.
10. **Keep the lREACT reserve visible.** `fund`, `reserveHealthy`, and `reserveCallsRemaining` expose the reserve health and estimated calls. Test: `test_FundingTheReserveIsVisible`.
11. **Apply the volatility safety override.** `_onSwap` calls `_autonomousExit` without a model when realised volatility is above `volExitLevelBps`; `_onProposal` also forces LP to zero with `VOLATILITY_EXIT`. Test: `test_AutonomousExitWhenVolatilityBreaksTheExitLevel` exercises the autonomous branch.
12. **Reject when no limits exist.** `_rejectReason` returns `NO_LIMITS`. Test: `test_ProposalWithoutLimitsIsRejected`.
13. **Reject while paused.** `_rejectReason` returns `PAUSED`. Test: `test_PausedVaultRejectsProposals`.
14. **Reject an unknown proposer.** `_rejectReason` returns `UNKNOWN_AGENT` unless the proposer is the registered agent. Test: `test_ProposalFromAStrangerIsRejected`.
15. **Reject the wrong cycle.** `_rejectReason` returns `CYCLE_MISMATCH` unless the proposal answers `pendingCycleId`. Test: `test_ProposalForTheWrongCycleIsRejected`.
16. **Reject a replay.** `_rejectReason` contains a `REPLAY` check for a spent cycle, although the earlier cycle-mismatch rule normally fires first; `test_ReplayIsRejected` expects `CYCLE_MISMATCH`. Test: `test_ReplayIsRejected`.
17. **Reject a stale proposal.** `_rejectReason` returns `STALE` after `freshnessSec`. Test: `test_StaleProposalIsRejected`.
18. **Reject bad input.** `_rejectReason` returns `BAD_INPUT` for an out-of-range allocation or range, or for a proposal prepared before the cycle opened. Test: `test_ProposalPreparedBeforeTheCycleOpenedIsRejected` covers the prepared-before branch.
19. **Accept a valid proposal from the registered agent.** `_onProposal` passes the rejection rules and enters the enforcement layers. Test: `test_ProposalFromTheRegisteredAgentIsAccepted`.
20. **Clamp LP share above the maximum.** `_onProposal` sets `finalLp` to `lpShareMaxBps` and sets `LP_ABOVE_MAX`. Test: `test_LpShareAboveTheMaximumIsClamped`.
21. **Clamp LP share below the minimum.** `_onProposal` sets `finalLp` to `lpShareMinBps` and sets `LP_BELOW_MIN`. Test: `test_LpShareBelowTheMinimumIsClamped`.
22. **Clamp the range on both sides.** `_onProposal` applies `rangeWidthMinBps` and `rangeWidthMaxBps` with `RANGE_BELOW_MIN` or `RANGE_ABOVE_MAX`. Test: `test_RangeWidthIsClampedOnBothSides`.
23. **Combine independent clamp flags.** `_onProposal` ORs every applied rule into `clampMask`. Test: `test_MultipleClampsAreCombined`.
24. **Veto an LP entry without a measured fee edge.** `_onProposal` calls `feeEdgeBps` and sets LP to zero with `ECONOMIC_VETO` when the edge is below `minFeeEdgeBps`. Test: `test_EconomicVetoKeepsTheVaultOutOfLp`.
25. **Do not veto a measured edge that beats lending.** `_onProposal` leaves LP unchanged when `feeEdgeBps` is at least `minFeeEdgeBps`. Test: `test_EconomicVetoDoesNotFireWhenFeesBeatLending`.
26. **Skip a move below the minimum trade.** `_onProposal` emits `NoTrade`, spends the cycle, and requests no rebalance when the allocation delta is below `minTradeBps`. Test: `test_NoTradeBelowTheMinimumTradeSizeIsSkipped`.
27. **Grade the previous forecast.** `_gradePendingForecast` records volatility and realised-fee-yield errors on the next cycle. Test: `test_ForecastIsGradedOnTheNextCycle`.
28. **Execute only the enforced allocation.** `_requestRebalance` sends the final LP share and range; `HelmVault.rebalance` moves the funds and marks the cycle used. Test: `test_EndToEndMoveMovesRealFunds`.
29. **Execute the model-free exit.** `_autonomousExit` requests zero LP and the vault returns the position to lending. Test: `test_AutonomousExitMovesRealFundsOutOfThePool`.
30. **Keep execution inside the callback budget.** `_requestRebalance` uses `CALLBACK_GAS_LIMIT`, and the live-envelope test checks the measured gas. Test: `test_TheLiveEnvelopeRebalanceFitsInsideTheCallbackGasLimit`.
