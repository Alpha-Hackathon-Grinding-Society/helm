#!/usr/bin/env bash
# Helm deployment to Base Sepolia (destination) + Reactive Lasna (enforcer).
#
# Order matters:
#   1. the reactive contract goes first, because the vault pins its address as the only callback sender
#   2. the vault goes second, with the reactive address baked in
#   3. the reactive contract is pointed at the vault
#   4. the user approves the risk envelope and funds the vault
#
# Usage: scripts/deploy.sh [--skip-lreact]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTRACTS="$ROOT/contracts"
KEYS="$ROOT/deploy-keys/addresses.txt"

export PATH="$PATH:/home/unify/.foundry/bin"

BASE_RPC="${BASE_RPC:-https://base-sepolia-rpc.publicnode.com}"
LASNA_RPC="${LASNA_RPC:-https://lasna-rpc.rnk.dev}"
SEPOLIA_RPC="${SEPOLIA_RPC:-https://ethereum-sepolia-rpc.publicnode.com}"

DEPLOYER_KEY="$(grep '^DEPLOYER_PRIVATE_KEY=' "$KEYS" | cut -d= -f2)"
DEPLOYER_ADDR="$(grep '^DEPLOYER_ADDRESS=' "$KEYS" | cut -d= -f2)"
AGENT_ADDR="$(grep '^AGENT_ADDRESS=' "$KEYS" | cut -d= -f2)"

CALLBACK_PROXY="0x476F44b11F5C942c58f4c8E3d0300E5710743585"
REACTIVE_FAUCET_SEPOLIA="0x9b9BB25f1A81078C544C829c5EB7822d747Cf434"

# The cron topic the enforcer subscribes to.
#
#   0xf02d6ea5...b514  every block   (one tick a second on Lasna)
#   0x04463f7c...b687  every 10 blocks (one tick every ten seconds)
#
# Every tick the network charges the contract roughly 0.0125 lREACT and *removes the
# subscription* when the balance runs out, so the ten-block topic is the default: it buys
# ten times the runway for the same money and the user's cooldown, not the tick rate, is
# what decides how often a cycle can open.
CRON_TOPIC="${CRON_TOPIC:-0x04463f7c1651e6b9774d7f85c85bb94654e3c46ca79b0c16fb16d4183307b687}"

# How much lREACT the enforcer starts with. This is fuel, not a deposit: the network spends
# it on every call. Twenty lREACT is about four thousand calls, which is days at the
# ten-block cron cadence.
REACTIVE_FUNDING="${REACTIVE_FUNDING:-20ether}"

# The user's approved risk envelope. The dashboard and the README show the same numbers.
LP_MIN=0
LP_MAX=4000
RANGE_MIN=500
RANGE_MAX=4000
COOLDOWN=20
VOL_EXIT=1200
MIN_TRADE=1000
FRESHNESS=600

START_PRICE="2000000000000000000000"   # 2000 USD, 1e18
LENDING_RATE=300
LENDING_UTIL=240

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
tx_lasna() { cast send "$@" --rpc-url "$LASNA_RPC" --private-key "$DEPLOYER_KEY" --legacy | grep -E "^(status|transactionHash)"; }
tx_base() { cast send "$@" --rpc-url "$BASE_RPC" --private-key "$DEPLOYER_KEY" --legacy | grep -E "^(status|transactionHash)"; }

deploy() {
  local target="$1"; shift
  local out
  out=$(cd "$CONTRACTS" && forge create "$target" \
      --broadcast --rpc-url "$BASE_RPC" --private-key "$DEPLOYER_KEY" \
      --legacy --json --constructor-args "$@")
  echo "$out" | python3 -c 'import sys,json; print(json.load(sys.stdin)["deployedTo"])'
}

deploy_lasna() {
  local target="$1"; shift
  local value="$1"; shift
  local out
  out=$(cd "$CONTRACTS" && forge create "$target" \
      --broadcast --rpc-url "$LASNA_RPC" --private-key "$DEPLOYER_KEY" \
      --legacy --json --value "$value" --constructor-args "$@")
  echo "$out" | python3 -c 'import sys,json; print(json.load(sys.stdin)["deployedTo"])'
}

# --------------------------------------------------------------------------------------------------
say "0. balances"
cast balance "$DEPLOYER_ADDR" --rpc-url "$BASE_RPC"
cast balance "$DEPLOYER_ADDR" --rpc-url "$LASNA_RPC"

