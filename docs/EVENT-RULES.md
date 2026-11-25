# Event rules and gates — Reactive Omni Buildathon

Filled from the official event page and the Reactive Network announcement on **2026-11-15**.
Sources: <https://dorahacks.io/hackathon/reactive-omni-buildathon>, <https://dorahacks.io/hackathon/reactive-omni-buildathon/build>,
<https://blog.reactive.network/reactive-omni-buildathon-thirty-days-to-find-out-what-one-second-buys/>,
<https://dev.reactive.network/> (Reactive docs, checked 2026-11-15).

## Event

| Item | Value |
| --- | --- |
| Event name | Reactive Omni Buildathon |
| Official URL | https://dorahacks.io/hackathon/reactive-omni-buildathon |
| Sponsor / platform | Reactive Network (Reactive Omni). Platform technologies listed by the event: Reactive Network, Solidity, OpenAI, Claude, Ethereum |
| Prize structure, prize count, currency | $5,500 total in USD, paid in REACT. Three tracks: *Every Second Counts* $2,000 first + $250 runner-up; *Set It and Forget It* $2,000 first + $250 runner-up; **Reactive Meets AI $1,000 first place only**. Helm enters *Reactive Meets AI*. |
| Submission opens (with timezone) | 2026-11-05 12:00 UTC (pre-registration opened 2026-11-04 12:00 UTC) |
| Deadline (with timezone) | **2026-12-05 20:00 UTC = 21:00 WAT (UTC+1)**. The PRD's "Dec 5, 2026, 21:00 WAT" is the same instant. Target submission: 2026-12-04. |
| **Total time budget** | 20 calendar days from 2026-11-15 to the deadline; the PRD's own build plan spans Nov 18 → Dec 5. |
| **Phase split derived from the budget** | Toolchain 5% · Rules capture 10% · Product decision 15% · Build 45% · Audit 10% · Demo rehearsal 5% · Freeze the artifact 7% · Submit 3% |
| Judging model | Four criteria, **scored 1 to 5, equally weighted**: Execution, Integration, Usefulness, Craft. Judged by the Reactive team. Guest judges may be announced on the DoraHacks page (none announced as of 2026-11-15). |
| Screening before scoring | Yes, an explicit execution gate: "Entries without [reactive transactions and their callbacks] aren't scored further." The DoraHacks builds tab currently shows "The organizer is reviewing Builds", so the published field is not enumerable. |
| Submission order effect | Not stated by the event. **Unverified.** The internal benchmark in this repo assumes none. |
| Editable after submitting | Not stated by the event. **Unverified.** Assumption: yes, so work continues to the deadline. |
| Required build tool or platform, and how it is verified | The build must use **Reactive Network**: a reactive contract on Reactive Mainnet or Lasna testnet, plus the callbacks it triggers. Verified by judges reading the deployed transactions: "We want to see the reactive transactions and the callbacks they trigger on-chain." Track rule: **"The AI has to be part of the running system, not just the tool you used to write the code."** |

### Ground rules quoted from the event

- Every Second Counts runs on Lasna testnet; the other two tracks may use Reactive mainnet **or** Lasna.
- Repositories must be **public and open-source** by the time you submit.
- **Everything should be built during the event.** Prior work can come in as a dependency, but not as the submission itself.
- On Base Sepolia, **use timestamps rather than block counts** for timers, cooldowns and deadlines. Base Sepolia blocks arrive every 200 ms since the Denim upgrade, so block-based timers run ten times faster than they used to.

## Rubric and gates

The event publishes **no numeric weights**: each of its four criteria is scored 1–5 with equal weight. The
weight column below therefore records the *equal* share (25% each) plus the internal benchmark weight, which is
what the gap routing in `docs/BENCHMARK.md` uses.

