"""Compare the fee economics of the real Base ETH/USDC pools.

The backtest is only meaningful on a pool where the LP leg actually competes with
lending. This script measures that competition on each candidate pool over the same
window, so the choice of venue is made on numbers rather than on a hunch.

    python scripts/compare_pools.py --hours 12
"""
from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from helm_agent.data import (  # noqa: E402
    POOL_CANDIDATES,
    aggregate_bars,
    decode_swap,
    fetch_swap_logs,
    get_block_number,
    get_block_timestamp,
    resolve_pool,
)
from helm_agent.features import annualise_fee_yield  # noqa: E402

BLOCK_TIME = 0.2
RPC = "https://base-rpc.publicnode.com"


def fetch_pool(pool_address: str, start: int, end: int, bucket: int = 900):
    pool = resolve_pool((pool_address,), url=RPC)
    start_ts = get_block_timestamp(start, RPC)
    end_ts = get_block_timestamp(end, RPC)
    ts_per_block = (end_ts - start_ts) / max(1, end - start)

    rows = []
    for log in fetch_swap_logs(pool.address, start, end, chunk_size=10_000, progress=False):
        block = int(log["blockNumber"], 16)
        price, volume, fees, liquidity, tvl = decode_swap(log, pool)
        rows.append((start_ts + int((block - start) * ts_per_block), price, volume, fees, liquidity, tvl))
    bars = aggregate_bars(rows, bucket_sec=bucket)
    return bars, pool.fee_bps


def measure(address: str, start: int, end: int, bucket: int = 900):
    try:
        bars, fee = fetch_pool(address, start, end, bucket)
    except Exception as exc:  # noqa: BLE001
        return address, None, str(exc)
    if not bars:
        return address, None, "no bars"
    aprs = [annualise_fee_yield(b.fees_usd, b.tvl_usd, bucket / 3600.0) for b in bars if b.tvl_usd > 0]
    if not aprs:
        return address, None, "no tvl"
    aprs.sort()
    n = len(aprs)
    tvls = sorted(b.tvl_usd for b in bars if b.tvl_usd > 0)
    return address, {
        "bars": len(bars),
        "feeBps": fee,
        "medianAprBps": round(aprs[n // 2], 1),
        "p75AprBps": round(aprs[3 * n // 4], 1),
        "p90AprBps": round(aprs[9 * n // 10], 1),
        "maxAprBps": round(aprs[-1], 1),
        "fracAboveLending300": round(sum(1 for a in aprs if a > 300) / n, 3),
        "medianTvl": round(tvls[len(tvls) // 2]),
        "totalVolume": round(sum(b.volume_usd for b in bars)),
    }, ""


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=12)
    parser.add_argument("--bucket", type=int, default=900)
    args = parser.parse_args()

    latest = get_block_number(RPC)
    span = int(args.hours * 3600 / BLOCK_TIME)
    start, end = latest - span, latest
    print(f"window: blocks {start}..{end} ({args.hours}h)", flush=True)

    with ThreadPoolExecutor(max_workers=3) as executor:
        for address, info, error in executor.map(
            lambda a: measure(a, start, end, args.bucket), POOL_CANDIDATES
        ):
            print(f"{address}\n  {info if info else 'FAILED: ' + error}", flush=True)
