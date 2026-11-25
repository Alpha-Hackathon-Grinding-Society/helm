# Helm — product brief

> **This brief was reconstructed after the build, not written before it.** The ordering it
> follows is the one the build should have followed. Where a decision was actually made
> late — and several were — this file says so rather than pretending otherwise. The
> reasons it records are the reasons the code takes.

## The weakest part first

**Helm's weakest claim is that the allocation is worth making at all.** On the evaluated
window the deployed system — the model's allocation with the contract's own rules on top
— returned **−4.26%**, while simply leaving the money in the lending pool returned
**+0.16%**. A strategy that does nothing beat Helm by 4.43 points. That is measured, it is
reproducible, and it is printed on the dashboard's own backtest page and in the README
rather than buried in a caveat.

The cause is the window, not the mechanism: the price fell 22.41% across the evaluation
period, and a full-range liquidity position is worth `sqrt(P1 / P0)` of what it was worth
when it was opened — a −11.91% drag before a dollar of fees. Helm earned $70 of fees and
paid $2,083 of rebalancing cost over 144 trades.

The evaluation region was then split into four consecutive disjoint five-day windows, and
**all four were falling** (−1.96%, −1.16%, −8.14%, −12.37%). Helm beat `best rate now` in
4 of 4 and `all LP` in 3 of 4, and beat `all lending` in 0 of 4. That is the honest shape
of the result: Helm's edge against a reactive strategy is consistent, and Helm's edge
against doing nothing is absent in this market.

What would change the assessment: a second evaluation window with a rising or sideways
price, in which the fee income is not swamped by impermanent loss; or a wider band where
the model's forecast has some edge; or a cost model closer to a real pool's. The honest
version of Helm's claim is therefore narrow, and it is the claim the submission makes:

> Helm beats the strategy real users actually run — **chasing the best rate available at
> that moment** — by **14.91 points**, on real Base mainnet history, out of sample, and in
> 4 of 4 disjoint windows. It does not beat doing nothing in a falling market, and it says
> so in the same place as the number.

Everything else in this build is in service of making that narrow claim checkable by a
judge who does not trust us.

## Who it is for

A stablecoin holder who wants their money to earn, and who does not want to be the
risk manager. Concretely: someone with a position large enough that the yield matters and
small enough that losing the principal to a bad automated trade matters more. They want
the machine to act, and they want a hard ceiling on what "act" means that does not depend
on the machine's judgement.

**Confidence: high.** This user shape is the PRD's own framing, and the event's track
rule ("the AI has to be part of the running system") only makes sense for a user who wants
the AI to act but not to be trusted.

## The situation that creates the need

Two tools exist and they pull in opposite directions.

- **Yield optimisers** ("best rate now") move the whole position to wherever the rate is
  highest at this instant. They are stateless: they have no memory of the rate they just
  left, and they rebalance freely. On the evaluated window they traded **303 times**, paid
  **$13,825** in costs and returned **−19.18%**.
- **Risk managers** want the opposite: a position approved once, and a machine that cannot
  talk them into anything outside it.

**What they do today:** either chase the rate and pay for it, or do nothing and earn the
lending rate. The gap is a third option that neither product offers — a machine that
proposes, and a contract that disposes, with the ceiling written down and enforced on
chain rather than promised in a policy document.

**Confidence: high on the mechanics, medium on the demand.** The cost of chasing rates is
measured. That anyone will pay for a different arrangement is not measured: no user
research was done, and there is no pricing decision in this build.

## The substitute, including doing nothing

The substitutes are not hypothetical:

1. **Do nothing.** Leave it in the lending pool. On the evaluated window this beat Helm
   by 4.43 points. It is free, needs no trust in anyone's model, and requires no audit.
2. **Chase the best rate now.** The baseline Helm is measured against, and the thing most
   yield products actually do. Helm beats it by 14.91 points, in 4 of 4 disjoint windows.
3. **Hold liquidity outright.** Returned −11.52% on the same window, with no trading cost
   at all.
4. **A fixed 50/50 split, rebalanced by hand.** Returned −5.68%, and Helm beat it by
   1.41 points while making 144 trades and paying $2,083 to do it.

Every one of these is cheaper and simpler than Helm. Helm's case has to be that a
**bounded, autonomous, auditable** allocator is worth more than a hand-managed one over
time — a claim this build demonstrates mechanically (the contract enforces the envelope
whatever the model says) but only partly demonstrates economically (it loses to lending
on the window measured, and beats a hand-managed 50/50 by less than the cost of the extra
trades it makes).

**Confidence: the weakness is real; the mechanism is not the weak part.** The contract
side is what the judges can check, and it is the part that works. The allocation side is
where the model is weak, and the build says so in the same place as the number.

## The outcome that changes for them

