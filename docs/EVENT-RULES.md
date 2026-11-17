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

| Criterion (verbatim) | Weight | Our plan | Evidence we will produce | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| **Execution** — "Does it run? We want to see the reactive transactions and the callbacks they trigger on-chain. Entries without them aren't scored further." | 25% event / 20% internal | A full loop that runs on Lasna + Base Sepolia: origin `Swap` event → reactive transaction on Lasna → callback to Base Sepolia → agent proposal → reactive transaction → callback → vault rebalance. Every leg carries a transaction hash. | README cycle-log table with one row per cycle: origin tx, Lasna reactive tx, proposal tx, second Lasna reactive tx, callback tx, each with an explorer link. `docs/EVIDENCE.md` holds the same table with observed results. | contracts | ☐ |
| **Integration** — "Does the reactive contract do real work, or is it bolted on?" | 25% event / 30% internal (impact+exec) | The reactive contract is the **gatekeeper and the safety net**, not a forwarder. It decides when to ask the model, checks every proposal against on-chain limits, clamps out-of-range values, rejects stale/foreign/replayed proposals, skips no-op moves, **and can force the LP share to zero on a volatility breach without asking the model at all**. It also grades the model against realized outcomes on-chain. | `docs/ARCHITECTURE.md` reactive-logic spec; Foundry tests for trigger, freshness, clamp, cooldown, skip, autonomous-exit; a recorded cycle where the agent is offline and the contract still de-risks. | contracts | ☐ |
| **Usefulness** — "Does it solve a problem real users have?" | 25% event / 30% internal | "Best rate now" is wrong an hour later, and yield optimizers chase today's highest rate. Helm forecasts next-hour lending rate and volatility and allocates under a user-set risk envelope. The claim is proven with an **out-of-sample backtest on real Base mainnet history** against three baselines. | `agent/backtest/` output: final value, worst drawdown and rebalance count per strategy, generated by `scripts/claims.py` into `docs/CLAIMS.md`; the same chart on the dashboard. | agent | ☐ |
| **Craft** — "Readable code, a working demo, and documentation someone else could follow." | 25% event / 10+15 internal (UX+demo) | Foundry test suite for every reactive rule, pytest for the model and the forecast→allocation formula, CI, a one-command deployment script, a machine-readable proof endpoint, a live dashboard that reads the chain, and a demo under 3 minutes. | `docs/CLAIMS.md` (every number generated by a script), `scripts/verify-deployment.sh` exiting zero against the live deployment, the live dashboard, the video link. | all | ☐ |
| *Track rule* — "The AI has to be part of the running system, not just the tool you used to write the code." | gate | A **neural network** (PyTorch MLP) forecasts on every cycle and its output is what the reactive contract checks, clamps and executes. The LLM never chooses an amount. The agent can be switched off and the vault is still protected. | `agent/helm_agent/model.py` (the network), `agent/helm_agent/allocate.py` (the decision), the on-chain cycle log showing a model proposal being clamped, and the autonomous-exit cycle with no proposal at all. | agent | ☐ |
| *Event emphasis (from the announcement)* — "The strongest entries will show their latency numbers measured across the full loop, not just one leg of it." | evidence | Helm measures **end-to-end loop latency** in seconds and in Reactive blocks, from the origin event's block to the vault's rebalance block. | `docs/EVIDENCE.md` latency table, generated from the recorded blocks. | scripts | ☐ |

Internal benchmark (the weight set used for gap routing in `docs/BENCHMARK.md`), from the build brief:
Impact on the user 30 · Technical execution 20 · Innovation 15 · Demo and evidence 15 · Product and UX 10 · Sponsor technology use 10.
**The event's own criteria and weights govern the actual judging.** The internal benchmark is the stricter working target.

## Required submission fields

Checked against the DoraHacks event page and the announcement, not against memory.

