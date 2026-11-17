#!/usr/bin/env bash
# Helm vault setup on Base Sepolia: funding, market maker, agent gas, callback reserve.
#
# Reads deployments/base-sepolia.json, so it always works against the addresses of the most
# recent deployment. Safe to re-run: every step is idempotent or additive.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$PATH:/home/unify/.foundry/bin"

BASE_RPC="${BASE_RPC:-https://base-sepolia-rpc.publicnode.com}"
KEYS="$ROOT/deploy-keys/addresses.txt"
DEPLOYER_KEY="$(grep '^DEPLOYER_PRIVATE_KEY=' "$KEYS" | cut -d= -f2)"
DEPLOYER_ADDR="$(grep '^DEPLOYER_ADDRESS=' "$KEYS" | cut -d= -f2)"
AGENT_ADDR="$(grep '^AGENT_ADDRESS=' "$KEYS" | cut -d= -f2)"
CALLBACK_PROXY="0x476F44b11F5C942c58f4c8E3d0300E5710743585"

read -r TOKEN LP_POOL LENDING VAULT < <(python3 -c "
import json
d=json.load(open('$ROOT/deployments/base-sepolia.json'))
print(d['token'], d['lpPool'], d['lendingPool'], d['vault'])
")

VAULT_FUNDING="100000000000000000000000"   # 100,000 USD into the vault
MARKET_MAKER="10000000000000000000000000"  # 10,000,000 USD into the pool
REPLAY_FUNDS="50000000000000000000000"     # 50,000 USD for the replay's market-making swaps
AGENT_GAS="0.05ether"
VAULT_GAS="0.15ether"

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
tx() { cast send "$@" --rpc-url "$BASE_RPC" --private-key "$DEPLOYER_KEY" --legacy | grep -E "^(status|transactionHash)"; }

say "1. ETH reserve for the vault's callbacks on Base Sepolia"
# This comes first, on purpose. The callback proxy charges the *recipient* for every callback,
# and a vault that cannot pay the charge stops receiving callbacks altogether: the enforcer
# keeps asking, the vault never hears it, and the fund manager looks alive while doing
# nothing. The vault needs ETH in hand before the first callback can land.
tx "$VAULT" --value "$VAULT_GAS"

say "2. minting vault USD and approving the vault"
tx "$TOKEN" "mint(address,uint256)" "$DEPLOYER_ADDR" "$VAULT_FUNDING"
tx "$TOKEN" "approve(address,uint256)" "$VAULT" "$VAULT_FUNDING"

say "3. depositing the vault funding"
tx "$VAULT" "deposit(uint256)" "$VAULT_FUNDING"

say "4. minting market-maker USD and approving the pool"
tx "$TOKEN" "mint(address,uint256)" "$DEPLOYER_ADDR" "$MARKET_MAKER"
tx "$TOKEN" "approve(address,uint256)" "$LP_POOL" "$MARKET_MAKER"

say "5. seeding the pool with the market maker"
tx "$LP_POOL" "depositLiquidity(uint256,uint256,address)" "$MARKET_MAKER" "10000" "$DEPLOYER_ADDR"

say "6. funding the replay's swaps and approving the pool"
tx "$TOKEN" "mint(address,uint256)" "$DEPLOYER_ADDR" "$REPLAY_FUNDS"
tx "$TOKEN" "approve(address,uint256)" "$LP_POOL" "$REPLAY_FUNDS"

say "7. gas for the agent on Base Sepolia"
tx "$AGENT_ADDR" --value "$AGENT_GAS"

say "8. settling any callback fee the proxy already charged"
# The proxy pulls this on its own once the vault holds ETH, but paying it explicitly means the
# next callback is never held up by a balance the proxy has not collected yet.
tx "$VAULT" "coverDebt()"

say "9. state"
printf 'vault total value  : '; cast call "$VAULT" "totalValueUsd()(uint256)" --rpc-url "$BASE_RPC"
printf 'vault lp share bps : '; cast call "$VAULT" "lpShareBps()(uint256)" --rpc-url "$BASE_RPC"
printf 'pool liquidity usd : '; cast call "$LP_POOL" "liquidityUsd()(uint256)" --rpc-url "$BASE_RPC"
printf 'vault ETH          : '; cast balance "$VAULT" --rpc-url "$BASE_RPC"
printf 'vault callback debt: '; cast call "$CALLBACK_PROXY" "debt(address)(uint256)" "$VAULT" --rpc-url "$BASE_RPC"
printf 'agent ETH          : '; cast balance "$AGENT_ADDR" --rpc-url "$BASE_RPC"