The user signs an envelope once: how much of the vault may sit in liquidity, how wide the
range may be, how long the cooldown is, what volatility forces an exit, how small a trade
is still worth doing, and how stale a price may be before it is refused.

After that, the expected outcome is not "a better rate". It is: **the machine can act,
and it cannot act outside the envelope** — and every time it acts, the decision, the
clamp that was applied and the reason are on chain with a transaction hash. The agent can
be switched off, and the vault is still protected, because the volatility exit rule lives
in the contract and does not need the model.

**Confidence: high for the mechanism (it is on chain and verifiable), low for the
economics (measured, and negative against the do-nothing baseline).**

## The constraints

- **Reactive Network is required by the event**, and it is not decoration: the enforcer
  has to be woken by the chain and act without a transaction of its own, the decision has
  to cross from Lasna to Base Sepolia, and the rules have to run where nobody can edit
  them. A plain Solidity contract cannot watch anything, and a bot that polls cannot
  react inside a second.
- **lREACT is fuel, not a deposit.** The network spends roughly 0.015 lREACT per reactive
  call. A dry balance does not throw an error — the network simply stops calling the
  contract, and the contract can be left *in debt* because the charge settles after the
  call. This is the single most surprising operational fact in the build and it has its
  own runbook: `scripts/topup-lreact.sh`.
- **Base Sepolia blocks arrive every 200 ms**, so every timer in the system is
  timestamp-based. The PRD says so explicitly and the code follows it.
- **The lREACT cost and the 1-second Lasna block time pull in opposite directions.** A
  1-second cadence produces a cycle a second and burns the reserve in a day; the
  deployment runs at a 1000-block cadence (about 17 minutes) for runway, and the dense
  evidence run used the 10-block cadence.
- **The paid explanation endpoint was out of allowance** for the second half of the build.
  The ledger records which explanation source was used for each cycle rather than
  pretending the LLM was always in the loop.
- **Base Sepolia's public archive is limited**, so the training history is about 70 days
  of real mainnet data rather than the year the PRD asked for.

## Explicit non-goals

- **Real money, or mainnet.** This is unaudited code. The PRD says so and the submission
  says so.
- **A general trading agent.** Helm allocates a stablecoin vault between exactly two
  venues: one lending pool and one liquidity position.
- **A strategy that chooses its own risk.** The envelope is the user's. The model never
  sees it and cannot widen it.
- **Maximising the backtest.** The build reports the loss to `all lending` in the README,
  on the dashboard, and in the generated claims registry. It does not tune the evaluation
  window until the model wins.
- **A general-purpose trading SDK.** The software surface is one agent CLI, two HTTP
  endpoints and a set of scripts.
- **Real liquidity provision.** The LP pool and the lending market are Helm's own mocks
  on Base Sepolia, so the fee and impermanent-loss arithmetic is arithmetic, not a
  market.

## Verified, assumed, proposed

| Claim | Label | Evidence | Confidence |
| --- | --- | --- | --- |
| The loop runs end to end on two chains, and every leg has a transaction hash | **verified** | `docs/EVIDENCE.md`; `bash scripts/verify-deployment.sh` passes 26 checks against the live deployment | high |
| The contract clamps, refuses, vetoes and exits on its own | **verified** | the generated on-chain record in `docs/CLAIMS.md`; 37 Foundry tests | high |
| The deployed runtime is the committed artifact | **verified** | `scripts/verify-bytecode.py`: identical at every byte outside the immutable address sites | high |
| Helm beats `best rate now` by 14.91 points out of sample, in 4 of 4 disjoint windows | **verified** | `agent/models/metrics.json`, reproduced by `python -m helm_agent.train`; `docs/BENCHMARK.md` | high |
| Helm loses to `all lending` by 4.43 points on the evaluated window | **verified** | same run, same file | high |
| Helm beats `static 50/50` by 1.41 points, having paid $2,083 of rebalance cost to do it | **verified** | same run, same file | high |
| The contract's economic veto removes 0.64 points of the model's loss, and would have fired in 64% of the window | **verified** | `feeSummary` in `agent/models/metrics.json`; the rule itself is on chain | high |
| The fee and impermanent-loss model is a fair approximation of a real v3 position | **assumed** | the arithmetic is in `agent/helm_agent/backtest.py`; it has not been checked against a live position's realised PnL | medium |
| A user would rather have a bounded autonomous allocator than a hand-managed one | **assumed** | no user research was done; the brief's framing comes from the PRD | low |
| The model has an edge on a sideways or rising market | **proposed, untested** | all four evaluation windows happened to be falling; no non-falling window has been run | low |
| The LLM explanation layer adds value to a real user | **proposed, untested** | it was not exercised in the live run because the paid allowance was exhausted | low |
| A user would pay for Helm | **proposed** | no pricing work was done; there is no revenue claim anywhere in this build | very low — deliberately |