| Field | Value we will submit | Verified link or artifact | Status |
| --- | --- | --- | --- |
| Project name | Helm | — | ☑ |
| One-line claim (vision) | "Helm keeps your stablecoins earning under limits you set once: a neural network proposes the split every cycle, and a reactive contract clamps every proposal to your limits on-chain." | README line 1 | ☐ |
| Description | see `docs/SUBMISSION.md` | `docs/SUBMISSION.md` | ☐ |
| Live app URL | dashboard on Vercel | — | ☐ |
| Repository URL | `https://github.com/Alpha-Hackathon-Grinding-Society/helm` | — | ☐ |
| Repository revision submitted | filled at submission time | `git rev-parse HEAD` | ☐ |
| Contract address(es) | Lasna reactive contract, Base Sepolia vault, mock pools | `docs/DEPLOYMENTS.md` | ☐ |
| Example transaction hash | one full loop | `docs/EVIDENCE.md` | ☐ |
| Explorer link | Lasna + Base Sepolia explorers | `docs/EVIDENCE.md` | ☐ |
| Video URL | demo under 3 minutes | — | ☐ |
| Builder profile URL | DoraHacks profile supplied by the owner | — | ☐ |
| Required tool or platform project URL | Reactive docs: https://dev.reactive.network/ | — | ☑ |
| Disclosures (funding, prior work, team) | built during the event; no sponsor funding; the mock pools are Helm's own; the AI is a PyTorch model, the LLM is Anthropic via Kite Passport | `docs/SUBMISSION.md` | ☐ |
| Other | the event's own requirement: "a few transaction hashes showing the full loop from origin event to callback" | `docs/EVIDENCE.md` | ☐ |

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
| Toolchain and version | Foundry — see `docs/CLAIMS.md` (generated) |
| Compiler version | solc — see `docs/CLAIMS.md` (generated) |
| Optimizer / runs | `optimizer = true`, `optimizer_runs = 200` (`contracts/foundry.toml`) |
| EVM target | `cancun` (`contracts/foundry.toml`) |
| `viaIR` | `false` (`contracts/foundry.toml`) |
| Artifact path in repository | `contracts/out/<Contract>.sol/<Contract>.json` |
| Artifact keccak-256 | generated |
| Artifact byte length | generated |
| Deployment transaction and block | generated from the chain |
| On-chain runtime keccak-256 | generated |
| On-chain byte length | generated |
| Comparison result | generated |
| Test suite re-run against this configuration (date, output file) | generated |
| Verification script and its exit status against the live deployment | `scripts/verify-deployment.sh` |

## Headline claim enforcement

| Assertion in the claim | Enforced by (contract rule / code path / mechanism) | Status |
| --- | --- | --- |
| "Helm keeps your stablecoins earning" | `HelmVault.rebalance()` moves the vault's balance between the lending pool and the LP position to the target split; `HelmVault` holds no strategy of its own | ☐ |
| "under limits you set once" | `HelmVault.setLimits()` stores the envelope; the owner approves it with one signature; `HelmReactive` reads it and cannot widen it | ☐ |
| "a neural network proposes the split every cycle" | `agent/helm_agent/model.py` produces the forecast; `agent/helm_agent/allocate.py` turns it into the split; the agent posts `ProposalPosted` on Base Sepolia | ☐ |
| "every cycle" | `HelmReactive` opens a cycle on a trigger (volatility move, rate move, or cron tick) and increments `cycleId` | ☐ |
| "a reactive contract clamps every proposal to your limits on-chain" | `HelmReactive._evaluate()` clamps `lpShareBps` and `rangeWidthBps` into the stored bounds, forces `lpShareBps = 0` above the exit level, and emits `ProposalClamped` | ☐ |
| "the contract enforces" | `HelmReactive` rejects a proposal whose `cycleId` does not match an open request, whose timestamp is outside the freshness window, or whose sender is not the registered agent; the vault rejects a repeated `cycleId` and refuses to act without a callback from the proxy | ☐ |

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

Status is one of: `mainnet exercised`, `testnet only`, `not built`. Nothing may be blank.

| Branch / path | Test | Target-network transaction | Status |
| --- | --- | --- | --- |
| Vault deposits test funds | — | ☐ | ☐ |
| Rebalance: move lending → LP | ☐ | ☐ | ☐ |
| Rebalance: move LP → lending | ☐ | ☐ | ☐ |
| Rebalance: LP share forced to 0 by the volatility exit (no model involved) | ☐ | ☐ | ☐ |
| Rebalance: move skipped because the change is below the minimum | ☐ | ☐ | ☐ |
| Rebalance: LP range re-centred at the proposed width | ☐ | ☐ | ☐ |
| Owner withdraws from the vault | ☐ | ☐ | ☐ |
| Owner pauses the vault | ☐ | ☐ | ☐ |

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
| Surface type (CLI, SDK, API) | CLI + HTTP API |
| Command or endpoint | `helmctl propose` / `helmctl status` / `helmctl backtest` / `helmctl verify`; `GET /proof.json`, `GET /api/cycles` |
| Required environment | `REACTIVE_RPC_URL`, `BASE_SEPOLIA_RPC_URL`, `AGENT_PRIVATE_KEY`, `HELM_VAULT_ADDRESS`, `HELM_REACTIVE_ADDRESS` |
| Output that proves it works | the vault's on-chain split, the last cycle's decision, the proof endpoint's JSON |
| How the output is checked against the chain or service | `scripts/verify-deployment.sh` compares the deployed runtime bytecode with the committed artifact and exits non-zero on any mismatch |
| Clean-checkout run confirmed | ☐ |

