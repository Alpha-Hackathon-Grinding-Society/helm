# Helm — DoraHacks submission text

## Still to fill

- [ ] **Live app URL** — the dashboard URL has not been published yet.
- [ ] **Repository revision submitted** — this is filled at submission time from the submitted public Git commit.
- [ ] **Demo video URL** — the demo video has not been hosted yet.
- [ ] **Builder profile URL** — the owner still has to supply the DoraHacks builder profile URL.

The fields below are the text to paste into the submission form.
The three hosted-link fields marked below must not be submitted in that state.

## Project name

Helm

## One-line claim (vision)

Helm keeps your stablecoins earning under limits you set once: a neural network proposes the split every cycle, and a reactive contract clamps every proposal to your limits on-chain.

## Description

### Short description

Stablecoin funds have to be split between lending and liquidity provision, and today's best rate can be wrong by the next hour.
Helm uses an off-chain neural network to propose the split, then puts the proposal through a reactive contract that applies the user's limits before any funds move.
The enforcer runs on Reactive Lasna and reaches a vault on Base Sepolia through Reactive callbacks.
The evidence is live: the generated chain record contains 61 full cycles, 60 proposals clamped by the contract, 4 rebalances that moved test funds and 1 autonomous exit with no model proposal.
The backtest is also reported against simple alternatives, including the cases where Helm loses.

### Long description

#### The problem

A stablecoin fund cannot earn by choosing today's highest advertised rate and leaving the decision there.
Rates and volatility change, and the right share in a liquidity position depends on both the expected fee yield and the risk of the market moving.
Helm treats this as a recurring allocation problem rather than a one-off rate comparison.

The model is allowed to make a proposal.
It is not allowed to decide what happens.
The user's approved risk envelope is the authority, and the reactive contract applies it on-chain.

#### How it works

Helm has three parts.

- A PyTorch MLP runs off-chain and proposes the share of the vault that should sit in a liquidity position.
- `HelmReactive` on Reactive Lasna opens a cycle, receives the proposal event, checks it against the approved envelope and requests the permitted allocation.
- `HelmVault` on Base Sepolia holds the test funds and approved limits, and moves the position only when the pinned enforcer or Reactive callback proxy asks it to.

The allocation model is trained on real market history rather than synthetic examples.
The generated claims registry records 6694 training-history bars of 900 s, 6402 labelled dataset rows and 1921 held-out evaluation rows.
The history covers the Uniswap v3 ETH/USDC pool on Base mainnet at `0xd0b53D9277642d899DF5C87A3966A349A798F224`, whose pool fee is 5 bps.
The training run uses 300 epochs, a $100,000.00 capital base, a 300.0 bps lending rate and a 5.0 bps rebalance cost per trade.

On each cycle, the enforcer on Reactive Lasna opens a decision and calls the vault on Base Sepolia.
The agent listens for the vault's request, runs the model and posts a proposal on Base Sepolia.
The Reactive network carries that proposal event back to the enforcer on Reactive Lasna.
The enforcer clamps or refuses it, then requests the allowed action from the vault on Base Sepolia.
The vault records the resulting position and the cycle is complete.

Anthropic's language model is used only to write the plain-English explanation of a cycle.
It receives the facts already decided by the model and contract and never chooses an allocation amount.
If that paid explanation service is unavailable, Helm still answers the cycle with a deterministic explanation.

#### The Reactive integration

The Reactive contract is on Reactive Lasna, chain ID 5318007, at `0xf24f1d13F995a2368015868048F791426AfeD39C`.
The vault, token and both market mocks are on Base Sepolia, chain ID 84532.
The vault is at `0x9ED8FAD6627B89104b5a5C2C31334168Ce73EB77`.

The enforcer on Reactive Lasna subscribes to the mock market events on Base Sepolia and to the vault's proposal, limits, pause and agent events.
It uses those cross-chain events to open cycles, mirror the user's envelope, judge proposals and issue the next instruction.
The Base Sepolia callback proxy at `0x476F44b11F5C942c58f4c8E3d0300E5710743585` injects the calling enforcer's address, and the vault checks that pinned sender before it acts.

The reactive contract is the safety layer rather than a pass-through.
It applies the user's limits, rejects stale, foreign, replayed and mismatched proposals, skips a move below the minimum trade and can veto a liquidity position when its on-chain fee measurement does not beat lending.
It can also act without the model: if observed volatility breaches the approved exit level, the only autonomous move it may make is to force the LP share to zero.

#### The on-chain proof

`scripts/collect-evidence.py` reads the two chains and writes `docs/EVIDENCE.md` and `agent/ledger/chain-events.jsonl` from the same pass.
The generated record contains 75 cycles opened on Reactive Lasna, of which 61 are full cycles.
It contains 60 proposals clamped by the contract, 30 proposals stopped by the economic veto and 1 proposal refused before execution.
There are 4 rebalances that moved test funds, of which 2 opened a liquidity position, and 1 autonomous exit with no model proposal.
The median open-to-proposal latency is 33 s and the median open-to-enforced latency is 33 s; the worst observed times are 514 s and 513 s respectively.

