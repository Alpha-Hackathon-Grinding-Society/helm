# Helm — self-score

Two scores are recorded here, because the event and the build brief ask different
questions:

1. **The event's rubric** — four criteria, each scored 1–5, equal weight. This is the score
   that decides the round.
2. **The internal benchmark** — the 100-point weighting the build brief set as a stricter
   working target. It is not the event's scoring.

Every score below cites the artefact that earns it. Anything below the maximum carries a
concrete fix, with the work, the cost and the time it would take, and a verdict on whether
it is worth the remaining budget.

**On the design-time score.** The brief asked for a score after design and again at the end.
The design-time score was produced in the working session but was never written to the
repository, so there is no timestamped artefact for it. It is not reconstructed here: a
score with no artefact behind it is a guess, and this file exists to avoid exactly that.
The end score is the citable one, and the design decisions it rests on are in
[`BRIEF.md`](BRIEF.md).

---

## 1. The event rubric (1–5, equal weight)

### Execution — 5/5

*Criterion: "Does it run? We want to see the reactive transactions and the callbacks they
trigger on-chain. Entries without them aren't scored further."*

| What the criterion asks for | Evidence |
| --- | --- |
| A running loop, not a recording | The agent process answers live cycles: `runs/agent.log`, `agent/ledger/cycles.jsonl`. The most recent answered cycle is in the ledger. |
| Reactive transactions on chain | `docs/EVIDENCE.md` lists every cycle with the Lasna transaction that opened it and the Lasna transaction that judged it. `agent/ledger/chain-events.jsonl` is the machine-readable copy. |
| Callbacks they trigger | Every judged proposal carries the Base Sepolia transaction the callback produced: the vault's `Rebalanced` or `NoTrade`. `docs/EVIDENCE.md`, result column. |
| Well past the ten-cycle floor | The generated record in [`CLAIMS.md`](CLAIMS.md) reports the counts; the full-cycle count is more than ten times the event's minimum. |
| Proof that the deployed code is the committed code | `scripts/verify-bytecode.py` compares the deployed runtime against `contracts/out/…` byte by byte outside the immutable sites, and checks each site holds the expected address. `bash scripts/verify-deployment.sh` runs it with 26 other checks and exits non-zero on any mismatch. |
| A single hash a judge can open | Cycle 2: the model asks for 7102 bps, the contract allows 4000, and the vault moves $40,000 of test funds. Lasna [`0xebd2fb0a…`](https://lasna.reactscan.net/tx/0xebd2fb0a4d66dd2ca62ae68af90932ca7d92a7bf3e377fc9e90e0b89c9d23070) → Base Sepolia [`0xd3e33f0e…`](https://sepolia.basescan.org/tx/0xd3e33f0e1dd7122cd3b0fcb1629305e2690ab86726d970c24910bd80667f0a19). |

**Why not 4.** The gate is exercised, not merely satisfied: the record contains clamps, a
refusal, an economic veto and an autonomous exit, each on chain with a hash.

### Integration — 5/5

*Criterion: "Does the reactive contract do real work, or is it bolted on?"*

The reactive contract is the decision-maker, not a forwarder. `contracts/src/HelmReactive.sol`:

| Work the contract does itself | Test | On-chain evidence |
| --- | --- | --- |
| Decides **when to ask** — a cron tick, a volatility move or a rate move opens a cycle | `test_CronOpensACycle`, `test_RateAndPriceAreObserved` | every `opened` leg in `agent/ledger/chain-events.jsonl` |
| Enforces the user's envelope and clamps an out-of-range proposal | `test_LpShareAboveTheMaximumIsClamped`, `test_LpShareBelowTheMinimumIsClamped`, `test_RangeWidthIsClampedOnBothSides`, `test_MultipleClampsAreCombined` | cycle 2: 7102 → 4000 bps, mask `LP_ABOVE_MAX` |
| Refuses a proposal that is stale, foreign, mismatched, replayed, or arrives with no limits | `test_StaleProposalIsRejected`, `test_ProposalFromAStrangerIsRejected`, `test_ProposalForTheWrongCycleIsRejected`, `test_ReplayIsRejected`, `test_ProposalWithoutLimitsIsRejected`, `test_ProposalPreparedBeforeTheCycleOpenedIsRejected`, `test_PausedVaultRejectsProposals` | cycle 9: refused, `CYCLE_MISMATCH` |
| Rate-limits itself | `test_CronHonoursTheCooldown`, `test_TheOwnerCanExpireAPendingCycle` | the 20 s cooldown in the deployed envelope |
| Skips a move that is not worth the gas | `test_NoTradeBelowTheMinimumTradeSizeIsSkipped` | the `NoTrade` rows in the cycle log |
| Vetoes the liquidity leg when the fee yield it measured does not beat lending | `test_EconomicVetoKeepsTheVaultOutOfLp`, `test_EconomicVetoDoesNotFireWhenFeesBeatLending`, `test_TheFeeWindowStartsWithTheFirstFeeTheContractSees` | cycle 37: 7102 → 0 bps, mask `LP_ABOVE_MAX|ECONOMIC_VETO` |
| Acts **without the model** when volatility breaches the exit level | `test_AutonomousExitWhenVolatilityBreaksTheExitLevel`, `test_AutonomousExitMovesRealFundsOutOfThePool` | cycle 10: 1801 bps of volatility, LP forced to zero, no proposal in the cycle |
| Grades the model's forecast against what actually happened | `test_ForecastIsGradedOnTheNextCycle` | `ForecastGraded` rows in the evidence |
| Moves real funds only through the pinned callback path | `test_EndToEndMoveMovesRealFunds`, `test_TheLiveEnvelopeRebalanceFitsInsideTheCallbackGasLimit` | 4 rebalances in the record, 2 of which opened an LP position |

**The strongest evidence that it is not bolted on** is the week the agent was offline. From
2026-11-17 15:18 UTC to 2026-11-24 20:47 UTC the contract opened 586 consecutive cycles on its
cron subscription, wrote each one off when no proposal arrived inside the freshness window,
and moved no funds. Nothing needed to be switched off or protected by hand. That behaviour is
in the evidence record and is described in [`EVIDENCE.md`](EVIDENCE.md) and
[`CLAIMS.md`](CLAIMS.md).

### Usefulness — 4/5

*Criterion: "Does it solve a problem real users have?"*

The problem is real and measured: a stablecoin holder choosing between lending and
liquidity provision is choosing between a rate that changes hourly and an impermanent-loss
exposure they cannot price. The baseline that real products run — chase the best rate now —
returns **−19.18%** on the evaluated window while paying **$13,825** in costs.

Helm's result, out of sample, on real Base mainnet history:

| Strategy | Total return | Trades | Rebalance cost |
| --- | --- | --- | --- |
| **Helm (model + contract rules)** | **−4.26%** | 144 | $2,083 |
| Best rate now | −19.18% | 303 | $13,825 |
| Static 50/50 | −5.68% | 0 | $0 |
| All lending | +0.16% | 0 | $0 |
| All LP | −11.52% | 0 | $0 |

Helm beats `best rate now` by **14.91 points**, and in **4 of 4** consecutive disjoint
windows. It loses to `all lending` by **4.43 points**, and all four windows were falling
ones.

**Why not 5.** The only regime evaluated is a falling market, and in that regime the
cheapest strategy wins. The claim "Helm allocates well" is demonstrated against one
baseline family and not against the do-nothing baseline that actually matters to a user.
The build says so in the README, on the dashboard, in the submission and here.

| Fix | Work | Cost | Time | Worth it? |
| --- | --- | --- | --- | --- |
| Add a second evaluation window in a rising or sideways regime | Find an archive with more than the ~70 days of Base mainnet history available from public RPC (an Alchemy or QuickNode free key covers years), re-run `python -m helm_agent.train` over a date range that includes a rally, and report both regimes side by side | $0 on a free archive tier; a paid key is not needed for one backfill | 3–4 h including the re-run and the doc updates | **Yes, if there is time.** It is the single change that would move this score, and the harness already supports it — only the history file changes. It cannot be done by tuning the existing window, and pretending otherwise would be dishonest. |

### Craft — 5/5

*Criterion: "Readable code, a working demo, and documentation someone else could follow."*

| What the criterion asks for | Evidence |
| --- | --- |
| Readable code | Contracts are split into `HelmTypes`, `HelmReactive`, `HelmVault`, the mock pools and the token; the Python agent is split by concern (`model`, `features`, `policy`, `listener`, `chain`, `backtest`, `train`); the dashboard is two pages of components. |
| A working demo | [The live dashboard](https://helm-dashboard-six.vercel.app) reads the chain on every request (`dynamic = "force-dynamic"`, no fixtures, no cache), and the video is a screen recording of it: [`helm-demo.mp4`](helm-demo.mp4), 2 min 45 s, under the three-minute limit. |
| Documentation someone else could follow | `README.md` follows the PRD's order; `docs/ARCHITECTURE.md`, `docs/DEPLOYMENTS.md`, `docs/BENCHMARK.md`, `docs/CLAIMS.md`, `docs/EVIDENCE.md`, `docs/SUBMISSION.md`, `docs/DEMO-SCRIPT.md`, `docs/BRIEF.md` and this file. |
| Tests | 37 Foundry tests (30 on the reactive rules, 7 on the vault's money paths) and 46 Python tests over the model, the policy mirror, the chain decoders, the features and the backtest. |
| Reproducibility | `python -m helm_agent.train` regenerates the backtest; `scripts/collect-evidence.py` regenerates the on-chain record; `scripts/claims.py` regenerates every number; `bash scripts/verify-deployment.sh` checks the live deployment. |
| Licence | MIT, `LICENSE`. |

**Caveats that are not hidden.** There is no CI workflow; the agent is restarted by hand
and one live crash (a TLS drop inside a cycle) was found and fixed rather than papered
over; the video is silent.

---

## 2. The internal benchmark (100 points)

Weights: Impact on the user 30 · Technical execution 20 · Innovation 15 · Demo and evidence
15 · Product and UX 10 · Sponsor technology use 10.

| Dimension | Weight | Score | Basis (citation) |
| --- | --- | --- | --- |
| Impact on the user | 30 | **22** | The problem is real and the mechanism is enforced (`docs/BRIEF.md`, "the weakest part first"). The measured economics are negative against doing nothing: −4.26% against +0.16% (`docs/CLAIMS.md`). No user research, no payer, no demand test. |
| Technical execution | 20 | **19** | Two chains, 168 full cycles out of 798 opened, bytecode identity proven for both contracts (`scripts/verify-bytecode.py`), 26 live checks (`scripts/verify-deployment.sh`), 83 tests. One point off for no CI and a manual restart policy. |
| Innovation | 15 | **12** | The split — a network proposes, a contract disposes, and the contract can act with no proposal at all — is a real structural idea, and the field has mostly built circuit breakers instead (`docs/COMPETITIVE-SCAN.md`). It is not a new primitive: clamps and kill-switches exist. |
| Demo and evidence | 15 | **13** | 2 min 45 s video of the live system, per-cycle hashes, a generated evidence file, a dashboard that reads the chain. Two points off: the video is silent, and the market data in the demo is replayed rather than live. |
| Product and UX | 10 | **8** | The dashboard is an instrument panel with real loading, empty and error states, and it works on a phone. Two points off: the envelope is set with `scripts/set-limits.sh`, not in the interface, and there is no deposit or withdraw flow. |
| Sponsor technology use | 10 | **9** | Reactive is load-bearing: the cron subscription is what opens cycles, the cross-chain callbacks are what carry the decision, and the rules run where the user cannot edit them (`docs/ARCHITECTURE.md`). One point off because a keeper bot could reproduce part of the loop, just not inside a second and not without an off-chain watcher. |
| **Total** | **100** | **83** | |

### The gaps, and what closing each would take

| Gap | Lever | Work | Cost | Time | Verdict |
| --- | --- | --- | --- | --- | --- |
| Impact 22 → 30 | A regime where the allocation is worth making, plus one named user who wants it | Backfill a longer history from an archive node and re-run; and ask five stablecoin holders what they do today | $0 for the backfill; user conversations are free | 3–4 h + a week of conversations | **The backfill is worth it** (see Usefulness). The user research cannot be manufactured in the remaining time, and a fabricated answer would be worse than the honest gap. |
| Execution 19 → 20 | CI on every push | Add `.github/workflows/ci.yml` running `forge test`, `pytest` and `npm run build`; push and confirm the run is green | $0 | 1 h, plus the wait for the first run | **Cheap and worth it** if the remaining budget allows a verified green run; a red badge would be worse than none, so it is only worth doing with time to fix the first failure. |
| Innovation 12 → 15 | A mechanism nobody else in the field has | E.g. on-chain accountability for the model: stake, slash on measured forecast error, publish a per-model score | Contract work and a new test suite | 8–12 h | **Not worth it.** It changes the product, not the score, at this stage. |
| Demo 13 → 15 | Narration, and a live rather than replayed market leg | Record a voice-over over the existing capture; the explorer leg is already live | $0 (human voice); a TTS engine is absent | 1 h | **Partially worth it** — a human narration would help, but the build machine has no microphone and no synthesiser, and a synthetic voice reading hashes was judged worse than silence. |
| UX 8 → 10 | Set the envelope and move funds from the dashboard | Wallet connect, `setLimits` and `deposit` transactions, a limits form with the same validation the contract applies | $0 | 4–6 h | **Not worth it now.** It is the right next product step, and the current split — a script for the owner, a read-only dashboard for everyone else — is stated plainly in the docs. |
| Sponsor 9 → 10 | Nothing realistic | The one point is the honest cost of a keeper bot existing as an alternative for part of the loop | — | — | **Leave it.** Claiming otherwise would be the kind of padding this file is meant to avoid. |

---

## 3. What the score does not cover

- **Whether the event's judges agree.** This is a self-score against the event's published
  criteria. It is not a prediction.
- **Whether the submission form is complete.** Two fields are the owner's: the builder
  profile URL and the submitted revision. See [`SUBMISSION.md`](SUBMISSION.md).
- **Whether the market result generalises.** It does not, yet: one regime, one pool, one
  70-day history, and the report says so.