## Evidence table

| Step | Actor | Transaction | Link | Observed result |
| --- | --- | --- | --- | --- |
| ☐ | | | | |

## Pre-submission gate results

| Gate | Result | Note |
| --- | --- | --- |
| A1 on-chain runtime equals committed artifact | | |
| A2 verification script exits zero against live deployment | | |
| A3 one toolchain and configuration for test, build, deploy | | |
| A4 suite re-run against the deployed configuration | | |
| A5 no required form field empty | | |
| A6 video public and shows the required build and transaction | | |
| A7 every headline claim enforced | | |
| A8 every value-moving branch has a test and a status | | |
| A9 every factual number comes from the claims registry | | |
| A10 every evidence link opens and shows what it claims | | |
| A11 software surface runs from a clean checkout | | |
| A12 network labels correct everywhere | | |

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
| Deployment target and plan | Lasna testnet (5318007) for the reactive contract; Base Sepolia (84532) for the vault, the agent and the destination mock pools; Unichain Sepolia (1301) as the second origin signal. All free testnets. |
| Public URL and subdomain | dashboard on Vercel; public RPC for the dashboard's chain reads. |
| Verified limits that matter for this build | Reactive tx gas cap **900,000**; callback gas limit minimum **100,000**; Lasna fee = `max(gasPrice, baseFee) × (gasUsed + 100,000)` with coefficient 1000/1000 and baseFee 100 gwei; the callback proxy charges the **recipient**; a contract with debt > 0 receives nothing. |
| Restriction that could bite (commercial use, build caps, timeouts) | Reactive transaction gas cap 900,000 — the reactive contract's `react()` must fit. lREACT runs out quickly: ~0.02 lREACT per reactive transaction. |
| Recurring cost and who pays | $0. lREACT comes from the Reactive faucet (1 Base Sepolia ETH → 100 lREACT). LLM calls are paid from the Kite Passport allowance (owner). |
| Sponsor allowance, if any, source, expiry, how to claim | Reactive faucet: `0x2afaFD298b23b62760711756088F75B7409f5967` on Base Sepolia, call `request(address)` with value, 1 ETH → 100 lREACT, max 5 ETH per tx. |
| Environment variables and where their values come from | `.env.example` lists every one; real values live in the untracked `.env`. |
| Verified how, and on what date | RPCs and contract addresses read directly from the chains on 2026-11-15: Lasna `https://lasna-rpc.rnk.dev/` (chainId 5318007, baseFee 100 gwei, `_extraGas` 100000, `_gasPriceCoeffPer1000` 1000), Base Sepolia `https://sepolia.base.org` (chainId 84532, gasPrice 6,000,000 wei), Unichain Sepolia `https://sepolia.unichain.org` (chainId 1301). Callback proxies: Base Sepolia `0x476F44b11F5C942c58f4c8E3d0300E5710743585`, Unichain Sepolia `0x775c9B990ADe401060B78D0e98684eEf8d2466C1`. |

## Benchmark and gap routing

See `docs/BENCHMARK.md`. Internal weights: Impact on the user 30 · Technical execution 20 · Innovation 15 · Demo and evidence 15 · Product and UX 10 · Sponsor technology use 10.

## Open questions

| Question | Owner | Needed by | Status |
| --- | --- | --- | --- |
| DoraHacks builder profile URL and the wallet to list as builder | owner | before submission | **open — owner said they would share it** |
| Kite Passport account allowance for the Anthropic endpoint | owner | before the LLM layer is exercised | **open — allowance is `none` today** |
| Base Sepolia and Unichain Sepolia ETH for the deployer `0x7225cC8352e80d402E83828EAdBC80767C04d222` | owner | before deployment | **open — addresses sent to the owner** |
| Whether the submission can be edited after submitting | — | before submission | unverified, assumption: yes |
