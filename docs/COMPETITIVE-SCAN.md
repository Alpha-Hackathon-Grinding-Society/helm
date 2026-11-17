# Competitive scan — Reactive Omni Buildathon, *Reactive Meets AI* track

Scanned 2026-11-15. Sources: the DoraHacks event and builds pages, the Reactive Network announcement,
GitHub repository search across the event's public tag lines, and the README of each entry inspected.

## 1. There is no prior edition of this event

Reactive Omni went live on mainnet on **2026-10-28**; the buildathon was announced on **2026-11-04** and runs
to **2026-12-05**. This is the first Reactive Omni Buildathon, so **there are no previous winners of this
event to copy**. The closest comparable rounds on the same ecosystem are:

| Round | Nature | Why it is comparable | What it teaches |
| --- | --- | --- | --- |
| Reactive bounty rounds (e.g. the Cross-Chain Oracle challenge) | Scored rounds run by the Reactive team on the same platform, with a judged winner | Same judges, same platform, same "show the reactive transaction and the callback" bar | The wins were decided by *evidence density* — deployed addresses, real hashes, and a working demo — not by contract complexity |
| UHI hookathon (Uniswap v4 hooks on Reactive) | Previous Reactive-adjacent hackathon with published winner write-ups | Same platform, same cross-chain callback mechanics, and the blog published each finalist's approach | The strongest entries published a *flow diagram plus a per-step transaction table*; several were shortlisted on documentation quality |
| Arc / ETHGlobal rounds inspected in the reusable winning-patterns reference | Adjacent judged hackathons on other stacks | Used only for **structure** (proof page, proof endpoint, capability table, published package, honest limitations) | Structural patterns, not ideas |

Because no prior edition of *this* event exists, the scan below is of the **live field** — the entries
building right now — which is a stronger signal anyway: they are the competition, and their state of
completion is the bar.

## 2. The live field (GitHub, public repos tagged with this event)

23 builds and 185 hackers are registered on DoraHacks. The builds tab reads "The organizer is reviewing
Builds", so the published field is not enumerable from the event page. The field below was recovered from
GitHub repository search over the event's tag lines. Entries marked **(AI track)** are direct competitors.

### Direct competitors, *Reactive Meets AI* track

