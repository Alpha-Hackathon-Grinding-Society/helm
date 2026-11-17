#!/usr/bin/env python3
"""Forward Base Sepolia ETH from the throwaway faucet addresses to the deployer.

Each faucet address holds exactly 0.0005 ETH, which is not enough to send the whole balance
and pay for the transaction at the same time. This leaves a small gas buffer behind.
"""
import json
import os
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS = os.path.join(ROOT, "deploy-keys", "addresses.txt")
OUT = os.path.join(ROOT, "deploy-keys", "faucet-claims.json")
RPC = "https://base-sepolia-rpc.publicnode.com"
GAS_BUFFER = 250_000_000_000  # 2.5e11 wei, comfortably above the ~1.3e11 wei a Base Sepolia send costs


def main():
    deployer = [l for l in open(KEYS) if l.startswith("DEPLOYER_ADDRESS=")][0].split("=")[1].strip()
    key = [l for l in open(KEYS) if l.startswith("DEPLOYER_PRIVATE_KEY=")][0].split("=")[1].strip()
    claims = json.load(open(OUT))

    total = 0
    sent = 0
    for c in claims:
        r = subprocess.run(
            ["cast", "balance", c["address"], "--rpc-url", RPC],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            continue
        bal = int(r.stdout.strip().split()[0])
        if bal <= GAS_BUFFER:
            continue
        value = bal - GAS_BUFFER
        tx = subprocess.run(
            ["cast", "send", deployer, "--value", str(value), "--rpc-url", RPC,
             "--private-key", c["private_key"], "--legacy"],
            capture_output=True, text=True,
        )
        if tx.returncode == 0:
            h = [l.split()[-1] for l in tx.stdout.splitlines() if l.startswith("transactionHash")]
            total += value
            sent += 1
            if sent <= 3:
                print(f"forwarded {value} wei from {c['address']} {h[0] if h else ''}", flush=True)
        else:
            print(f"forward failed {c['address']}: {tx.stderr[:160]}", flush=True)
        time.sleep(0.25)

    print(f"forwarded from {sent} addresses, total {total} wei = {total / 1e18} ETH")


if __name__ == "__main__":
    main()
