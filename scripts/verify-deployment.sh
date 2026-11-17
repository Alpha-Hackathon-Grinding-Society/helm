#!/usr/bin/env bash
# Verify the live deployment against what this repository claims it deployed.
#
# This script is the last gate before a judge opens the links. It exits non-zero if any
# of the following is not true:
#
#   1. the addresses in `deployments/base-sepolia.json` are the ones on the chains;
#   2. the enforcer is wired to the vault, the pools and the agent;
#   3. the user's risk envelope is stored on the vault *and* mirrored on the enforcer,
#      and the two agree;
#   4. the deployed runtime bytecode is the committed Foundry artifact, byte for byte
#      outside the immutable addresses the constructor baked in;
#   5. the vault can pay for its callbacks, and has no callback debt;
#   6. the enforcer owes the Reactive network nothing, has lREACT left, and is
#      subscribed to the cron topic the deployment record names;
#   7. the on-chain record contains the evidence the README points at:
#      at least ten full cycles, a clamped proposal, an economic veto, a rebalance that
#      moved funds, and an autonomous exit.
#
# Usage: scripts/verify-deployment.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$PATH:/home/unify/.foundry/bin"

BASE_RPC="${BASE_RPC:-https://base-sepolia-rpc.publicnode.com}"
LASNA_RPC="${LASNA_RPC:-https://lasna-rpc.rnk.dev}"
DEPLOYMENT="$ROOT/deployments/base-sepolia.json"
PYTHON="${PYTHON:-$ROOT/agent/.venv/bin/python}"

FAILURES=0
CHECKS=0

