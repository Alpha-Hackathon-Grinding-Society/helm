# Skill map

Helm was built during the Reactive Omni Buildathon with the locally installed `hackathon-build` skill and the workflow files it points to. This file records which instructions shaped the build, where the resulting evidence lives, and where the build departed from those instructions.

“Consulted” below means that the instruction set was read. “Used” is narrower: it means that this repository contains a trace of the instruction being applied. A file listed as evidence does not, by itself, prove that every related gate passed.

## Skills and workflows consulted

| Skill or workflow file | What it asks for | Used? | Evidence in this repository |
| --- | --- | --- | --- |
| `hackathon-build` | Establish the event target, build the smallest complete journey, expose proof and a programmatic surface, then verify and prepare delivery | yes | `docs/EVENT-RULES.md`, `docs/ARCHITECTURE.md`, `docs/EVIDENCE.md`, `scripts/verify-deployment.sh` |
| `hackathon-scoring-gates` | Turn the rubric into gates; prove artifact identity, claims, branch coverage, a software surface, demo honesty and submission completeness | partly | `docs/EVENT-RULES.md`, `docs/CLAIMS.md`, `scripts/verify-bytecode.py`, `scripts/claims.py` |
| `hackathon-demo-check` | Exercise the actual journey, a changed input, a failure path, responsive and keyboard behaviour, and every submission link | partly | `docs/DEMO-SCRIPT.md`, `scripts/demo-video.mjs`, `runs/agent.log` |
| `hackathon-runbook` | Follow the fixed phase sequence, budget the work by phase, and leave a checkable artefact at each phase | partly | `docs/EVENT-RULES.md`, `docs/ARCHITECTURE.md`, `docs/EVIDENCE.md`, `docs/SUBMISSION.md` |
| `verification` | Map requirements to outputs and evidence, use complementary checks, preserve artefact identity, and distinguish fresh evidence from reused evidence | partly | `docs/BRIEF.md`, `docs/CLAIMS.md`, `scripts/verify-deployment.sh`, `agent/ledger/chain-events.jsonl` |
| `value-articulation` | Test the moment, reframe, substitute, payer, repeat and payment evidence before presenting the product as worthwhile | partly | `docs/BRIEF.md`, `docs/BENCHMARK.md`, `docs/COMPETITIVE-SCAN.md` |
| `product-development` | Establish the problem and constraints, verify hosting feasibility, build the operational journey, and keep the repository useful to a new user | partly | `docs/BRIEF.md`, `docs/EVENT-RULES.md`, `docs/ARCHITECTURE.md`, `README.md` |
| `hackathon-discovery` | Establish official event constraints, scan the field, investigate the customer case and alternatives, then hand the chosen idea to the build | partly | `docs/EVENT-RULES.md`, `docs/COMPETITIVE-SCAN.md`, `docs/BRIEF.md` |
| `frontend-build` | Put the operational journey first, connect real state, handle states and small screens, and verify the result in a browser | yes | `dashboard/src/app/page.tsx`, `dashboard/src/app/cycles/page.tsx`, `dashboard/src/lib/chain.ts`, `dashboard/src/app/globals.css` |
| `frontend-audit` | Review the real interface for usability, accessibility, responsive behaviour and truthfulness, with a coverage inventory and prioritised findings | partly | Design guidance is reflected in `dashboard/src/app/globals.css` and `docs/ARCHITECTURE.md`; there is no formal audit report |

## What each part produced

### `hackathon-build`

- The instruction was to record the event rules, rubric, fields and eligibility before treating the build as ready to submit. Helm captured those in `docs/EVENT-RULES.md`, including a 20-day budget, the phase split and one evidence plan per rubric criterion.
- The smallest complete journey became the six-leg loop from cron trigger to vault result. `docs/ARCHITECTURE.md` describes the interface between `HelmReactive`, `HelmVault` and the agent; `docs/EVIDENCE.md` records the legs from both chains.
- The headline was made an enforcement input rather than decoration. The claim-to-rule table is in `docs/EVENT-RULES.md`; the rules and their tests are in `contracts/src/HelmReactive.sol`, `contracts/src/HelmVault.sol` and `contracts/test/HelmReactive.t.sol`.
- Judge-facing surfaces exist: `dashboard/src/app/proof.json/route.ts` serves `GET /proof.json`, `dashboard/src/app/api/state/route.ts` serves `GET /api/state`, and `agent/helm_agent/cli.py` provides the agent command.
- The repository’s own check is `bash scripts/verify-deployment.sh`; the contract suites can be run with `cd contracts && forge test` and the Python suite with `cd agent && .venv/bin/python -m pytest tests -q`.
- Not done fully: the demo and submission gates were not completed in the form requested, and no exact submitted revision is yet recorded.

