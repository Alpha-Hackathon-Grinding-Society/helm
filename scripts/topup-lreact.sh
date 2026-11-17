#!/usr/bin/env bash
# Top the enforcer's lREACT reserve up and make sure the reactive subscription is alive.
#
# ## Why this script exists
#
# On Reactive Lasna the lREACT held by a reactive contract is **fuel, not a deposit**: the
# network spends roughly 0.015 lREACT on every `react()` call. Two failure modes follow
# from that, and both are silent:
#
#   1. When the balance runs dry the network stops calling the contract. The subscription
#      is gone; the contract is not paused, it is simply never called again.
#   2. The charge is settled after the call, so a contract can be left *in debt*. A
#      contract that owes the system contract money is not called either, and topping the
#      balance up is not enough on its own — the debt has to be settled with `coverDebt()`.
#
# The recovery is always the same three steps: buy lREACT, send it to the enforcer with
# `fund()`, settle the debt with `coverDebt()`, and re-subscribe with `setCronTopic()`.
#
# ## The cron cadence
#
# The cadence decides the runway. The cron emitter publishes topics at several
# cadences; these were read off the emitter's own logs on Lasna:
#
#   0xf02d6ea5...b514   every block      (1 s on Lasna)
#   0x04463f7c...b687   every 10 blocks  (10 s)
#   0xb49937fb...c70    every 100 blocks (100 s)
#   0xe20b3129...3f4    every 1 000 blocks (1 000 s, about 17 minutes)
#   0xd214e1d8...a56    every 10 000 blocks (10 000 s, about 2.8 hours)
#
# At about 0.015 lREACT a call, the 1 000-block cadence turns 30 lREACT into roughly
# three weeks of running time, which is what the live deployment uses. The 10-block
# cadence is what the evidence run used, because it produces a cycle every ten seconds.
#
# Usage: scripts/topup-lreact.sh [--eth 0.25] [--topic 1000]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$PATH:/home/unify/.foundry/bin"

KEYS="$ROOT/deploy-keys/addresses.txt"
BASE_RPC="${BASE_RPC:-https://base-sepolia-rpc.publicnode.com}"
LASNA_RPC="${LASNA_RPC:-https://lasna-rpc.rnk.dev}"

DEPLOYER_KEY="$(grep '^DEPLOYER_PRIVATE_KEY=' "$KEYS" | cut -d= -f2)"
DEPLOYER_ADDR="$(grep '^DEPLOYER_ADDRESS=' "$KEYS" | cut -d= -f2)"

# The Reactive faucet on Base Sepolia: one ETH of Sepolia ETH buys 100 lREACT on Lasna.
REACTIVE_FAUCET_BASE="0x2afaFD298b23b62760711756088F75B7409f5967"

# The cron topics, by cadence in blocks.
declare -A CRON_TOPICS=(
  [1]=0xf02d6ea5c22a71cffe930a4523fcb4f129be6c804db50e4202fb4e0b07ccb514
  [10]=0x04463f7c1651e6b9774d7f85c85bb94654e3c46ca79b0c16fb16d4183307b687
  [100]=0xb49937fb8970e19fd46d48f7e3fb00d659deac0347f79cd7cb542f0fc1503c70
  [1000]=0xe20b31294d84c3661ddc8f423abb9c70310d0cf172aa2714ead78029b325e3f4
  [10000]=0xd214e1d84db704ed42d37f538ea9bf71e44ba28bc1cc088b2f5deca654677a56
)

SPEND_ETH="${SPEND_ETH:-0.25}"
CADENCE="${CADENCE:-1000}"

REACTIVE="$(python3 -c "import json;print(json.load(open('$ROOT/deployments/base-sepolia.json'))['reactive']['address'])")"
SYSTEM="0x8888888888888888888888888888888888888888"

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --eth) SPEND_ETH="$2"; shift 2 ;;
    --topic) CADENCE="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

TOPIC="${CRON_TOPICS[$CADENCE]:-}"
if [[ -z "$TOPIC" ]]; then
  echo "unknown cadence '$CADENCE'; known: ${!CRON_TOPICS[*]}" >&2
  exit 2
fi

say "1. buying lREACT with $SPEND_ETH Base Sepolia ETH (100 lREACT per ETH)"
cast balance "$DEPLOYER_ADDR" --rpc-url "$BASE_RPC"
cast send "$REACTIVE_FAUCET_BASE" "request(address)" "$DEPLOYER_ADDR" \
  --value "${SPEND_ETH}ether" --rpc-url "$BASE_RPC" --private-key "$DEPLOYER_KEY" --legacy \
  | grep -E "^(status|transactionHash)"
say "waiting for the lREACT to land on Lasna"
for _ in $(seq 1 24); do
  sleep 5
  LREACT="$(cast balance "$DEPLOYER_ADDR" --rpc-url "$LASNA_RPC")"
  [[ "$LREACT" != "0" ]] && break
done
echo "deployer lREACT: $LREACT"

say "2. funding the enforcer"
cast send "$REACTIVE" "fund()" --value 30ether --rpc-url "$LASNA_RPC" \
  --private-key "$DEPLOYER_KEY" --legacy | grep -E "^(status|transactionHash)"
echo "enforcer balance: $(cast balance "$REACTIVE" --rpc-url "$LASNA_RPC")"

say "3. settling the debt the network is holding against the enforcer"
echo "debt before: $(cast call "$SYSTEM" 'debt(address)(uint256)' "$REACTIVE" --rpc-url "$LASNA_RPC" | head -1)"
cast send "$REACTIVE" "coverDebt()" --rpc-url "$LASNA_RPC" \
  --private-key "$DEPLOYER_KEY" --legacy | grep -E "^(status|transactionHash)"
echo "debt after:  $(cast call "$SYSTEM" 'debt(address)(uint256)' "$REACTIVE" --rpc-url "$LASNA_RPC" | head -1)"

say "4. re-subscribing to the every-$CADENCE-block cron topic"
cast send "$REACTIVE" "setCronTopic(uint256)" "$TOPIC" --rpc-url "$LASNA_RPC" \
  --private-key "$DEPLOYER_KEY" --legacy | grep -E "^(status|transactionHash)"

say "5. the loop is running when this counter moves"
BEFORE="$(cast call "$REACTIVE" 'reactCount()(uint256)' --rpc-url "$LASNA_RPC" | head -1)"
echo "reactCount before: $BEFORE"
for _ in $(seq 1 6); do
  sleep 10
  AFTER="$(cast call "$REACTIVE" 'reactCount()(uint256)' --rpc-url "$LASNA_RPC" | head -1)"
  echo "reactCount now:    $AFTER"
  [[ "$AFTER" != "$BEFORE" ]] && break
done
echo "reserve: $(cast call "$REACTIVE" 'reserveCallsRemaining()(uint256)' --rpc-url "$LASNA_RPC" | head -1) more calls"
echo "balance: $(cast balance "$REACTIVE" --rpc-url "$LASNA_RPC")"
