# Helm deployment record

This is the judge-facing record of Helm's testnet deployment.
Every address below is a testnet address and must be read with its network name.
The canonical deployment record is `deployments/base-sepolia.json`.
The generated claims and evidence are in `docs/CLAIMS.md` and `docs/EVIDENCE.md`.

## 1. What is deployed where

| Contract | Network | Chain ID | Address | Explorer | What it does |
| --- | --- | --- | --- | --- | --- |
| `HelmReactive` | Reactive Lasna | 5318007 | `0xf24f1d13F995a2368015868048F791426AfeD39C` | [Reactscan](https://lasna.reactscan.net/address/0xf24f1d13F995a2368015868048F791426AfeD39C) | Opens decision cycles, receives cross-chain events, judges proposals and requests the permitted allocation. |
| `HelmVault` | Base Sepolia | 84532 | `0x9ED8FAD6627B89104b5a5C2C31334168Ce73EB77` | [BaseScan](https://sepolia.basescan.org/address/0x9ED8FAD6627B89104b5a5C2C31334168Ce73EB77) | Holds the test funds and approved limits, and is the only Helm contract that can move the position. |
| Mock USD token (`MockERC20`) | Base Sepolia | 84532 | `0x51555FB414931F12Dc5d14E4cF02d09E7e663730` | [BaseScan](https://sepolia.basescan.org/address/0x51555FB414931F12Dc5d14E4cF02d09E7e663730) | Test-only asset minted into the vault and market mocks. |
| Mock LP pool (`MockEthUsdcPool`) | Base Sepolia | 84532 | `0xa2e8273C708C77faFb13867e2406AF87Ee13A12a` | [BaseScan](https://sepolia.basescan.org/address/0xa2e8273C708C77faFb13867e2406AF87Ee13A12a) | Test-only liquidity venue used by the vault. |
| Mock lending pool (`MockLendingPool`) | Base Sepolia | 84532 | `0x49e57e791A9dd7b12F74c6767A8845156Fa0c1ed` | [BaseScan](https://sepolia.basescan.org/address/0x49e57e791A9dd7b12F74c6767A8845156Fa0c1ed) | Test-only lending venue used by the vault. |
| Reactive callback proxy | Base Sepolia | 84532 | `0x476F44b11F5C942c58f4c8E3d0300E5710743585` | [BaseScan](https://sepolia.basescan.org/address/0x476F44b11F5C942c58f4c8E3d0300E5710743585) | Reactive's cross-chain callback proxy; the vault accepts callbacks from this pinned address. |

The registered Helm agent is an externally owned account, not a contract.
Its address on Base Sepolia is `0x26127Ee61ECE6C105B575eD3296C5698323F029A`.
That account may post proposals on Base Sepolia but has no authority to move funds.

## 2. The wiring

The `HelmReactive` contract on Reactive Lasna points at:

- the `HelmVault` on Base Sepolia, at `0x9ED8FAD6627B89104b5a5C2C31334168Ce73EB77`;
- the mock LP pool on Base Sepolia, at `0xa2e8273C708C77faFb13867e2406AF87Ee13A12a`;
- the mock lending pool on Base Sepolia, at `0x49e57e791A9dd7b12F74c6767A8845156Fa0c1ed`; and
- the registered agent on Base Sepolia, at `0x26127Ee61ECE6C105B575eD3296C5698323F029A`.

The enforcer subscribes to the pools' swap, fee and rate events and to the vault's proposal, limits, pause and agent events.
Those subscriptions are pinned to the exact Base Sepolia addresses above.

The `HelmVault` on Base Sepolia pins two callers at construction:

- the Reactive callback proxy on Base Sepolia, at `0x476F44b11F5C942c58f4c8E3d0300E5710743585`; and
- the `HelmReactive` enforcer on Reactive Lasna, at `0xf24f1d13F995a2368015868048F791426AfeD39C`.

For a proxied callback, the proxy injects the calling enforcer's address as the first argument.
The vault accepts a callback from the pinned proxy or a direct call from the pinned enforcer, and nothing else.
The model and the agent key therefore never receive authority to move the vault's funds.

The risk envelope is stored by the owner on the `HelmVault` on Base Sepolia.
The vault emits `LimitsUpdated`, and `HelmReactive` on Reactive Lasna mirrors that envelope from the event.
The deployed values are:

| Limit | Stored and mirrored value |
| --- | --- |
| LP share minimum | 0 bps |
| LP share maximum | 4000 bps |
| Range-width minimum | 500 bps |
| Range-width maximum | 4000 bps |
| Cooldown | 20 s |
| Volatility exit level | 1200 bps |
| Minimum trade | 1000 bps |
| Freshness window | 600 s |

The enforcer on Reactive Lasna is subscribed to the cron topic for every 1,000 Lasna blocks
(`0xe20b31294d84c3661ddc8f423abb9c70310d0cf172aa2714ead78029b325e3f4`, about one cycle every
17 minutes), plus the vault's `ProposalPosted`, `LimitsUpdated`, `Paused` and `AgentChanged`
events and the LP pool's `Swap` / `FeeRateUpdated` and the lending pool's `RateUpdated` events.
The agent listens for the vault's `DecisionRequested` event on Base Sepolia and answers with a proposal event.
Only then can the enforcer on Reactive Lasna judge and enforce the proposal.

## 3. How to verify it yourself

Run this command from the repository root:

```bash
bash scripts/verify-deployment.sh
```

The verifier reads the two chains and the committed deployment artefacts.
It does not send a transaction.
It exits non-zero if any check fails.

| Check group | What it proves |
| --- | --- |
| Addresses | The enforcer on Reactive Lasna and the vault, token and both pools on Base Sepolia have contract code at the recorded addresses. |
| Wiring | The enforcer on Reactive Lasna points at the recorded vault, LP pool, lending pool and agent on Base Sepolia. |
| Risk envelope | The enforcer on Reactive Lasna has an envelope, and its on-chain values match the envelope recorded for the Base Sepolia vault. |
| Bytecode | The runtime code on each chain matches the committed Foundry artefact byte for byte outside the immutable addresses baked in at construction. |
| Callback funding | The vault on Base Sepolia has no callback debt and enough Base Sepolia ETH to receive callbacks; the agent also has Base Sepolia ETH to post proposals. |
| Reactive continuity | The enforcer on Reactive Lasna has a healthy lREACT reserve, owes the Reactive network nothing, has been called by the network and is subscribed to the recorded cron topic. |
| Evidence record | The generated ledger contains at least ten full cycles, a clamped proposal, an economic veto, a refused proposal, a rebalance that moved funds and an autonomous exit. |

`docs/CLAIMS.md` gives the checked test totals, and `docs/EVIDENCE.md` gives the generated cycle and latency tables.

## 4. One complete cycle, leg by leg

Cycle 2 is a complete cycle that ended in a rebalance which moved funds.
It is present in `agent/ledger/chain-events.jsonl` and in `docs/EVIDENCE.md`.
Both files are written from the same pass of `scripts/collect-evidence.py`, which reads the events directly from Reactive Lasna and Base Sepolia.

| Leg | Network | Transaction hash | Observed result |
| --- | --- | --- | --- |
| Cycle opened | Reactive Lasna | [`0x01a2ab43f717831ff4a2b9d5092210d83e4cdfed9b4e206f0245c0be7a948c34`](https://lasna.reactscan.net/tx/0x01a2ab43f717831ff4a2b9d5092210d83e4cdfed9b4e206f0245c0be7a948c34) | The enforcer opened cycle 2 and asked the vault for a decision. |
| Vault asked | Base Sepolia | [`0x01de5b2b05cc5d4ce7baf896340c08462a0ff3c27d024aac62897eadce9476d5`](https://sepolia.basescan.org/tx/0x01de5b2b05cc5d4ce7baf896340c08462a0ff3c27d024aac62897eadce9476d5) | The vault on Base Sepolia emitted `DecisionRequested` for cycle 2. |
| Agent proposal | Base Sepolia | [`0x465a48e0fde71a2fafff5fdada8785ec42b4ce9129ab7ab169aae67d484dd980`](https://sepolia.basescan.org/tx/0x465a48e0fde71a2fafff5fdada8785ec42b4ce9129ab7ab169aae67d484dd980) | The registered agent proposed 7102 bps in LP with a 4000 bps range. |
| Proposal judged | Reactive Lasna | [`0xebd2fb0a4d66dd2ca62ae68af90932ca7d92a7bf3e377fc9e90e0b89c9d23070`](https://lasna.reactscan.net/tx/0xebd2fb0a4d66dd2ca62ae68af90932ca7d92a7bf3e377fc9e90e0b89c9d23070) | The enforcer clamped the LP share from 7102 bps to 4000 bps with `LP_ABOVE_MAX` and requested the change. |
| Funds moved | Base Sepolia | [`0xd3e33f0e1dd7122cd3b0fcb1629305e2690ab86726d970c24910bd80667f0a19`](https://sepolia.basescan.org/tx/0xd3e33f0e1dd7122cd3b0fcb1629305e2690ab86726d970c24910bd80667f0a19) | The vault moved into a 4000 bps LP position worth $40,000.00 from a $100,000.00 test vault. |

For this cycle, the recorded open-to-proposal latency was 41 s, open-to-enforced was 40 s and open-to-funds-moved was 42 s.

## 5. Two other evidence cases

### A proposal clamped by the contract

Cycle 1 proposed 7102 bps in LP, but the enforcer on Reactive Lasna allowed 0 bps.
The clamp bits were `LP_ABOVE_MAX` and `ECONOMIC_VETO`.
The judgement is in transaction [`0xdfa5152aaac0e6c654ca358c6eba1866757ea3ce5e8361e12b7bce3d7018b651`](https://lasna.reactscan.net/tx/0xdfa5152aaac0e6c654ca358c6eba1866757ea3ce5e8361e12b7bce3d7018b651) on Reactive Lasna.

### The contract acting with no proposal

Cycle 10 has no proposal, no requested decision and no posted proposal in the ledger.
After observing 1801 bps of volatility, above the approved 1200 bps exit level, the enforcer on Reactive Lasna forced the LP share to zero by itself.
The autonomous-exit transaction is [`0x8f01d459591e2448bade1580c5be0d868ed03cf32cea8be838de133a0e728633`](https://lasna.reactscan.net/tx/0x8f01d459591e2448bade1580c5be0d868ed03cf32cea8be838de133a0e728633) on Reactive Lasna.
The resulting vault action on Base Sepolia is [`0xf044fbf02967a0ab057b3ccebf7f4a2464b261d190f166b299fabf4617fc34d0`](https://sepolia.basescan.org/tx/0xf044fbf02967a0ab057b3ccebf7f4a2464b261d190f166b299fabf4617fc34d0).

## 6. Funding and running costs

lREACT is fuel for the Reactive network, not a deposit into the vault.
The recorded charge is approximately 0.02 lREACT per reactive transaction.
The enforcer on Reactive Lasna keeps an lREACT reserve because the network consumes that balance on each call.
`reserveHealthy()` reports whether the reserve is above the floor, and `reserveCallsRemaining()` estimates the calls left from the balance and the conservative per-call estimate.
If the reserve runs out, the Reactive network stops calling the enforcer, so reserve health and network debt are part of the live verification.

The event deployment note records the Reactive faucet conversion as 1 Base Sepolia ETH for 100 lREACT.
The chain deployment target itself has a recorded recurring cost of $0.
Base Sepolia ETH pays for the Reactive callback and for the agent's proposal transactions.
Anthropic explanation calls, when enabled, are paid from the owner's Kite Passport allowance rather than from the vault.

The lending pool and LP position are Helm's own mocks on Base Sepolia.
The vault contains test tokens only.
No real money is deposited, lent or moved by this deployment, and the test tokens have no monetary value.

## 7. Re-deploying

`scripts/deploy.sh` sends transactions, so use only a dedicated testnet key.
It needs Foundry and `cast`, Python, access to Reactive Lasna and Base Sepolia, and Base Sepolia ETH.
It also needs `deploy-keys/addresses.txt` with `DEPLOYER_PRIVATE_KEY`, `DEPLOYER_ADDRESS` and `AGENT_ADDRESS`.
Unless `--skip-lreact` is passed, it uses Ethereum Sepolia ETH to obtain lREACT for the enforcer on Reactive Lasna.

The one-command flow is:

```bash
bash scripts/deploy.sh
```

That command:

- deploys the mock token and both mock markets on Base Sepolia;
- deploys `HelmReactive` on Reactive Lasna and `HelmVault` on Base Sepolia;
- wires the enforcer to the vault and pools, registers the agent and stores the risk envelope;
- writes the new `deployments/base-sepolia.json`; and
- calls `scripts/setup-vault.sh` to fund the test vault, markets, agent and callback reserve.

To fund or inspect an existing deployment without redeploying the contracts, run:

```bash
bash scripts/setup-vault.sh
```

`setup-vault.sh` reads `deployments/base-sepolia.json`, so it follows the most recent deployment record.
It needs the same deployment keys and Base Sepolia ETH.
Its steps are idempotent or additive: it reserves Base Sepolia ETH for callbacks, mints and deposits mock USD, seeds the mock market, funds the agent and settles callback debt.

After either flow, run the read-only check again:

```bash
bash scripts/verify-deployment.sh
```