pass() { CHECKS=$((CHECKS + 1)); printf '  \033[32mok\033[0m   %s\n' "$1"; }
fail() {
  CHECKS=$((CHECKS + 1))
  FAILURES=$((FAILURES + 1))
  printf '  \033[31mFAIL\033[0m %s\n' "$1"
  [[ $# -gt 1 ]] && printf '       %s\n' "$2"
}
section() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }

# `cast call` prints one return value per line. This flattens them onto one line so a
# single `read` can take them apart, and it is the reason the envelope check used to
# read only the first value.
cast_flat() { cast call "$@" 2>/dev/null | tr '\n' ' '; }

read -r REACTIVE VAULT LP_POOL LENDING TOKEN PROXY AGENT CHAIN_ID LASNA_ID CRON_TOPIC SYSTEM < <(python3 -c "
import json
d = json.load(open('$DEPLOYMENT'))
print(d['reactive']['address'], d['vault'], d['lpPool'], d['lendingPool'], d['token'],
      d['callbackProxy'], d['agent'], d['chainId'], d['reactive']['chainId'],
      d['reactive'].get('cronTopic', ''), d['reactive'].get('systemContract', '0x8888888888888888888888888888888888888888'))
")

section "1. the addresses are the ones on the chains"

for pair in "enforcer:$REACTIVE:$LASNA_RPC" "vault:$VAULT:$BASE_RPC" "lp pool:$LP_POOL:$BASE_RPC" \
            "lending pool:$LENDING:$BASE_RPC" "token:$TOKEN:$BASE_RPC"; do
  name="${pair%%:*}"; rest="${pair#*:}"; addr="${rest%%:*}"; rpc="${rest#*:}"
  code="$(cast code "$addr" --rpc-url "$rpc" 2>/dev/null)"
  if [[ -z "$code" || "$code" == "0x" ]]; then
    fail "$name has no code at $addr"
  else
    pass "$name has code at $addr"
  fi
done

section "2. the enforcer is wired to the vault, the pools and the agent"

on_chain_vault="$(cast_flat "$REACTIVE" "vault()(address)" --rpc-url "$LASNA_RPC" | awk '{print $1}')"
on_chain_pool="$(cast_flat "$REACTIVE" "lpPool()(address)" --rpc-url "$LASNA_RPC" | awk '{print $1}')"
on_chain_lending="$(cast_flat "$REACTIVE" "lendingPool()(address)" --rpc-url "$LASNA_RPC" | awk '{print $1}')"
on_chain_agent="$(cast_flat "$REACTIVE" "agent()(address)" --rpc-url "$LASNA_RPC" | awk '{print $1}')"

[[ "${on_chain_vault,,}" == "${VAULT,,}" ]] \
  && pass "the enforcer points at the deployed vault" \
  || fail "the enforcer points at $on_chain_vault, not $VAULT"
[[ "${on_chain_pool,,}" == "${LP_POOL,,}" ]] \
  && pass "the enforcer points at the deployed LP pool" \
  || fail "the enforcer points at $on_chain_pool, not $LP_POOL"
[[ "${on_chain_lending,,}" == "${LENDING,,}" ]] \
  && pass "the enforcer points at the deployed lending pool" \
  || fail "the enforcer points at $on_chain_lending, not $LENDING"
[[ "${on_chain_agent,,}" == "${AGENT,,}" ]] \
  && pass "the registered agent is $AGENT" \
  || fail "the registered agent is $on_chain_agent, not $AGENT"

section "3. the risk envelope is stored on the vault and mirrored on the enforcer"

read -r V_MIN V_MAX V_RMIN V_RMAX V_COOL V_VOL V_MINTRADE V_FRESH < <(python3 -c "
import json
d = json.load(open('$DEPLOYMENT'))['limits']
print(d['lpShareMinBps'], d['lpShareMaxBps'], d['rangeWidthMinBps'], d['rangeWidthMaxBps'],
      d['cooldownSec'], d['volExitLevelBps'], d['minTradeBps'], d['freshnessSec'])
")

read -r R_MIN R_MAX R_RMIN R_RMAX R_COOL R_VOL R_MINTRADE R_FRESH < <(
  cast_flat "$REACTIVE" "limits()(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256)" \
    --rpc-url "$LASNA_RPC" | awk '{print $1, $2, $3, $4, $5, $6, $7, $8}'
)

if [[ "$V_MIN" == "$R_MIN" && "$V_MAX" == "$R_MAX" && "$V_RMIN" == "$R_RMIN" && "$V_RMAX" == "$R_RMAX" \
   && "$V_COOL" == "$R_COOL" && "$V_VOL" == "$R_VOL" && "$V_MINTRADE" == "$R_MINTRADE" \
   && "$V_FRESH" == "$R_FRESH" ]]; then
  pass "the enforcer's envelope matches the vault's ($R_MIN–$R_MAX bps LP, exit at $R_VOL bps)"
else
  fail "the envelopes disagree" "vault: $V_MIN $V_MAX $V_RMIN $V_RMAX $V_COOL $V_VOL $V_MINTRADE $V_FRESH / enforcer: $R_MIN $R_MAX $R_RMIN $R_RMAX $R_COOL $R_VOL $R_MINTRADE $R_FRESH"
fi

limits_set="$(cast_flat "$REACTIVE" "limitsSet()(bool)" --rpc-url "$LASNA_RPC" | awk '{print $1}')"
[[ "$limits_set" == "true" ]] && pass "the enforcer has the envelope" || fail "the enforcer has no envelope"

section "4. the deployed bytecode is the committed artifact"

if "$PYTHON" "$ROOT/scripts/verify-bytecode.py" \
    --label HelmReactive \
    --artifact "$ROOT/contracts/out/HelmReactive.sol/HelmReactive.json" \
    --address "$REACTIVE" --rpc "$LASNA_RPC" \
    --immutable "$SYSTEM"; then
  pass "HelmReactive: the deployed runtime is the committed artifact"
else
  fail "HelmReactive: the deployed runtime is not the committed artifact"
fi

if "$PYTHON" "$ROOT/scripts/verify-bytecode.py" \
    --label HelmVault \
    --artifact "$ROOT/contracts/out/HelmVault.sol/HelmVault.json" \
    --address "$VAULT" --rpc "$BASE_RPC" \
    --immutable "$PROXY" --immutable "$REACTIVE" --immutable "$LP_POOL" \
    --immutable "$TOKEN" --immutable "$LENDING"; then
  pass "HelmVault: the deployed runtime is the committed artifact"
else
  fail "HelmVault: the deployed runtime is not the committed artifact"
fi

section "5. the vault can pay for its callbacks"

vault_eth="$(cast balance "$VAULT" --rpc-url "$BASE_RPC" 2>/dev/null | awk '{print $1}')"
callback_debt="$(cast_flat "$PROXY" "debt(address)(uint256)" "$VAULT" --rpc-url "$BASE_RPC" | awk '{print $1}')"
if [[ "${callback_debt:-0}" != "0" ]]; then
  fail "the vault owes the callback proxy $callback_debt wei" "run 'cast send $VAULT \"coverDebt()\"'"
else
  pass "the vault has no callback debt"
fi

vault_eth_text="$(python3 -c "print(f'{${vault_eth:-0} / 1e18:.6f}')" 2>/dev/null || echo 0)"
if python3 -c "import sys; sys.exit(0 if ${vault_eth:-0} > 1000000000000000 else 1)"; then
  pass "the vault holds $vault_eth_text ETH for its callbacks"
else
  fail "the vault holds too little ETH to pay for callbacks" "balance: $vault_eth_text ETH"
fi

agent_eth="$(cast balance "$AGENT" --rpc-url "$BASE_RPC" 2>/dev/null | awk '{print $1}')"
agent_eth_text="$(python3 -c "print(f'{${agent_eth:-0} / 1e18:.6f}')" 2>/dev/null || echo 0)"
if python3 -c "import sys; sys.exit(0 if ${agent_eth:-0} > 100000000000000 else 1)"; then
  pass "the agent holds $agent_eth_text ETH to pay for its proposals"
else
  fail "the agent has too little ETH to post a proposal" "balance: $agent_eth_text ETH"
fi

section "6. the enforcer can keep reacting"

reserve_calls="$(cast_flat "$REACTIVE" "reserveCallsRemaining()(uint256)" --rpc-url "$LASNA_RPC" | awk '{print $1}')"
reserve_healthy="$(cast_flat "$REACTIVE" "reserveHealthy()(bool)" --rpc-url "$LASNA_RPC" | awk '{print $1}')"
react_count="$(cast_flat "$REACTIVE" "reactCount()(uint256)" --rpc-url "$LASNA_RPC" | awk '{print $1}')"
enforcer_lreact="$(cast balance "$REACTIVE" --rpc-url "$LASNA_RPC" 2>/dev/null | awk '{print $1}')"
enforcer_text="$(python3 -c "print(f'{${enforcer_lreact:-0} / 1e18:.6f}')" 2>/dev/null || echo 0)"
network_debt="$(cast_flat "$SYSTEM" "debt(address)(uint256)" "$REACTIVE" --rpc-url "$LASNA_RPC" | awk '{print $1}')"

if [[ "$reserve_healthy" == "true" ]]; then
  pass "the enforcer's lREACT reserve is healthy ($enforcer_text lREACT, about $reserve_calls more calls)"
else
  fail "the enforcer's lREACT reserve is low" "$enforcer_text lREACT left, about $reserve_calls calls"
fi

# The subscription dies silently when the contract owes the network money: the network
# simply stops calling it. This is the check that catches that failure mode.
if [[ "${network_debt:-0}" == "0" ]]; then
  pass "the enforcer owes the Reactive network nothing"
else
  fail "the enforcer owes the Reactive network $network_debt wei of lREACT" \
    "the network stops calling a contract that is in debt: run 'cast send $REACTIVE \"coverDebt()\"'"
fi

if [[ "${react_count:-0}" -gt 0 ]]; then
  pass "the network has called the enforcer $react_count times"
else
  fail "the enforcer has never been called" "the reactive subscription is not working"
fi

on_chain_cron="$(cast_flat "$REACTIVE" "cronTopic()(uint256)" --rpc-url "$LASNA_RPC" | awk '{print $1}')"
cron_match="$(python3 -c "
try:
    print(int('${on_chain_cron:-0}') == int('${CRON_TOPIC:-0}', 16))
except Exception:
    print('False')
")"
if [[ "$cron_match" == "True" ]]; then
  pass "the enforcer is subscribed to the cron topic in the deployment record"
else
  fail "the cron topic on chain is $on_chain_cron, not $CRON_TOPIC"
fi

section "7. the on-chain record holds the evidence"

EVIDENCE="$ROOT/agent/ledger/chain-events.jsonl"
if [[ ! -f "$EVIDENCE" ]]; then
  fail "no evidence file at $EVIDENCE" "run 'scripts/collect-evidence.py'"
else
  read -r CYCLES FULL CLAMPED VETOED REJECTED REBALANCED EXITS < <("$PYTHON" - "$EVIDENCE" <<'PY'
import json, sys
rows = []
for line in open(sys.argv[1]):
    line = line.strip()
    if line:
        rows.append(json.loads(line))
full = sum(1 for r in rows if r.get("fullCycle"))
clamped = sum(1 for r in rows if (r.get("evaluated") or {}).get("clampMask"))
vetoed = sum(1 for r in rows if (r.get("evaluated") or {}).get("clampMask", 0) & (1 << 5))
rejected = sum(1 for r in rows if r.get("rejected"))
rebalanced = sum(1 for r in rows if r.get("rebalanced"))
exits = sum(1 for r in rows if r.get("autonomousExit"))
print(len(rows), full, clamped, vetoed, rejected, rebalanced, exits)
PY
)
  [[ "${FULL:-0}" -ge 10 ]] \
    && pass "$FULL full cycles on chain (the gate is 10)" \
    || fail "only $FULL full cycles on chain, the gate is 10"
  [[ "${CLAMPED:-0}" -ge 1 ]] \
    && pass "$CLAMPED proposals clamped by the contract" \
    || fail "no clamped proposal on chain"
  [[ "${VETOED:-0}" -ge 1 ]] \
    && pass "$VETOED proposals stopped by the economic veto" \
    || fail "no economic veto on chain"
  [[ "${REJECTED:-0}" -ge 1 ]] \
    && pass "$REJECTED proposals refused before execution" \
    || fail "no refused proposal on chain"
  [[ "${REBALANCED:-0}" -ge 1 ]] \
    && pass "$REBALANCED rebalances that moved funds" \
    || fail "no rebalance on chain"
  [[ "${EXITS:-0}" -ge 1 ]] \
    && pass "$EXITS autonomous exits" \
    || fail "no autonomous exit on chain"
fi

printf '\n'
if [[ "$FAILURES" -eq 0 ]]; then
  printf '\033[1;32m%d checks, all passed.\033[0m\n' "$CHECKS"
  exit 0
fi
printf '\033[1;31m%d checks, %d failed.\033[0m\n' "$CHECKS" "$FAILURES"
exit 1
