#!/usr/bin/env bash
# Set the vault's risk envelope on Base Sepolia and record it in the deployment file.
#
#   scripts/set-limits.sh [lpMin lpMax rangeMin rangeMax cooldown volExit minTrade freshness]
#
# The envelope is the user's side of the contract: it is what the model is not allowed to
# exceed. The script reads deployments/base-sepolia.json, writes the limits on chain with
# the owner's key, waits for the receipt, reads the limits back and then records them in
# the deployment file so the dashboard and the repository agree with the chain.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$PATH:/home/unify/.foundry/bin"

BASE_RPC="${BASE_RPC:-https://base-sepolia-rpc.publicnode.com}"
KEYS="$ROOT/deploy-keys/addresses.txt"
DEPLOYER_KEY="$(grep '^DEPLOYER_PRIVATE_KEY=' "$KEYS" | cut -d= -f2)"

LP_MIN="${1:-0}"
LP_MAX="${2:-4000}"
RANGE_MIN="${3:-500}"
RANGE_MAX="${4:-4000}"
COOLDOWN="${5:-20}"
VOL_EXIT="${6:-1200}"
MIN_TRADE="${7:-200}"
FRESHNESS="${8:-600}"

VAULT="$(python3 -c "import json;print(json.load(open('$ROOT/deployments/base-sepolia.json'))['vault'])")"

printf '\n\033[1m==> setting the envelope on %s\033[0m\n' "$VAULT"
cast send "$VAULT" \
  "setLimits(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256)" \
  "$LP_MIN" "$LP_MAX" "$RANGE_MIN" "$RANGE_MAX" "$COOLDOWN" "$VOL_EXIT" "$MIN_TRADE" "$FRESHNESS" \
  --rpc-url "$BASE_RPC" --private-key "$DEPLOYER_KEY" --legacy

printf '\n\033[1m==> reading the envelope back from the chain\033[0m\n'
LIMITS="$(cast call "$VAULT" "limits()(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256)" --rpc-url "$BASE_RPC")"
printf '%s\n' "$LIMITS"

python3 - "$ROOT" "$LIMITS" <<'PY'
import json, re, sys
from pathlib import Path

root = Path(sys.argv[1])
raw = sys.argv[2]
values = [int(v) for v in re.findall(r"\d+", raw)][-8:]
keys = [
    "lpShareMinBps",
    "lpShareMaxBps",
    "rangeWidthMinBps",
    "rangeWidthMaxBps",
    "cooldownSec",
    "volExitLevelBps",
    "minTradeBps",
    "freshnessSec",
]
path = root / "deployments" / "base-sepolia.json"
record = json.loads(path.read_text())
record["limits"] = dict(zip(keys, values))
path.write_text(json.dumps(record, indent=2) + "\n")
print("\ndeployment record updated:", json.dumps(record["limits"]))
PY