The generated claims registry records 30 passing Foundry tests and 46 passing Python tests.
The live deployment verifier is `bash scripts/verify-deployment.sh`; it checks the addresses, wiring, envelope, deployed bytecode, callback funding, Reactive reserve and evidence record, and exits non-zero on any mismatch.

#### The backtest, including where Helm loses

The evaluation is out of sample on the held-out rows of real Base mainnet history.
The comparison uses the same capital, lending rate and rebalance cost for each strategy.

| Strategy | Total return | Max drawdown | Trades | Fees earned | Rebalance cost |
| --- | --- | --- | --- | --- | --- |
| Helm (the model) | -7.62% | -8.71% | 266 | $127.11 | $2,658.44 |
| Best rate now | -19.18% | -20.14% | 303 | $182.67 | $13,825.23 |
| Static 50/50 | -5.68% | -8.06% | 0 | $129.02 | $0.00 |
| All lending | 0.16% | 0.00% | 0 | $0.00 | $0.00 |
| All LP | -11.52% | -16.01% | 0 | $258.03 | $0.00 |

Helm beats the best-rate-now strategy by 11.56 percentage points of total return on this window.
That is not the whole result.
Helm loses to all lending by 7.79 points and to static 50/50 by 1.95 points.
The evaluated window is a falling market, so remaining in lending is the safer result on these rows.
Helm's 266 trades also cost $2,658.44 in rebalance cost.
The submission therefore makes no claim that the model beats every simple alternative or that it demonstrates savings.

#### Safety

The deployed user envelope allows an LP share from 0 to 4000 bps and a range width from 500 to 4000 bps.
It applies a 20 s cooldown, a 1200 bps volatility exit level, a 1000 bps minimum trade and a 600 s freshness window.
The vault stores that envelope and the enforcer mirrors it from the vault's `LimitsUpdated` event.

The vault pins both the Reactive callback proxy and the enforcer as its only permitted callback senders.
The agent key can post a proposal and nothing else.
The model proposal carries no authority to move funds, and the vault refuses to spend the same cycle twice.
Every clamp, refusal, no-trade, rebalance and autonomous exit is emitted as an on-chain event.

## Tech stack

- **Contracts:** Solidity, Foundry, the Reactive Omni library and OpenZeppelin contracts.
- **Reactive layer:** `HelmReactive` on Reactive Lasna (chain ID 5318007), with cross-chain callbacks to Base Sepolia (chain ID 84532).
- **Destination layer:** `HelmVault`, a mock ERC-20, a mock lending pool and a mock ETH/USDC pool on Base Sepolia.
- **Model and agent:** Python, a PyTorch MLP for allocation, Ethereum signing and chain clients, with pytest coverage.
- **Dashboard:** Next.js, React, TypeScript and viem for reading the live chain state.
- **Explanation layer:** Anthropic through the Kite Passport paid endpoint; it writes explanations only.
- **Evidence:** Foundry and `cast` for contract checks, plus `scripts/collect-evidence.py` for the generated on-chain record.

## Repository URL

https://github.com/Alpha-Hackathon-Grounding-Society/helm

## Repository revision submitted

Filled at submission time from the submitted public Git commit.

## Live app URL

TO BE FILLED AT SUBMISSION

## Contract addresses