### `hackathon-scoring-gates`

- Event rules, weights, gates, required fields, eligibility and open questions were recorded in `docs/EVENT-RULES.md`. The competitive-position section points to `docs/COMPETITIVE-SCAN.md` and states the open axis in one sentence.
- Artefact identity has a strict local implementation: `scripts/verify-bytecode.py` compares deployed runtime with Foundry output outside constructor-baked immutable addresses, and `scripts/verify-deployment.sh` calls it for both contracts.
- The headline claim has named enforcement paths, and the contracts have tests for rejection, clamping, the economic veto, no-trade, autonomous exit and replay handling. `docs/EVIDENCE.md` supplies target-network examples.
- A generated claims registry exists at `docs/CLAIMS.md`; `scripts/claims.py` reads model metrics, chain ledgers, deployment data, Foundry settings and test results. The chain record is regenerated by `scripts/collect-evidence.py`.
- The software surface is partly satisfied: `python -m helm_agent.cli` performs the proposal-and-reconcile action, while the two HTTP routes are read-only proof surfaces.
- Not done fully: several gate statuses remain blank, the artefact-hash identity record is incomplete, the claims registry is not enforced against all prose, and the submission packet is unfinished.

### `hackathon-demo-check`

- The expected journey was written as a shot list in `docs/DEMO-SCRIPT.md`: problem, risk envelope, live loop, on-chain clamp, backtest and architecture.
- `scripts/demo-video.mjs` records the deployed dashboard and the Reactive explorer transaction that enforced a clamp. It uses the live dashboard by default and points at the transaction named in `docs/EVIDENCE.md`.
- The journey has real failure and edge cases in the evidence: a refused proposal, an economic veto and an autonomous exit are recorded in `docs/EVIDENCE.md` and `docs/CLAIMS.md`.
- `runs/agent.log` records live agent responses and reconciliations, including restart recovery for an earlier cycle.
- Not done fully: there is no formal demo-check result table marked passed, failed or unverified, and no recorded fresh-session, narrow-viewport, keyboard or console-error result.

### `hackathon-runbook`

- The prescribed split was recorded before the build in `docs/EVENT-RULES.md`: toolchain 5%, rules capture 10%, product decision 15%, build 45%, audit 10%, demo rehearsal 5%, freeze 7% and submission 3%.
- Toolchain settings are pinned in `contracts/foundry.toml`; deployment details are in `deployments/base-sepolia.json` and `docs/DEPLOYMENTS.md`.
- The build phase produced the cross-chain loop, model pipeline, dashboard and evidence tools. The demo phase produced `docs/DEMO-SCRIPT.md` and `scripts/demo-video.mjs`.
- Not done in sequence: the product brief was reconstructed after the build, the formal audit phase is absent, the artefact freeze is not tied to a committed revision, and submission has not been completed.

### `verification`

- Helm uses complementary evidence: contract tests, Python tests, a held-out backtest, live chain reads, transaction histories and a deployment verifier. The commands are listed in `docs/CLAIMS.md` and `README.md`.
- `docs/BRIEF.md` maps important claims to artefacts and labels verified, assumed and proposed statements.
- `scripts/collect-evidence.py` writes `docs/EVIDENCE.md` and `agent/ledger/chain-events.jsonl` from one chain-reading pass, preserving source identity rather than transcribing rows by hand.
- `scripts/claims.py` regenerates the registry and records its timestamp and repository revision. The current registry says the revision is `not committed yet`.
- Not done fully: the exact artefact and submitted-revision identity is missing, and freshness is not enforced across every document that repeats a claim.

### `value-articulation`