# --------------------------------------------------------------------------------------------------
if [[ "${1:-}" != "--skip-lreact" ]]; then
  say "1. buying lREACT with Sepolia ETH (1 ETH -> ~105 lREACT on Lasna)"
  LREACT_BEFORE=$(cast balance "$DEPLOYER_ADDR" --rpc-url "$LASNA_RPC")
  if [[ "$LREACT_BEFORE" == "0" ]]; then
    cast send "$REACTIVE_FAUCET_SEPOLIA" "request(address)" "$DEPLOYER_ADDR" \
      --value 0.5ether --rpc-url "$SEPOLIA_RPC" --private-key "$DEPLOYER_KEY" --legacy \
      | grep -E "^(status|transactionHash)"
    say "waiting for the lREACT to land on Lasna"
    for _ in $(seq 1 30); do
      sleep 5
      LREACT_NOW=$(cast balance "$DEPLOYER_ADDR" --rpc-url "$LASNA_RPC")
      [[ "$LREACT_NOW" != "0" ]] && break
    done
  fi
  echo "lREACT on Lasna: $(cast balance "$DEPLOYER_ADDR" --rpc-url "$LASNA_RPC")"
fi

# --------------------------------------------------------------------------------------------------
say "2. deploying the Base Sepolia markets"
TOKEN=$(deploy src/mocks/MockERC20.sol:MockERC20 "Helm USD" "HUSD" "$DEPLOYER_ADDR")
echo "MockERC20          $TOKEN"
LP_POOL=$(deploy src/mocks/MockEthUsdcPool.sol:MockEthUsdcPool "$TOKEN" "$START_PRICE")
echo "MockEthUsdcPool    $LP_POOL"
LENDING=$(deploy src/mocks/MockLendingPool.sol:MockLendingPool "$TOKEN" "$LENDING_RATE" "$LENDING_UTIL")
echo "MockLendingPool    $LENDING"

# --------------------------------------------------------------------------------------------------
say "3. deploying HelmReactive on Lasna"
# The contract starts with enough lREACT to pay the network for every cycle it reacts to.
REACTIVE=$(deploy_lasna src/HelmReactive.sol:HelmReactive "$REACTIVE_FUNDING" "$DEPLOYER_ADDR" "$CRON_TOPIC")
echo "HelmReactive       $REACTIVE"

# --------------------------------------------------------------------------------------------------
say "4. deploying HelmVault on Base Sepolia (callback sender pinned to the reactive contract)"
VAULT=$(deploy src/HelmVault.sol:HelmVault "$CALLBACK_PROXY" "$REACTIVE" "$TOKEN" "$LENDING" "$LP_POOL" "$DEPLOYER_ADDR")
echo "HelmVault          $VAULT"

# --------------------------------------------------------------------------------------------------
say "5. wiring the reactive contract to the vault"
tx_lasna "$REACTIVE" "configure(address,address,address)" "$VAULT" "$LP_POOL" "$LENDING"
# The economic guard rails the demo needs: a 50 bps edge over lending, and a one-minute
# observation window before the contract is willing to trust its own fee measurement.
tx_lasna "$REACTIVE" "setEconomicParams(uint256,uint256,uint256)" 50 60 3600

# --------------------------------------------------------------------------------------------------
say "6. writing the deployment record"
mkdir -p "$ROOT/deployments"
cat > "$ROOT/deployments/base-sepolia.json" <<JSON
{
  "chainId": 84532,
  "chain": "Base Sepolia",
  "rpc": "$BASE_RPC",
  "explorer": "https://sepolia.basescan.org",
  "deployer": "$DEPLOYER_ADDR",
  "agent": "$AGENT_ADDR",
  "token": "$TOKEN",
  "lpPool": "$LP_POOL",
  "lendingPool": "$LENDING",
  "vault": "$VAULT",
  "callbackProxy": "$CALLBACK_PROXY",
  "limits": {
    "lpShareMinBps": $LP_MIN,
    "lpShareMaxBps": $LP_MAX,
    "rangeWidthMinBps": $RANGE_MIN,
    "rangeWidthMaxBps": $RANGE_MAX,
    "cooldownSec": $COOLDOWN,
    "volExitLevelBps": $VOL_EXIT,
    "minTradeBps": $MIN_TRADE,
    "freshnessSec": $FRESHNESS
  },
  "reactive": {
    "network": "Reactive Lasna",
    "chainId": 5318007,
    "rpc": "$LASNA_RPC",
    "explorer": "https://lasna.reactscan.net/",
    "address": "$REACTIVE"
  }
}
JSON
cat "$ROOT/deployments/base-sepolia.json"

# --------------------------------------------------------------------------------------------------
say "7. user setup: the agent and the risk envelope"
tx_base "$VAULT" "setAgent(address)" "$AGENT_ADDR"
tx_base "$VAULT" "setLimits(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256)" \
  "$LP_MIN" "$LP_MAX" "$RANGE_MIN" "$RANGE_MAX" "$COOLDOWN" "$VOL_EXIT" "$MIN_TRADE" "$FRESHNESS"

# --------------------------------------------------------------------------------------------------
say "8. funding the vault, the market maker, the agent and the callback reserve"
bash "$ROOT/scripts/setup-vault.sh"
