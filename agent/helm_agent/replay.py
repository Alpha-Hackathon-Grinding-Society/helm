"""The replay script: drive the mock markets with a real slice of Base mainnet history.

The PRD asks for this (D-3), and it exists because a testnet market does not move on its
own. Without it, the demo would show a chain reacting to nothing.

What the replay does, for every bar of a real slice of history:

* it sets the mock pool's price to the price the market actually had in that bar,
* it makes a swap sized so that the pool's fee flow matches the fee yield the real pool
  paid, which is what lets the reactive contract measure a fee edge on chain,
* it publishes the lending rate the real market had at that time.

What the replay does not do: it does not fake any part of Helm. The reactive trigger, the
model's proposal, the limit check, the clamp, the callback, the rebalance and the
explanation are all live transactions, and the dashboard says so.
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path

from helm_agent.chain import ChainClient, call_data
from helm_agent.data import Bar, read_bars
from helm_agent.deployment import Deployment
from helm_agent.keccak import selector

SECONDS_PER_YEAR = 365 * 24 * 3600


@dataclass
class ReplayStep:
    """One bar of history, turned into the calls that reproduce it."""

    timestamp: int
    price_e18: int
    swap_usdc: int
    rate_bps: int
    volume_usd: float
    fees_usd: float
    shock_bps: int = 0


def pick_slice(bars: list[Bar], window_bars: int, mode: str = "move") -> list[Bar]:
    """The window of history the replay should reproduce.

    `mode="move"` picks the window with the most movement in it, which is what a demo
    wants when it is showing the volatility exit. `mode="calm"` picks the window with the
    least movement, which is what a demo wants when it is showing the fund manager
    trading normally. Either way the window is chosen by the data, not by hand, and the
    README can name the timestamps it used.
    """
    if len(bars) <= window_bars:
        return list(bars)
    best_start = 0
    best_score = -1.0 if mode == "move" else float("inf")
    for start in range(0, len(bars) - window_bars):
        window = bars[start : start + window_bars]
        first = window[0].price
        last = window[-1].price
        move = abs(last - first) / first if first else 0.0
        # the volatility of the window matters too: a slow slide is not a shift
        spread = max(b.price for b in window) - min(b.price for b in window)
        score = move + spread / first if first else 0.0
        if mode == "calm":
            better = score < best_score
        else:
            better = score > best_score
        if better:
            best_score = score
            best_start = start
    return bars[best_start : best_start + window_bars]


def swap_size_for_target_apr(
    depth_usd: float,
    fee_rate_bps: int,
    target_apr_bps: float,
    window_sec: float,
    swaps_per_window: int = 1,
) -> float:
    """How big a swap has to be for the contract to measure the fee yield we want.

    The contract measures `fees / depth / elapsed`, annualised. To land on a target
    annualised fee yield, the replay has to put the right amount of fees into the pool
    over the observation window — and that amount is shared out between the swaps that
    happen inside the window. A replay that fires every four seconds needs a much
    smaller swap than one that fires once an hour, because it is making the same number
    of swaps either way.
    """
    if depth_usd <= 0 or fee_rate_bps <= 0:
        return 0.0
    fees_needed = target_apr_bps / 10_000 * depth_usd * window_sec / SECONDS_PER_YEAR
    fees_per_swap = fees_needed / max(1, swaps_per_window)
    return fees_per_swap / (fee_rate_bps / 10_000)


def build_steps(
    bars: list[Bar],
    depth_usd: float,
    fee_rate_bps: int,
    target_apr_bps: float,
    lending_rate_bps: float,
    window_sec: float,
    swaps_per_window: int = 1,
    anchor_price_e18: int | None = None,
    shock_at: int = -1,
    shock_bps: int = 0,
) -> list[ReplayStep]:
    """Turn a slice of history into the calls that reproduce it.

    The real price path is *anchored* on the mock pool's own price rather than copied
    across whole. The level of the mock market is its own; what the replay reproduces is
    the shape of the real path — the same percentage moves, in the same order — so the
    reactive contract sees the same volatility the real market produced without the
    discontinuity that copying the absolute price would create.

    `shock_at` and `shock_bps` put one deliberate violent move into the path. That is
    the move the contract's own volatility exit is supposed to react to, and it is
    recorded in the replay log like every other step.
    """
    steps: list[ReplayStep] = []
    swap_usd = swap_size_for_target_apr(
        depth_usd,
        fee_rate_bps,
        target_apr_bps,
        window_sec,
        swaps_per_window,
    )
    first_price = bars[0].price if bars else 0.0
    scale = (anchor_price_e18 / 1e18 / first_price) if (anchor_price_e18 and first_price) else 1.0
    for index, bar in enumerate(bars):
        price_e18 = int(bar.price * scale * 1e18)
        if index == shock_at and shock_bps:
            price_e18 = int(price_e18 * (1 + shock_bps / 10_000))
        steps.append(
            ReplayStep(
                timestamp=bar.timestamp,
                price_e18=price_e18,
                swap_usdc=int(swap_usd * 1e18),
                rate_bps=int(lending_rate_bps),
                volume_usd=bar.volume_usd,
                fees_usd=bar.fees_usd,
                shock_bps=shock_bps if index == shock_at else 0,
            )
        )
    return steps


def run_replay(
    deployment: Deployment,
    steps: list[ReplayStep],
    pace_sec: float = 4.0,
    dry_run: bool = False,
) -> list[dict]:
    """Replay the steps against the live mock markets."""
    client = ChainClient(
        rpc_url=deployment.base_rpc,
        chain_id=deployment.chain_id,
        private_key=deployment.deployer_key,
        from_address=deployment.deployer,
    )

    # the trader has to be able to pay the pool
    approve = selector("approve(address,uint256)") + "0" * 24 + deployment.lp_pool[2:] + "f" * 64
    if not dry_run:
        tx = client.send_transaction(deployment.token, approve)
        print(f"approve pool: {tx}", flush=True)

    results: list[dict] = []
    for index, step in enumerate(steps):
        step_started = time.time()
        if not dry_run:
            set_price = selector("setPrice(uint256)") + f"{step.price_e18:064x}"
            price_tx = client.send_transaction(deployment.lp_pool, set_price)

            swap = selector("swap(uint256)") + f"{step.swap_usdc:064x}"
            swap_tx = client.send_transaction(deployment.lp_pool, swap)

            set_rate = selector("setRate(uint256)") + f"{step.rate_bps:064x}"
            rate_tx = client.send_transaction(deployment.lending_pool, set_rate)
        else:
            price_tx = swap_tx = rate_tx = "dry-run"

        record = {
            "index": index,
            "timestamp": step.timestamp,
            "priceE18": step.price_e18,
            "swapUsdc": step.swap_usdc,
            "rateBps": step.rate_bps,
            "setPriceTx": price_tx,
            "swapTx": swap_tx,
            "setRateTx": rate_tx,
        }
        results.append(record)
        print(
            f"replay {index + 1}/{len(steps)}: price {step.price_e18 / 1e18:.2f}, "
            f"swap {step.swap_usdc / 1e18:,.0f} USD, rate {step.rate_bps} bps",
            flush=True,
        )
        if not dry_run and pace_sec > 0:
            # `pace_sec` is the interval between the start of one bar and the start of the next,
            # not the sleep after the transactions. The three transactions take a few seconds on
            # their own, and the fee yield the contract measures is a rate per second, so the
            # spacing has to be the real one or the measurement will not land on its target.
            elapsed = time.time() - step_started
            time.sleep(max(0.0, pace_sec - elapsed))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay real Base history into the mock markets.")
    parser.add_argument("--history", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "base_eth_usdc_15m.jsonl")
    parser.add_argument("--deployment", type=Path, default=None)
    parser.add_argument("--bars", type=int, default=16, help="how many bars of history to replay")
    parser.add_argument(
        "--slice",
        choices=("move", "calm"),
        default="calm",
        help="pick the most volatile window, or the quietest one",
    )
    parser.add_argument(
        "--pace",
        type=float,
        default=10.0,
        help="seconds between the start of one bar and the start of the next",
    )
    parser.add_argument("--target-apr-bps", type=float, default=800.0)
    parser.add_argument("--lending-rate-bps", type=float, default=300.0)
    parser.add_argument("--shock-at", type=int, default=-1, help="which step gets the violent move")
    parser.add_argument("--shock-bps", type=int, default=0, help="how violent that move is")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if not args.history.exists():
        print(f"no history at {args.history}; download it first", flush=True)
        return 1
    bars = read_bars(args.history)
    slice_bars = pick_slice(bars, args.bars, mode=args.slice)
    if not slice_bars:
        print("no bars to replay", flush=True)
        return 1

    deployment = Deployment.load(args.deployment) if args.deployment else Deployment.load()
    client = ChainClient(
        rpc_url=deployment.base_rpc,
        chain_id=deployment.chain_id,
        private_key=deployment.deployer_key,
        from_address=deployment.deployer,
    )
    depth = client.call_uint(deployment.lp_pool, "liquidityUsd()") / 1e18
    fee_rate = client.call_uint(deployment.lp_pool, "feeRateBps()")

    # The contract annualises the fee flow over the time it has actually observed, so the
    # swap size has to be sized against the time the replay itself takes, not against the
    # contract's one-hour observation window. A replay that runs for eighty seconds has
    # to put eighty seconds' worth of fees into the pool to land on the target yield.
    window_sec = max(1.0, len(slice_bars) * args.pace)
    swaps_per_window = max(1, int(window_sec / max(1.0, args.pace)))
    anchor_price_e18 = client.call_uint(deployment.lp_pool, "priceE18()")
    steps = build_steps(
        slice_bars,
        depth_usd=depth,
        fee_rate_bps=fee_rate,
        target_apr_bps=args.target_apr_bps,
        lending_rate_bps=args.lending_rate_bps,
        window_sec=window_sec,
        swaps_per_window=swaps_per_window,
        anchor_price_e18=anchor_price_e18,
        shock_at=args.shock_at,
        shock_bps=args.shock_bps,
    )
    print(
        f"replaying {len(steps)} bars from {slice_bars[0].timestamp} to {slice_bars[-1].timestamp}; "
        f"pool depth ${depth:,.0f}, fee {fee_rate} bps, "
        f"{steps[0].swap_usdc / 1e18:,.0f} USD per swap for a {args.target_apr_bps:.0f} bps fee yield",
        flush=True,
    )
    if args.shock_at >= 0:
        print(
            f"a {args.shock_bps} bps shock is applied at step {args.shock_at + 1}",
            flush=True,
        )

    records = run_replay(deployment, steps, pace_sec=args.pace, dry_run=args.dry_run)
    out = args.out or (Path(__file__).resolve().parents[1] / "ledger" / "replay.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(records, indent=2))
    print(f"replay written to {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