- The reconstructed brief starts with the weakest part: Helm loses to leaving money in lending on the evaluated window. `docs/BRIEF.md` and `docs/BENCHMARK.md` show that result and the evidence behind it.
- The moment and reframe are stated as a stablecoin holder wanting recurring allocation without becoming the risk manager. The category is risk-bounded allocation rather than an AI or blockchain feature.
- The substitutes are concrete and include doing nothing: best-rate-now, all lending, static 50/50, all LP and manual management are compared in `docs/BENCHMARK.md`.
- Not done fully: there is no named paying customer, repeat-purchase event or payment evidence. `docs/BRIEF.md` says no user research or pricing work was done, so the payment question remains unresolved rather than passed.

### `product-development`

- The product brief now records the user, situation, outcome, constraints, non-goals, substitutes and weakest assumption in `docs/BRIEF.md`.
- Hosting and cost were treated as part of the design. `docs/EVENT-RULES.md` records the testnet topology, relevant limits and cost; `docs/DEPLOYMENTS.md` records the deployed addresses and testnet labels.
- The operational journey was built before any separate marketing page. The dashboard’s routes are listed in `docs/ARCHITECTURE.md` and implemented under `dashboard/src/app/`.
- The shared interface is documented in `docs/ARCHITECTURE.md`, including chain state, ledger records, error states and the two JSON routes.
- `README.md` gives a clone-and-run recipe, the agent command, the dashboard command, the deployment verifier and the repository map.
- Not done in the intended order: `docs/BRIEF.md` says it was reconstructed after the build, so it cannot prove that the weakest-part and constraint decisions shaped the original implementation.

### `hackathon-discovery`

- Official constraints, deadline, rubric, eligibility, required fields and the reactive-transaction execution gate are in `docs/EVENT-RULES.md`.
- `docs/COMPETITIVE-SCAN.md` records the live field, comparable prior rounds, the absence of a previous edition, common patterns and the axis Helm chose. It also distinguishes structural patterns from ideas that were not copied.
- The event field was not fully enumerable, so the scan says so and uses public repositories as the comparison set rather than claiming complete coverage.
- Not done fully: no preserved candidate comparison or original discovery handoff exists, and customer demand was not tested with users. The later brief is a reconstruction, not primary research.

### `frontend-build`

- The dashboard opens on current state, the latest decision, recent cycles, the backtest headline and deployment addresses. `dashboard/src/app/page.tsx` implements that hierarchy.
- Live and recorded truth are kept distinct in `dashboard/src/lib/chain.ts`: chain state is read live, cycle history comes from the ledgers, and backtest results are labelled as offline output.
- The interface has explicit empty and error states, including unreadable chain state. The split visualisation shows the model’s number, the enforced number and the clamp in `dashboard/src/components/split-bar.tsx`.
- The visual system, focus treatment and breakpoints are in `dashboard/src/app/globals.css`; the documented breakpoints are 860 and 560 pixels.
- Not done fully: no retained reference-inspection brief is available, and the repository does not contain a complete wide-and-narrow browser and keyboard verification record.

### `frontend-audit`

- The interface reflects the skill’s guidance on hierarchy, restrained colour use, non-colour status cues, visible focus and deliberate small-screen behaviour. The resulting rules are recorded in `dashboard/src/app/globals.css` and `docs/ARCHITECTURE.md`.
- The dashboard avoids misleading success states: chain failures show an error and missing ledger or metrics data shows an empty state rather than a fixture.
- Not done: there was no formal read-only completion audit of the finished dashboard, with an enumerated journey, state, viewport and role coverage inventory.
- No findings register or severity-ranked audit report exists, so this map does not claim accessibility conformance or a completed human usability study.

## Deviations