| Criterion (verbatim) | Weight | Our plan | Evidence produced | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| **Execution** — "Does it run? We want to see the reactive transactions and the callbacks they trigger on-chain. Entries without them aren't scored further." | 25% event / 20% internal | A full loop that runs on Lasna + Base Sepolia: origin `Swap` event → reactive transaction on Lasna → callback to Base Sepolia → agent proposal → reactive transaction → callback → vault rebalance. Every leg carries a transaction hash. | README cycle-log table with one row per cycle: origin tx, Lasna reactive tx, proposal tx, second Lasna reactive tx, callback tx, each with an explorer link. `docs/EVIDENCE.md` holds the same table with observed results. | contracts | ☑ |
| **Integration** — "Does the reactive contract do real work, or is it bolted on?" | 25% event / 30% internal (impact+exec) | The reactive contract is the **gatekeeper and the safety net**, not a forwarder. It decides when to ask the model, checks every proposal against on-chain limits, clamps out-of-range values, rejects stale/foreign/replayed proposals, skips no-op moves, **and can force the LP share to zero on a volatility breach without asking the model at all**. It also grades the model against realized outcomes on-chain. | `docs/ARCHITECTURE.md` reactive-logic spec; 30 Foundry tests for trigger, freshness, clamp, cooldown, skip, veto and autonomous exit; the recorded week the agent was offline, when the contract wrote 586 consecutive cycles off without moving funds. | contracts | ☑ |
| **Usefulness** — "Does it solve a problem real users have?" | 25% event / 30% internal | "Best rate now" is wrong an hour later, and yield optimizers chase today's highest rate. Helm forecasts next-hour lending rate and volatility and allocates under a user-set risk envelope. The claim is proven with an **out-of-sample backtest on real Base mainnet history** against three baselines. | `python -m helm_agent.train` writes `agent/models/metrics.json`; `scripts/claims.py` writes the result, the worst drawdown and the rebalance count per strategy into `docs/CLAIMS.md`; the dashboard reads the same file. | agent | ☑ |
| **Craft** — "Readable code, a working demo, and documentation someone else could follow." | 25% event / 10+15 internal (UX+demo) | Foundry test suite for every reactive rule, pytest for the model and the forecast→allocation formula, CI, a one-command deployment script, a machine-readable proof endpoint, a live dashboard that reads the chain, and a demo under 3 minutes. | `docs/CLAIMS.md` (every number generated by a script), `scripts/verify-deployment.sh` exiting zero against the live deployment, the live dashboard, the video link. | all | ☑ |
| *Track rule* — "The AI has to be part of the running system, not just the tool you used to write the code." | gate | A **neural network** (PyTorch MLP) forecasts on every cycle and its output is what the reactive contract checks, clamps and executes. The LLM never chooses an amount. The agent can be switched off and the vault is still protected. | `agent/helm_agent/model.py` (the network), `agent/helm_agent/policy.py` (the decision and the off-chain mirror of the contract's rules), the on-chain cycle log showing a model proposal being clamped, and the autonomous-exit cycle with no proposal at all. | agent | ☑ |
| *Event emphasis (from the announcement)* — "The strongest entries will show their latency numbers measured across the full loop, not just one leg of it." | evidence | Helm measures **end-to-end loop latency** in seconds and in Reactive blocks, from the origin event's block to the vault's rebalance block. | `docs/EVIDENCE.md` latency table, generated from the recorded blocks. | scripts | ☑ |

Internal benchmark (the weight set used for gap routing in `docs/BENCHMARK.md`), from the build brief:
Impact on the user 30 · Technical execution 20 · Innovation 15 · Demo and evidence 15 · Product and UX 10 · Sponsor technology use 10.
**The event's own criteria and weights govern the actual judging.** The internal benchmark is the stricter working target.

## Required submission fields

Checked against the DoraHacks event page and the announcement, not against memory.

| Field | Value we will submit | Verified link or artifact | Status |
| --- | --- | --- | --- |
| Project name | Helm | — | ☑ |
| One-line claim (vision) | "Helm keeps your stablecoins earning under limits you set once: a neural network proposes the split every cycle, and a reactive contract clamps every proposal to your limits on-chain." | README line 1 | ☑ |
| Description | see `docs/SUBMISSION.md` | `docs/SUBMISSION.md` | ☑ |
| Live app URL | `https://helm-dashboard-six.vercel.app` | checked unauthenticated: `/`, `/cycles`, `/policy`, `/backtest`, `/proof.json` all return 200 | ☑ |
| Repository URL | `https://github.com/Alpha-Hackathon-Grinding-Society/helm` (mirror: `https://github.com/unifyWeb3/helm`) | `git remote -v` | ☑ |
| Repository revision submitted | filled at submission time | `git rev-parse HEAD` | ☐ |
| Contract address(es) | Lasna enforcer `0xf24f1d13F995a2368015868048F791426AfeD39C`; Base Sepolia vault `0x9ED8FAD6627B89104b5a5C2C31334168Ce73EB77`, token, LP pool, lending pool | `docs/DEPLOYMENTS.md` | ☑ |
| Example transaction hash | cycle 2: Lasna `0xebd2fb0a4d66dd2ca62ae68af90932ca7d92a7bf3e377fc9e90e0b89c9d23070` → Base Sepolia `0xd3e33f0e1dd7122cd3b0fcb1629305e2690ab86726d970c24910bd80667f0a19` | `docs/EVIDENCE.md` | ☑ |
| Explorer link | `https://lasna.reactscan.net/` and `https://sepolia.basescan.org/` | every row in `docs/EVIDENCE.md` | ☑ |
| Video URL | `https://helm-dashboard-six.vercel.app/helm-demo.mp4` (2 min 45 s) | served by the same deployment, sha256 checked | ☑ |
| Builder profile URL | DoraHacks profile supplied by the owner | — | ☐ |
| Required tool or platform project URL | Reactive docs: https://dev.reactive.network/ | — | ☑ |
| Disclosures (funding, prior work, team) | built during the event; no sponsor funding; the mock pools are Helm's own; the AI in the loop is a local PyTorch model, and an optional Claude explanation layer is paid through Kite Passport (cycle 795 carries the first recorded LLM explanation and its payment) | `docs/SUBMISSION.md`, `agent/ledger/cycles.jsonl` | ☑ |
| Other | the event's own requirement: "a few transaction hashes showing the full loop from origin event to callback" | `docs/EVIDENCE.md` | ☑ |

## Eligibility

| Requirement | Met | Evidence |
| --- | --- | --- |
| Built with the required tool | Yes | Reactive contract on Lasna testnet using `reactive-lib-omni`; callbacks delivered through the Reactive callback proxy on Base Sepolia. |
| Deployed to the target network | Yes | Lasna testnet (5318007) and Base Sepolia (84532), both in the event's origin/destination table. |
| Real value moved through the contract and the app | Yes | Test funds move between a mock lending pool and a mock LP position inside `HelmVault` on Base Sepolia, driven only by reactive callbacks. Testnet only — no real money. |
| Not testnet-only | **Not met, deliberately** | The PRD's non-goals say: "Real money or mainnet use. This is unaudited code run by an AI agent." The event permits Lasna testnet for this track. Stated plainly in the submission. |
| Not a mockup, deck, or design | Yes | The loop runs; every claim is backed by a transaction hash. |
| Not already funded by a sponsor program | Yes | No sponsor funding. |
| Work is ours, or we have the right to submit it | Yes | Everything in this repo was written during the event. The Reactive Omni library is a dependency, not the submission. |
| Jurisdiction and sanctions eligibility | Unverified | Not published by the event. |
| One submission per project | Yes | Helm is one project in one track. |

## Artifact identity

Filled from the artifact and the chain, never from memory. Regenerated with `scripts/claims.py`.

| Field | Value |
| --- | --- |
| Toolchain and version | Foundry 1.9.0 — `docs/CLAIMS.md` (generated) |
| Compiler version | solc 0.8.27+commit.40a35a09 — `docs/CLAIMS.md` |
| Optimizer / runs | `optimizer = true`, `optimizer_runs = 200` (`contracts/foundry.toml`) |
| EVM target | `cancun` (`contracts/foundry.toml`) |
| `viaIR` | `false` (`contracts/foundry.toml`) |
| Artifact path in repository | `contracts/out/<Contract>.sol/<Contract>.json` |
| Artifact keccak-256 and byte length | `docs/CLAIMS.md`, "Artifact identity" (generated) |
| On-chain runtime keccak-256 and byte length | `docs/CLAIMS.md`, "Artifact identity" (generated) |
| Comparison result | byte-identical outside the immutable sites for both contracts — `scripts/verify-bytecode.py`, run inside `scripts/verify-deployment.sh` (26 checks, exit 0, 2026-11-25) |
| Deployment transaction and block | the explorers linked from `docs/DEPLOYMENTS.md`; the vault's creation block is 59,724,169 on Base Sepolia |
| Test suite re-run against this configuration | 2026-11-25: 37 Foundry tests, 46 Python tests, counts written by `scripts/claims.py` into `docs/CLAIMS.md` |
| Verification script and its exit status against the live deployment | `bash scripts/verify-deployment.sh` → exit 0, 26 checks, 2026-11-25 |

## Headline claim enforcement

| Assertion in the claim | Enforced by (contract rule / code path / mechanism) | Status |
| --- | --- | --- |
| "Helm keeps your stablecoins earning" | `HelmVault.rebalance()` moves the vault's balance between the lending pool and the LP position to the target split; the vault holds no strategy of its own | ☑ |
| "under limits you set once" | `HelmVault.setLimits()` stores the envelope; the owner approves it with one signature; `HelmReactive` mirrors the envelope from the vault's `LimitsUpdated` event and cannot widen it | ☑ |
| "a neural network proposes the split every cycle" | `agent/helm_agent/model.py` produces the forecast; `agent/helm_agent/policy.py` turns it into the split; the agent posts `ProposalPosted` on Base Sepolia. Every cycle the agent sees is answered; the record also shows the 586 cycles it did not see while the process was down, and the contract's behaviour then (below) | ☑ |
| "every cycle" | `HelmReactive` opens a cycle on its cron subscription (1,000 Lasna blocks, ~17 min), on a rate move, or on a volatility move, and increments `cycleId`. A cycle with no proposal inside the 600 s freshness window is written off; no funds move | ☑ |
| "a reactive contract clamps every proposal to your limits on-chain" | `HelmReactive._evaluate()` clamps `lpShareBps` and `rangeWidthBps` into the stored bounds, applies the economic veto, and emits the clamp mask with the evaluated proposal | ☑ |
| "the contract enforces" | `HelmReactive` rejects a proposal whose `cycleId` does not match an open request, whose timestamp is outside the freshness window, or whose sender is not the registered agent; the vault rejects a repeated `cycleId` and refuses to act without a callback from the proxy | ☑ |
| "the agent cannot move money" (implicit in the design) | The agent key can call `postProposal` and nothing else; the vault's money-moving entry points accept only the pinned callback proxy / reactive address. The 586-cycle outage is the live proof: the agent was gone and the funds stayed put | ☑ |

## Limitations consistency

| Limitation | Does it negate the headline claim? | Action |
| --- | --- | --- |
| Testnet only; the lending pool and LP position are mocks | No | Stated in the README and submission. The claim is about the loop, not about real yield. |
| Market data in the demo is replayed from real Base mainnet history | No | Stated explicitly: "market data is replayed and execution is live." |
| The forecasting model is small and honestly evaluated, not state of the art | No | The claim does not promise accuracy. The backtest reports where Helm loses. |
| The model is trained on history and can be wrong | No | That is the reason the contract clamps it. |
| The LLM never decides an amount | No | The claim says the neural network proposes. |
| No mainnet deployment and no audited code | No | Consistent with the PRD's non-goals. |

## Value-moving branch coverage

Status is one of: `testnet only` (exercised on Base Sepolia / Lasna), `unit test only` (built and tested, not exercised on the live deployment), `not built`. Nothing may be blank.

| Branch / path | Test | Target-network transaction | Status |
| --- | --- | --- | --- |
| Vault deposits test funds | `test_TheOwnerCanDepositAndTheFundsAreLentOut` | Base Sepolia [`0xeeb2d62b…`](https://sepolia.basescan.org/tx/0xeeb2d62beec1613f892d30a1d271eb94010218fdb7f164b8355c14804c0baaea) | `testnet only` |
| Rebalance: move lending → LP | `test_EndToEndMoveMovesRealFunds`, `test_TheLiveEnvelopeRebalanceFitsInsideTheCallbackGasLimit` | Base Sepolia [`0xd3e33f0e…`](https://sepolia.basescan.org/tx/0xd3e33f0e1dd7122cd3b0fcb1629305e2690ab86726d970c24910bd80667f0a19) (cycle 2), [`0x0439a062…`](https://sepolia.basescan.org/tx/0x0439a062a321d60cf7e506eb5c1f845c3954af7012b68dbd4d6a60c7051016ca4) (cycle 13) | `testnet only` |
| Rebalance: move LP → lending because the fee edge did not beat lending | `test_EconomicVetoKeepsTheVaultOutOfLp`, `test_EconomicVetoDoesNotFireWhenFeesBeatLending` | Base Sepolia [`0x6c23b7fd…`](https://sepolia.basescan.org/tx/0x6c23b7fda15cdb86f27d99ccc6572c48cdc8c3af4d792f4638feab909ba2a1d8) (cycle 37) | `testnet only` |
| Rebalance: LP share forced to 0 by the volatility exit (no model involved) | `test_AutonomousExitWhenVolatilityBreaksTheExitLevel`, `test_AutonomousExitMovesRealFundsOutOfThePool` | Lasna [`0x8f01d459…`](https://lasna.reactscan.net/tx/0x8f01d459591e2448bade1580c5be0d868ed03cf32cea8be838de133a0e728633) → Base Sepolia [`0xf044fbf0…`](https://sepolia.basescan.org/tx/0xf044fbf02967a0ab057b3ccebf7f4a2464b261d190f166b299fabf4617fc34d0) (cycle 10) | `testnet only` |
| Rebalance: move skipped because the change is below the minimum | `test_NoTradeBelowTheMinimumTradeSizeIsSkipped` | Lasna [`0xdfa5152a…`](https://lasna.reactscan.net/tx/0xdfa5152aaac0e6c654ca358c6eba1866757ea3ce5e8361e12b7bce3d7018b651) (cycle 1, `NoTrade`); the count is in `docs/CLAIMS.md` | `testnet only` |
| Envelope mirrored from the vault and enforced | `test_LimitsAreMirroredFromTheVault` | Base Sepolia [`0x43b429ec…`](https://sepolia.basescan.org/tx/0x43b429ecec86391364bb4b8b3e3c6a4f6e774609ad050d3dae7a2c5e319359a1) (`LimitsUpdated`) | `testnet only` |
| Owner withdraws from the vault | `test_TheOwnerCanWithdrawPartOfTheVault`, `test_TheOwnerCanWithdrawEverything`, `test_WithdrawingMoreThanTheVaultHoldsReverts` | none — no withdrawal has been made from the live vault | `unit test only` |
| Owner pauses the vault | `test_APausedVaultRefusesDepositsAndCallbacksButLetsTheOwnerLeave`, `test_PausingEmitsThePauseEvent`, `test_PausedVaultRejectsProposals` | none — the live vault has never been paused | `unit test only` |

**Range width.** The enforcer clamps `rangeWidthBps` into the user's band and the vault records the width it was last given, but the deployed mock pool opens a position at the width supplied and does not re-centre an existing one when only the width changes. In the recorded run every LP position was opened at 4000 bps, so the width did not change while a position was open. This is a limitation of the mock venue, not a claim that the range was re-centred on chain; the Python backtest models the range and its cost directly. See `docs/BENCHMARK.md`, "what this backtest does not simulate".

## State transition table

| From | Action | To | Actor | Notes and unexpected-ordering behavior |
| --- | --- | --- | --- | --- |
| Idle | trigger fires (volatility / rate / cron) | Awaiting proposal | reactive contract | `cycleId` increments; a callback to the vault is requested; the vault emits `DecisionRequested` |
| Awaiting proposal | a valid proposal arrives | Executed | reactive contract | `cycleId` must match, timestamp inside the freshness window, sender must be the registered agent |
| Awaiting proposal | a proposal outside the limits arrives | Executed (clamped) | reactive contract | `ProposalClamped` is emitted with the original and the clamped values |
| Awaiting proposal | a stale / mismatched / foreign proposal arrives | Awaiting proposal | reactive contract | rejected; the cycle stays open until the freshness window closes |
| Awaiting proposal | the freshness window closes with no proposal | Idle | reactive contract | the cycle is abandoned; no funds move |
| Idle | realized volatility breaches the exit level | Executed (forced) | reactive contract | the contract forces `lpShareBps = 0` **without asking the model**; `AutonomousExit` is emitted |
| Any | a callback arrives with a `cycleId` already used | unchanged | vault | the vault rejects the replay; the reactive contract's `cycleId` is single-use |
| Any | a callback arrives from an address other than the callback proxy | unchanged | vault | `NotAuthorized` |
| Any | the vault is paused | unchanged | vault | every money-moving call is refused; the reactive contract keeps running and its callbacks fail |

## Claims registry

`docs/CLAIMS.md`. Every factual number in the README, docs, UI and submission description comes from here. Values are generated by `scripts/claims.py`, not typed.

| Claim | Value | Source of truth | Verification command | Verified on |
| --- | --- | --- | --- | --- |
| *populated by `scripts/claims.py`* | | | | |

## Software surface

| Item | Value |
| --- | --- |
| Surface type (CLI, SDK, API) | CLI + HTTP |
| Command or endpoint | `python -m helm_agent.cli` runs the loop; `python -m helm_agent.cli --status` prints the deployment; `GET /api/state` and `GET /proof.json` on the dashboard; `scripts/collect-evidence.py`, `scripts/claims.py`, `scripts/verify-deployment.sh` |
| Required environment | `HELM_AGENT_PRIVATE_KEY` and `HELM_AGENT_ADDRESS` for the loop; `HELM_RPC_URL`; `HELM_LLM_API_KEY` only for the optional paid explanation. Addresses default to `deployments/base-sepolia.json` |
| Output that proves it works | `--status` prints the addresses; `/proof.json` returns the deployment and the last cycle; `/api/state` returns the vault, the enforcer, the envelope, the ledger and the backtest |
| How the output is checked against the chain or service | `scripts/verify-deployment.sh` runs 26 checks, including the runtime-vs-artifact comparison for both contracts, and exits non-zero on any mismatch |
| Clean-checkout run confirmed | ☑ — `python -m helm_agent.cli --status` needs only the committed deployment record; see the gate result A11 |

## Evidence table

| Step | Actor | Transaction | Link | Observed result |
| --- | --- | --- | --- | --- |
| Vault funded with 100,000 test USD | owner | Base Sepolia `0xeeb2d62beec1613f892d30a1d271eb94010218fdb7f164b8355c14804c0baaea` | [BaseScan](https://sepolia.basescan.org/tx/0xeeb2d62beec1613f892d30a1d271eb94010218fdb7f164b8355c14804c0baaea) | `Deposited`; the vault supplied the balance to the lending pool |
| Envelope approved once | owner | Base Sepolia `0x43b429ecec86391364bb4b8b3e3c6a4f6e774609ad050d3dae7a2c5e319359a1` | [BaseScan](https://sepolia.basescan.org/tx/0x43b429ecec86391364bb4b8b3e3c6a4f6e774609ad050d3dae7a2c5e319359a1) | `LimitsUpdated`: LP 0–4000, range 500–4000, cooldown 20 s, vol exit 1200, min trade 1000, freshness 600 |
| Cycle 2 opened and asked | enforcer | Lasna `0x01a2ab43…` → Base Sepolia `0x01de5b2b…` | [Reactscan](https://lasna.reactscan.net/tx/0x01a2ab43f717831ff4a2b9d5092210d83e4cdfed9b4e206f0245c0be7a948c34) | `CycleOpened` on Lasna; `DecisionRequested` on Base Sepolia |
| Cycle 2 proposed | agent | Base Sepolia `0x465a48e0fde71a2fafff5fdada8785ec42b4ce9129ab7ab169aae67d484dd980` | [BaseScan](https://sepolia.basescan.org/tx/0x465a48e0fde71a2fafff5fdada8785ec42b4ce9129ab7ab169aae67d484dd980) | the model asked for 7102 bps of LP |
| Cycle 2 clamped and executed | enforcer → vault | Lasna `0xebd2fb0a…` → Base Sepolia `0xd3e33f0e…` | [Reactscan](https://lasna.reactscan.net/tx/0xebd2fb0a4d66dd2ca62ae68af90932ca7d92a7bf3e377fc9e90e0b89c9d23070) | 7102 → 4000 bps, mask `LP_ABOVE_MAX`; the vault moved $40,000 into the LP position |
| Cycle 9 refused | enforcer | Lasna `0x4b56e9be…` | [Reactscan](https://lasna.reactscan.net/tx/0x4b56e9bed865264e93255c3f7476e08739bbc519b2ac1ef390e77435ca843f7e) | `CYCLE_MISMATCH`; no callback moved funds |
| Cycle 10 autonomous exit | enforcer → vault | Lasna `0x8f01d459…` → Base Sepolia `0xf044fbf0…` | [Reactscan](https://lasna.reactscan.net/tx/0x8f01d459591e2448bade1580c5be0d868ed03cf32cea8be838de133a0e728633) | volatility 1801 bps > 1200; LP forced 4000 → 0 with no proposal in the cycle |
| Cycle 13 second LP opening | enforcer → vault | Lasna `0x544fe3c6…` → Base Sepolia `0x0439a062…` | [Reactscan](https://lasna.reactscan.net/tx/0x544fe3c634e9e32c5a3d6b480e03a90944f2ac82c41f43e4b48dcd68d0bebc71) | 7102 → 4000; the vault opened LP again after the exit |
| Cycle 37 economic veto | enforcer → vault | Lasna `0x0d2845aa…` → Base Sepolia `0x6c23b7fd…` | [Reactscan](https://lasna.reactscan.net/tx/0x0d2845aa3c3dd6e30863c29f836871d72e65813bc4974d741893a949912d6e58) | 7102 → 0 bps, mask `LP_ABOVE_MAX, ECONOMIC_VETO`; LP pulled to lending |
| The agent is removed (17–24 Nov) | — | cycle 182 opens `0x5ba6faa6…` and expires `0xa057f3e8…` | [Reactscan](https://lasna.reactscan.net/tx/0x5ba6faa6365cb168640086e207730459da6125a97b3164e01cb5588c8c166d8b) | 586 consecutive cycles opened and written off with no proposal and no funds moved; the contract stayed safe without the AI |

## Pre-submission gate results

| Gate | Result | Note |
| --- | --- | --- |
| A1 on-chain runtime equals committed artifact | **pass** | `scripts/verify-bytecode.py` for both `HelmReactive` and `HelmVault`: identical at every byte outside the immutable sites, and every site holds the expected address (2026-11-25) |
| A2 verification script exits zero against live deployment | **pass** | `bash scripts/verify-deployment.sh` → 26 checks, all passed, exit 0 (2026-11-25) |
| A3 one toolchain and configuration for test, build, deploy | **pass** | one `contracts/foundry.toml` (solc pinned by `svm`/Foundry, optimizer 200, cancun, no viaIR) used by `forge test`, `forge build` and `scripts/deploy.sh` |
| A4 suite re-run against the deployed configuration | **pass** | 37 Foundry tests + 46 Python tests re-run 2026-11-25; the counts are written into `docs/CLAIMS.md` by `scripts/claims.py` |
| A5 no required form field empty | **blocked on the owner** | two fields remain: the DoraHacks builder profile URL and the submitted revision (filled at submission time) |
| A6 video public and shows the required build and transaction | **pass** | `https://helm-dashboard-six.vercel.app/helm-demo.mp4`, 164.92 s, unauthenticated 200, sha256 `bf2d04cb…` matches the committed `docs/helm-demo.mp4`; it shows the live dashboard and the cycle's transactions |
| A7 every headline claim enforced | **pass** | see the headline-claim table above; the agent-offline week is stated, not hidden |
| A8 every value-moving branch has a test and a status | **pass** | see the branch table above; two owner branches are `unit test only` and say so |
| A9 every factual number comes from the claims registry | **pass** | `docs/CLAIMS.md` regenerated by `scripts/claims.py` after the final evidence pass; README and submission counts are copied from it |
| A10 every evidence link opens and shows what it claims | **partially verified** | every Lasna Reactscan link opens; BaseScan's Cloudflare protection refuses this build machine's headless requests, so the Base Sepolia links were verified by reading the same transactions through the public RPC instead |
| A11 software surface runs from a clean checkout | **pass** | fresh `git clone` → `cd agent && uv sync` → `python -m helm_agent.cli --status` prints the deployment and `pytest` passes 46 (2026-11-25) |
| A12 network labels correct everywhere | **pass** | every address is labelled Lasna 5318007 or Base Sepolia 84532; the earlier Unichain Sepolia rows are removed |

## Competitive field

See `docs/COMPETITIVE-SCAN.md` for the full scan with links.

| Item | Value |
| --- | --- |
| Entries in the field, and how winners were decided | The DoraHacks builds tab is under organizer review, so the field could not be enumerated from the event page (23 builds, 185 hackers registered as of 2026-11-15). The field was scanned on GitHub instead: 20+ repositories publicly tag themselves with this event and track. No winners have been announced — the event is still open. |
| Prior winners inspected, with links | **No prior edition of the Reactive Omni Buildathon has concluded** — this is the first one (Reactive Omni went live on mainnet 2026-10-28; the announcement is dated 2026-11-04). The closest comparable rounds are the **Reactive bounty rounds** and the **UHI hookathon**, whose winning repositories are the pattern source (see `docs/COMPETITIVE-SCAN.md`). |
| Axes where winners were a near-universal subset (these decided the round) | On-chain reactive transactions and their callbacks, a public repo, a demo video under 3 minutes, and honest limitations. |
| Axes common across the whole field (these are noise) | "AI scores something and freezes something" — at least six entries in this track do it. |
| Approach the field has converged on | A neural network (often a small MLP with integer weights) that scores each event and trips a circuit breaker, a freeze, or a stop-loss. Models are trained on **synthetic** data. |
| Open axis we will take | A model that **allocates** under a user-set risk envelope, trained on **real market history** and evaluated **out of sample** against baselines — with the contract able to act **without** the model, and an on-chain record of the model's own forecast accuracy. |
| One sentence: on which axis do we beat the field? | Everyone else asks "is this event dangerous?"; Helm asks "what should the next hour's allocation be?", answers with a model trained on real market history, and proves it with an out-of-sample backtest instead of a circuit-breaker demo. |
| Structures taken from prior winners (proof page, proof endpoint, capability table, published package) | Proof endpoint and proof page; capability→file table; badge strip; one-sentence claim; honest limitations; a public repo with a runnable verifier. Structures only. |
| Ideas, designs, interfaces, or copy we did not take | No circuit-breaker, no anomaly detection, no synthetic training data, no integer-weight on-chain inference, no stop-loss. No competitor's interface or copy. |

## Deployment and cost

| Item | Value |
| --- | --- |
| Deployment target and plan | Reactive Lasna (5318007) for the enforcer; Base Sepolia (84532) for the vault, the token, the two mock pools, the agent and the callback proxy. Both are free testnets named by the event. |
| Public URL | dashboard `https://helm-dashboard-six.vercel.app` (Vercel project `helm-dashboard`, team `oxunify`); video at `https://helm-dashboard-six.vercel.app/helm-demo.mp4`. The dashboard reads the public RPCs `https://lasna-rpc.rnk.dev/` and `https://base-sepolia-rpc.publicnode.com` on every request. |
| Verified limits that matter for this build | Reactive tx gas cap **900,000**; callback gas limit minimum **100,000**; Lasna fee = `max(gasPrice, baseFee) × (gasUsed + 100,000)` with coefficient 1000/1000 and baseFee 100 gwei; the callback proxy charges the **recipient** about 0.000925 ETH per callback; a contract with debt > 0 receives nothing. |
| Restriction that could bite (commercial use, build caps, timeouts) | The 900,000 gas cap — `react()` must fit inside it, which the suite checks with `test_TheLiveEnvelopeRebalanceFitsInsideTheCallbackGasLimit`. lREACT is the real budget: measured at **0.0125–0.0147 lREACT per `react()`**, so a shortfall silently drops the subscription and can leave network debt. |
| Recurring cost and who pays | $0 for the testnets. lREACT comes from the Reactive faucet (1 Base Sepolia ETH → 100 lREACT); the enforcer currently holds 17.9 lREACT ≈ 1,378 more calls. The optional LLM explanation is paid from the owner's Kite Passport allowance (one recorded call cost $0.0073). |
| Sponsor allowance, if any, source, expiry, how to claim | Reactive faucet `0x2afaFD298b23b62760711756088F75B7409f5967` on Base Sepolia: `request(address)` with value, 1 ETH → 100 lREACT, max 5 ETH per tx. `scripts/topup-lreact.sh` wraps it, then `coverDebt()` and `setCronTopic()`. |
| Environment variables and where their values come from | `.env.example` lists every one; the real agent key lives only in the untracked `deploy-keys/addresses.txt` and the environment of the running process. |
| Verified how, and on what date | RPCs, chain ids, contract addresses, limits and balances read directly from the chains on **2026-11-25** by `scripts/verify-deployment.sh` (26 checks, exit 0): Lasna `https://lasna-rpc.rnk.dev/` (chainId 5318007, baseFee 100 gwei, `_extraGas` 100000, `_gasPriceCoeffPer1000` 1000), Base Sepolia `https://base-sepolia-rpc.publicnode.com` (chainId 84532). Callback proxy on Base Sepolia: `0x476F44b11F5C942c58f4c8E3d0300E5710743585`. |

## Benchmark and gap routing

See `docs/BENCHMARK.md`. Internal weights: Impact on the user 30 · Technical execution 20 · Innovation 15 · Demo and evidence 15 · Product and UX 10 · Sponsor technology use 10.

## Open questions

| Question | Owner | Needed by | Status |
| --- | --- | --- | --- |
| DoraHacks builder profile URL and the wallet to list as builder | owner | before submission | **open — the owner said they would share it; the only remaining form field besides the revision** |
| Kite Passport allowance for the Anthropic endpoint | owner | before the LLM layer is exercised | **resolved 2026-11-23** — the allowance reset and cycle 795 used it for a paid explanation ($0.0073, payment tx recorded in `agent/ledger/cycles.jsonl`) |
| Testnet ETH for the deployer `0x7225cC8352e80d402E83828EAdBC80767C04d222` and the agent `0x26127Ee61ECE6C105B575eD3296C5698323F029A` | owner | before deployment | **resolved** — both are funded (agent 0.174 ETH, vault 0.149 ETH for callback fees on 2026-11-25) and the loop is live |
| Whether the submission can be edited after submitting | — | before submission | unverified, assumption: yes |
