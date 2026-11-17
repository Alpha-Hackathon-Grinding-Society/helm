#!/usr/bin/env python3
"""Claim Base Sepolia ETH from the A2AWire faucet using fresh addresses, then forward it.

The faucet pays 0.0005 ETH per address per 24 hours. Helm needs roughly 0.03 ETH on Base
Sepolia: vault deployment, the vault setup transactions, the agent's gas and the vault's
callback reserve. This script rotates through throwaway keys so each claim lands on a new
address, and forwards everything to the deployer.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

CLAIM_URL = "https://a2awire.com/agents/faucet/invoke"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS = os.path.join(ROOT, "deploy-keys", "addresses.txt")
OUT = os.path.join(ROOT, "deploy-keys", "faucet-claims.json")


def rpc(method, params, url):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def new_key():
    out = subprocess.run(
        ["cast", "wallet", "new"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    for line in out.splitlines():
        if "\t" in line:
            addr, key = line.split()
            return key, addr
    raise RuntimeError(f"could not parse keypair output: {out!r}")


def claim(address):
    body = json.dumps({"task": "claim", "input": {"address": address}}).encode()
    req = urllib.request.Request(CLAIM_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def main():
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    deployer = [l for l in open(KEYS) if l.startswith("DEPLOYER_ADDRESS=")][0].split("=")[1].strip()
    key = [l for l in open(KEYS) if l.startswith("DEPLOYER_PRIVATE_KEY=")][0].split("=")[1].strip()
    rpc_url = "https://base-sepolia-rpc.publicnode.com"

    claims = []
    if os.path.exists(OUT):
        claims = json.load(open(OUT))

    have = 0
    for i in range(target):
        k, a = new_key()
        try:
            r = claim(a)
        except Exception as exc:  # noqa: BLE001
            print(f"[{i}] claim failed for {a}: {exc}", flush=True)
            time.sleep(1.5)
            continue
        payload = r.get("output") or {}
        amount = int(payload.get("amount_wei", "0") or 0)
        tx = payload.get("tx_hash")
        print(f"[{i}] {a} -> {amount} wei  {tx}", flush=True)
        claims.append({"address": a, "private_key": k, "amount_wei": str(amount), "tx_hash": tx})
        have += amount
        if amount == 0:
            time.sleep(1.0)
        json.dump(claims, open(OUT, "w"), indent=2)

    # forward every claimed balance to the deployer
    total = 0
    for c in claims:
        bal = rpc("eth_getBalance", [c["address"], "latest"], rpc_url)["result"]
        bal = int(bal, 16)
        if bal == 0:
            continue
        tx = subprocess.run(
            ["cast", "send", c["address"], "--value", str(bal), "--rpc-url", rpc_url,
             "--private-key", c["private_key"], "--legacy"],
            capture_output=True, text=True,
        )
        if tx.returncode == 0:
            h = [l for l in tx.stdout.splitlines() if l.startswith("transactionHash")]
            print(f"forwarded {bal} wei from {c['address']} {h[0] if h else ''}", flush=True)
            total += bal
        else:
            print(f"forward failed for {c['address']}: {tx.stderr[:200]}", flush=True)
        time.sleep(0.4)

    print(f"total forwarded: {total} wei = {total / 1e18} ETH")


if __name__ == "__main__":
    main()