| Entry | What it built | Why it scores well | What it misses |
| --- | --- | --- | --- |
| [wwaterfall2027/reactive-sentinel](https://github.com/wwaterfall2027/reactive-sentinel) **(AI track)** | A 6-8-1 neural network executed **inside `react()` on Lasna**, scoring every Base Sepolia swap; trips a circuit breaker that freezes withdrawals | Boldest possible reading of the track rule; integer inference in Solidity matches the float model 100% on 2,000 checks; live dashboard; a swap-by-swap decision table with explorer links; honest "trained on synthetic data" caveat | **Synthetic training data.** The model detects a manipulated move, not a real market. It is a *detector* — it can say no, never *what to do*. No user-facing product |
| [sainath998/neural-watchdog](https://github.com/sainath998/neural-watchdog) **(AI track)** | A 5-8-1 network inside the reactive contract scores every vault withdrawal and freezes the vault above p=0.9 | Concrete harm prevented with numbers (0.098 saved of 0.098 at risk); live dashboard; a per-step on-chain score table | **Synthetic training data.** A binary freeze. Scores withdrawals, not allocations. No user-facing product |
| [halfabillion/aegis-reactive](https://github.com/halfabillion/aegis-reactive) **(AI track)** | A small net publishes a *stop policy*; the reactive contract applies it to each price; the vault re-checks the drawdown against its own entry before closing | The clearest separation of "model publishes" from "contract decides"; `RULES.md`, `DEPLOYMENTS.md`, a 93-second captioned video | **Weights are hand-set, not fitted.** The README says so. The LLM hook is disabled. It still only decides *stop or not* |
| [Night-Etrenal/agent-risk-guard](https://github.com/Night-Etrenal/agent-risk-guard) **(AI track)** | An "AI risk oracle" posts a 0-100 risk verdict; a Lasna reactive contract freezes an agent vault | Clean three-contract architecture; uses the **Omni** API correctly (`SYSTEM.subscribe`, `requestCallbackV_1_0`); honest note that Base Sepolia faucets were gated so it moved to Ethereum Sepolia | The model is an **LLM verdict** (`gpt-6-luna`), not a forecasting network. `deployments/…json` is still "filled after a successful testnet deploy" — **not deployed** |
| [enderzcx/RIFI](https://github.com/enderzcx/RIFI) | "AI decides. Reactive executes." — an autonomous trading agent on Base with Reactive stop-loss/take-profit | Big surface area, real integrations | The AI is an LLM news/OSINT pipeline, not a forecast model; it is a wrapper around stop-loss, which the event's own track-1 entries already do better |

### The wider field (other tracks) — the converged pattern

Stop-loss and take-profit guardians dominate: [Klowor2002/stop-loss-sentinel](https://github.com/Klowor2002/stop-loss-sentinel),
[Dimaa099/secondshield](https://github.com/Dimaa099/secondshield), [Godson-droid/reflex](https://github.com/Godson-droid/reflex),
[Nassami1/omnistop](https://github.com/Nassami1/omnistop), [luongs3/tripwire-reactive](https://github.com/luongs3/tripwire-reactive),
[faduuuu1/reactive-latency](https://github.com/faduuuu1/reactive-latency). Circuit breakers and drains dominate the security corner:
[0xward/contagion-stop](https://github.com/0xward/contagion-stop), [AlexLavoie42/reactive-vault-guard](https://github.com/AlexLavoie42/reactive-vault-guard),
[Revaaa28/guardian-angel](https://github.com/Revaaa28/guardian-angel), [apeirs/tripwire](https://github.com/apeirs/tripwire),
[mrphatom/reactive-sentinel](https://github.com/mrphatom/reactive-sentinel). Payments and automation fill the rest:
[Ajengayukusu/billpilot](https://github.com/Ajengayukusu/billpilot), [andreprasetyo/autopay-vault](https://github.com/andreprasetyo/autopay-vault),
[sainath998/instant-queue](https://github.com/sainath998/instant-queue), [edycutjong/ledgerlock](https://github.com/edycutjong/ledgerlock),
[chainwright/pursestrings](https://github.com/chainwright/pursestrings), [kerne-protocol/reserve-circuit-breaker](https://github.com/kerne-protocol/reserve-circuit-breaker).

### What the field has in common

| Axis | Shared by | Verdict |
| --- | --- | --- |
| A reactive contract on Lasna that subscribes to an origin event and requests a callback | essentially everyone | **Noise.** Table stakes. |
| A model that *detects* something and *freezes / stops / closes* | every AI-track entry | **Noise.** The round would be decided by this if it were the differentiator. |
| Training data that is **synthetic** | Sentinel, Neural Watchdog; Aegis uses hand-set weights | **Open axis.** Nobody has trained on real market history. |
| Integer-weight inference **inside `react()`** | Sentinel, Neural Watchdog | **Converged.** Doing this again is not a position. |
| A model that decides *what to do* (an allocation) rather than *whether to act* | **nobody** | **Open axis.** |
| A user-facing product with onboarding | **nobody** — every entry is a dashboard that shows a contract reacting | **Open axis.** |
| **Deployed** with real transaction hashes on the testnet | several entries are still `filled after a successful testnet deploy` | **Open axis, and the cheapest one to win.** The event's first screening criterion is that the reactive transactions exist on-chain. |
| Full-loop latency measured end to end | only [faduuuu1/reactive-latency](https://github.com/faduuuu1/reactive-latency) (explicitly) and a few casually | **Partly open.** The announcement says the strongest entries show it. |
| A machine-readable proof endpoint a judge can fetch unauthenticated | rare | **Open axis.** |

## 3. The ideas worth borrowing, and how each shapes Helm

Nothing is copied. These are *structures* and *insights*.

| # | Insight | Source | How Helm takes it |
| --- | --- | --- | --- |
| 1 | **A model must be separable from the authority.** The moment the model's output can be *checked*, the entry stops being "AI verdict then freeze" and becomes a real system. | Aegis: the vault re-checks the drawdown against its own entry before acting | Helm splits authority into two layers: the **reactive contract** holds the limits and clamps; the **vault** holds the funds and refuses anything that did not come through the callback proxy with a fresh, single-use `cycleId`. The model proposes, the contract decides, the vault executes. Nothing is trusted, including the contract's own caller. |
| 2 | **Honesty about the training data buys credibility that accuracy claims cannot.** | Sentinel: "trained on synthetic data … not a production manipulation detector" | Helm trains on **real Base mainnet history** and reports the held-out result against baselines, including where Helm loses. The claim is narrow enough to be true. |
| 3 | **A judge must be able to check without trusting a screenshot.** | winning-patterns reference: the proof endpoint is "the cheapest credibility in a judged round" | Helm ships `GET /proof.json` (unauthenticated, same facts as the page) and a `scripts/verify-deployment.sh` that byte-compares the live runtime with the committed artifact. |
| 4 | **Show the whole loop, leg by leg.** | UHI finalists and the event announcement | Helm's evidence table has one row per leg of one cycle, each with a block number and an explorer link, plus the **end-to-end latency** in seconds and in Reactive blocks. |
| 5 | **A number you cannot regenerate is decoration.** | winning-patterns reference: hand-written numbers rot | Every number in Helm's README and dashboard comes from `scripts/claims.py`, which reads the chain and the artifacts. |
| 6 | **Judges are not domain experts and have minutes.** | winning-patterns reference: onboarding belongs in the product | Helm's dashboard opens on the user's actual job — *state your goal once, approve the limits, never touch it again* — with the cycle log and the proof second. The LLM turns the goal sentence into limits the user reviews before anything is signed. |
| 7 | **The funding wall is real and it stops most entries.** | AgentRiskGuard: "public faucets were gated on mainnet ETH, so origin/destination is Ethereum Sepolia"; several entries still not deployed | Helm funds on the chains the PRD names (Base Sepolia + Unichain Sepolia), deploys, and publishes real hashes. The lREACT budget is planned against the measured Lasna fee formula rather than guessed. |

## 4. The axis Helm takes

> **Everyone in this track asks "is this event dangerous?" and freezes when it is. Helm asks "what should the
> next hour's allocation be?", answers with a neural network trained on real market history and evaluated
> out of sample, and proves it with an out-of-sample backtest instead of a circuit-breaker demo — while a
> reactive contract on-chain holds the limits, clamps the model, and can de-risk the vault even when the
> model is switched off.**

Three parts make that a position rather than a slogan:

1. **The model is responsible for the money decision.** It forecasts next-hour lending rate, next-hour
   realized volatility, next-hour LP fee income and next-hour impermanent loss, and the allocation follows
   from those four numbers. It is not a threshold and it cannot say "no".
2. **The contract is responsible for the risk.** It holds the user's approved envelope, clamps every
   proposal into it, rejects stale, mismatched and foreign proposals, and — on a volatility breach — forces
   the LP share to zero **without asking the model at all**. Kill the agent and the user is still protected.
3. **Both are auditable.** The contract grades the model's own forecast against realized outcomes, on-chain.
   A judge can watch the model be wrong, watch the contract clamp it, and watch the score move.

## 5. What Helm deliberately does not take from the field

- No circuit breaker, no anomaly detector, no stop-loss, no freeze-on-score.
- No synthetic training data.
- No integer-weight inference inside `react()`. Helm's model is a PyTorch network running off-chain, because
  the point is a *good forecast*, not a small one — and because a model that can be retrained on new history
  is the product, while a hard-coded weight blob is a demo.
- No competitor's interface, copy, contract design, event names or scenario framing.
- No pretense of mainnet readiness, adoption, or measured savings that do not exist.