1. No continuous-workflow runner was used. The agent was started and restarted manually; `runs/agent.log` contains several separate starts and a failed `nohup` launch. The listener can recover an unfinished ledger entry, but there is no supervisor keeping it alive.
2. There is no first-party CI workflow file. The repository has no `.github/workflows/` directory; the vendored libraries under `contracts/lib/` are not Helm CI.
3. The hackathon demo check was applied by hand rather than run as a repeatable check with a formal result. `docs/DEMO-SCRIPT.md` and `scripts/demo-video.mjs` cover the presentation, not every item in the demo-check record.
4. **Resolved.** The real surfaces are `python -m helm_agent.cli` (the loop, `--status` prints the deployment), `GET /api/state` and `GET /proof.json`, plus the generation scripts. `docs/EVENT-RULES.md` now names exactly these and records the clean-checkout run (fresh clone → `uv sync` → `--status` prints the deployment, `pytest` 46 passed, 2026-11-25).
5. `frontend-audit` was used as a design reference rather than as a formal review of the finished dashboard. No completion-audit coverage inventory or findings report was produced.
6. The product-development brief was reconstructed after the build. `docs/BRIEF.md` states this explicitly, so it records the intended reasoning but not the original decision order.
7. **Mostly resolved.** `docs/SUBMISSION.md` now carries the live app URL, the video URL, the evidence counts and the backtest table; `docs/EVENT-RULES.md` has every gate result filled. What remains is the owner's: the DoraHacks builder profile URL and the submitted revision.
8. **Resolved.** `docs/CLAIMS.md` is regenerated by `scripts/claims.py` over the full deployment lifetime (807 cycles, 171 full, 170 clamped, 140 vetoed, 1 refused, 634 written off, 586-cycle outage run, 36 s / 582 s latency), and the README, `docs/SUBMISSION.md`, `docs/BRIEF.md` and `docs/SCORING.md` were updated to those numbers. The loop is still live, so the counts move between regenerations; each file states its generation timestamp. A scripted consistency check (regenerate and diff the prose) still does not exist — that is the remaining gap, and it is why the numbers are copied by hand at each regeneration.
9. **Resolved.** `scripts/claims.py` now writes an artifact-identity section: artifact path, byte length and keccak-256, on-chain byte length and keccak-256 for both `HelmReactive` and `HelmVault`, plus the byte-equality command. The deployment *transaction* hash is not in the registry; it is on the explorers linked from `docs/DEPLOYMENTS.md`.
10. **Resolved.** `docs/SCORING.md` records both scores with citations: the event rubric (Execution 5, Integration 5, Usefulness 4, Craft 5) and the internal 100-point benchmark (83/100 with per-dimension citations and a fix/work/cost/time/verdict table for every gap). The design-time score was never persisted and is not reconstructed.
11. The evidence remains builder-controlled testnet activity. Helm has no second-party workflow, adoption evidence or payment evidence, and its lending and liquidity venues are mocks. The one payment that does exist is the Kite Passport LLM explanation (cycle 795, $0.0073, payment tx in the ledger).
12. **Resolved.** The allowance reset on 2026-11-23 and the LLM explanation path was exercised live: cycle 795 carries a paid `claude-sonnet-4-5` explanation with its payment transaction. Most cycles still answer with the deterministic template when the LLM is slower than the cycle, which the code documents as the designed fallback.

## What the skills would still catch

- A formal demo-check record: mark each journey, changed input, recovery path, narrow viewport, keyboard path, runtime error and submission link as passed, failed or unverified. The existing recording script is not a substitute for that table.
- A completion audit of the dashboard, including mobile and desktop viewports, empty and failed dependency states, keyboard and focus order, and an inventory of which roles were exercised.
- Continuous delivery checks. A first-party workflow would need to run the Foundry suite, Python suite and dashboard checks on each change; a service supervisor would need to restart the agent and expose failed restarts. The agent is still started by hand (`/tmp` launcher), and it did die once on a Lasna TLS drop before the listener learned to survive `ChainError`.
- A scripted claims-consistency gate that regenerates `docs/CLAIMS.md` and fails the build if the prose tables in `README.md`, `docs/SUBMISSION.md`, `docs/BRIEF.md` or `docs/SCORING.md` drift from it.
- A complete submission packet with the exact public revision and the builder profile, and a record that the form was submitted. Nothing here records the submission itself.
- Primary customer evidence. The reconstructed brief cannot replace a named payer, a repeat event, payment evidence or a falsifiable demand test; closing this needs authorised user research rather than more implementation.
- A clearer route from the dashboard to the product's user journey. The deployed dashboard observes a configured vault, while limits are set through `scripts/set-limits.sh`; a usability review would decide whether that is adequate for the stated user.
