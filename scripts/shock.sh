#!/usr/bin/env bash
# Move the mock pool's price by a given number of basis points, in one transaction.
#
#   scripts/shock.sh 1800
#   scripts/shock.sh 18000 --wait-for-lp
#
# The mock pool publishes every price move as a `Swap`, and the Reactive contract on
# Lasna subscribes to those. A move bigger than the user's volatility exit level is what
# the contract's own autonomous exit is supposed to react to, without the model being
# asked and without the agent having any say in it.
#
# With --wait-for-lp the script first waits until the vault actually holds a liquidity
# position, so the exit has something to exit from. It gives up after the timeout.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$PATH:/home/unify/.foundry/bin"

BASE_RPC="${BASE_RPC:-https://base-sepolia-rpc.publicnode.com}"
KEYS="$ROOT/deploy-keys/addresses.txt"
DEPLOYER_KEY="$(grep '^DEPLOYER_PRIVATE_KEY=' "$KEYS" | cut -d= -f2)"

BPS="${1:-1800}"
WAIT_FOR_LP=0
TIMEOUT_SEC=300
for arg in "${@:2}"; do
  case "$arg" in
    --wait-for-lp) WAIT_FOR_LP=1 ;;
    --timeout=*) TIMEOUT_SEC="${arg#*=}" ;;
  esac
done

read -r POOL VAULT < <(python3 -c "
import json
d=json.load(open('$ROOT/deployments/base-sepolia.json'))
print(d['lpPool'], d['vault'])
")

if [[ "$WAIT_FOR_LP" == "1" ]]; then
  printf '\n\033[1m==> waiting for the vault to hold a liquidity position\033[0m\n'
  waited=0
  while [[ "$waited" -lt "$TIMEOUT_SEC" ]]; do
    LP="$(cast call "$VAULT" "currentLpShareBps()(uint256)" --rpc-url "$BASE_RPC" | awk '{print $1}')"
    printf '\r    lp share %6s bps   (%ss elapsed)' "$LP" "$waited"
    if [[ "$LP" -gt 0 ]]; then
      printf '\n'
      break
    fi
    sleep 3
    waited=$((waited + 3))
  done
  if [[ "${LP:-0}" -eq 0 ]]; then
    printf '\nthe vault never took a liquidity position; the shock would have nothing to exit from\n' >&2
    exit 1
  fi
fi

CURRENT="$(cast call "$POOL" "priceE18()(uint256)" --rpc-url "$BASE_RPC" | awk '{print $1}')"
NEW="$(python3 -c "
current = int('$CURRENT')
bps = int('$BPS')
print(current * (10000 + bps) // 10000)
")"

printf '\n\033[1m==> shocking the mock market\033[0m\n'
printf 'pool        %s\n' "$POOL"
printf 'price       %s -> %s (%+d bps)\n' "$CURRENT" "$NEW" "$BPS"
cast send "$POOL" "setPrice(uint256)" "$NEW" --rpc-url "$BASE_RPC" --private-key "$DEPLOYER_KEY" --legacy \
  | grep -E "^(status|transactionHash)"