| Contract | Network | Chain ID | Address | Explorer |
| --- | --- | --- | --- | --- |
| Reactive enforcer (`HelmReactive`) | Reactive Lasna | 5318007 | `0xf24f1d13F995a2368015868048F791426AfeD39C` | [Reactscan](https://lasna.reactscan.net/address/0xf24f1d13F995a2368015868048F791426AfeD39C) |
| Vault (`HelmVault`) | Base Sepolia | 84532 | `0x9ED8FAD6627B89104b5a5C2C31334168Ce73EB77` | [BaseScan](https://sepolia.basescan.org/address/0x9ED8FAD6627B89104b5a5C2C31334168Ce73EB77) |
| Mock USD token | Base Sepolia | 84532 | `0x51555FB414931F12Dc5d14E4cF02d09E7e663730` | [BaseScan](https://sepolia.basescan.org/address/0x51555FB414931F12Dc5d14E4cF02d09E7e663730) |
| Mock LP pool | Base Sepolia | 84532 | `0xa2e8273C708C77faFb13867e2406AF87Ee13A12a` | [BaseScan](https://sepolia.basescan.org/address/0xa2e8273C708C77faFb13867e2406AF87Ee13A12a) |
| Mock lending pool | Base Sepolia | 84532 | `0x49e57e791A9dd7b12F74c6767A8845156Fa0c1ed` | [BaseScan](https://sepolia.basescan.org/address/0x49e57e791A9dd7b12F74c6767A8845156Fa0c1ed) |
| Reactive callback proxy | Base Sepolia | 84532 | `0x476F44b11F5C942c58f4c8E3d0300E5710743585` | [BaseScan](https://sepolia.basescan.org/address/0x476F44b11F5C942c58f4c8E3d0300E5710743585) |

## Example transaction hash

Cycle 2 on Base Sepolia moved test funds into a 4000 bps liquidity position.

`0xd3e33f0e1dd7122cd3b0fcb1629305e2690ab86726d970c24910bd80667f0a19`

[Open the transaction on BaseScan](https://sepolia.basescan.org/tx/0xd3e33f0e1dd7122cd3b0fcb1629305e2690ab86726d970c24910bd80667f0a19)

## Explorer link

- Reactive Lasna explorer: https://lasna.reactscan.net/
- Base Sepolia explorer: https://sepolia.basescan.org/
- Cycle 2 judgement on Reactive Lasna: [`0xebd2fb0a4d66dd2ca62ae68af90932ca7d92a7bf3e377fc9e90e0b89c9d23070`](https://lasna.reactscan.net/tx/0xebd2fb0a4d66dd2ca62ae68af90932ca7d92a7bf3e377fc9e90e0b89c9d23070)
- Cycle 2 fund movement on Base Sepolia: [`0xd3e33f0e1dd7122cd3b0fcb1629305e2690ab86726d970c24910bd80667f0a19`](https://sepolia.basescan.org/tx/0xd3e33f0e1dd7122cd3b0fcb1629305e2690ab86726d970c24910bd80667f0a19)

## Demo video URL

TO BE FILLED AT SUBMISSION

## Builder profile URL

TO BE FILLED AT SUBMISSION

## Required tool or platform project URL

Reactive developer documentation: https://dev.reactive.network/

## Disclosures (funding, prior work, team)

- Helm was built during the Reactive Omni Buildathon.
- Helm has received no sponsor funding.
- The mock lending pool and mock LP pool are Helm's own test contracts.
- The allocation model is a PyTorch MLP.
- The LLM is Anthropic, accessed through Kite Passport.
- The LLM only writes explanations; it never chooses an allocation amount.
- The Reactive Omni library is a dependency, while the submitted contracts, agent, model pipeline, dashboard and evidence tools are the Helm submission.

## Other: transaction hashes showing the full loop

These are the transactions for complete cycle 2, which ended in a rebalance that moved test funds.
The rows are generated from `agent/ledger/chain-events.jsonl`, written by `scripts/collect-evidence.py` from the chain events themselves.

| Leg | Network | Transaction hash |
| --- | --- | --- |
| Cycle opened | Reactive Lasna | [`0x01a2ab43f717831ff4a2b9d5092210d83e4cdfed9b4e206f0245c0be7a948c34`](https://lasna.reactscan.net/tx/0x01a2ab43f717831ff4a2b9d5092210d83e4cdfed9b4e206f0245c0be7a948c34) |
| Vault asked | Base Sepolia | [`0x01de5b2b05cc5d4ce7baf896340c08462a0ff3c27d024aac62897eadce9476d5`](https://sepolia.basescan.org/tx/0x01de5b2b05cc5d4ce7baf896340c08462a0ff3c27d024aac62897eadce9476d5) |
| Agent proposal | Base Sepolia | [`0x465a48e0fde71a2fafff5fdada8785ec42b4ce9129ab7ab169aae67d484dd980`](https://sepolia.basescan.org/tx/0x465a48e0fde71a2fafff5fdada8785ec42b4ce9129ab7ab169aae67d484dd980) |
| Proposal judged | Reactive Lasna | [`0xebd2fb0a4d66dd2ca62ae68af90932ca7d92a7bf3e377fc9e90e0b89c9d23070`](https://lasna.reactscan.net/tx/0xebd2fb0a4d66dd2ca62ae68af90932ca7d92a7bf3e377fc9e90e0b89c9d23070) |
| Funds moved | Base Sepolia | [`0xd3e33f0e1dd7122cd3b0fcb1629305e2690ab86726d970c24910bd80667f0a19`](https://sepolia.basescan.org/tx/0xd3e33f0e1dd7122cd3b0fcb1629305e2690ab86726d970c24910bd80667f0a19) |

The separate autonomous-exit evidence is the enforcer transaction on Reactive Lasna [`0x8f01d459591e2448bade1580c5be0d868ed03cf32cea8be838de133a0e728633`](https://lasna.reactscan.net/tx/0x8f01d459591e2448bade1580c5be0d868ed03cf32cea8be838de133a0e728633) and the resulting vault transaction on Base Sepolia [`0xf044fbf02967a0ab057b3ccebf7f4a2464b261d190f166b299fabf4617fc34d0`](https://sepolia.basescan.org/tx/0xf044fbf02967a0ab057b3ccebf7f4a2464b261d190f166b299fabf4617fc34d0).

## What Helm does not do

- Helm is testnet only; there is no mainnet deployment.
- The lending pool and the LP position are mocks, not integrations with a real lending market or a real liquidity position.
- The market data in the demo is replayed from real Base mainnet history while the contract execution is live on Base Sepolia.
- On the evaluated window, the model loses to both always lending and static 50/50.
- The code is unaudited.
- This submission does not claim adoption, demand or savings.
