#!/usr/bin/env python3
"""Collect the on-chain evidence of Helm's loop and write it down.

The README and the submission need a table of cycles, and every row of that table has to
be a transaction that a judge can open in a block explorer and read. This script builds it
from the two chains themselves:

  * **Reactive Lasna** (5318007) holds the enforcer. Its events say when a cycle opened,
    what the model proposed, what the contract allowed, and whether the contract pulled the
    position out on its own.
  * **Base Sepolia** (84532) holds the vault. Its events say when the vault was asked, when
    the agent posted, and whether funds actually moved.

The two chains are joined by `cycleId`, which is the same number in both: the enforcer
opens the cycle, the vault is asked about that cycle, and the vault is told what to do with
that cycle. Every row therefore carries up to five transaction hashes across two chains.

Nothing here is typed by hand. The script reads the chains, writes the JSON, and writes
the markdown from the same data, so the two can never disagree.

Usage:
    scripts/collect-evidence.py [--deployment deployments/base-sepolia.json]
                                [--out agent/ledger/chain-events.jsonl]
                                [--markdown docs/EVIDENCE.md]
                                [--lasna-blocks 60000]
                                [--base-blocks 250000]

The two lookbacks are different because the two chains have different block times: Lasna
blocks are a second apart, Base Sepolia's are about two hundred milliseconds apart, so the
same window of wall-clock time is a lot more blocks on the second chain.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))

from helm_agent.chain import (  # noqa: E402
    AUTONOMOUS_EXIT_TOPIC,
    CYCLE_EXPIRED_TOPIC,
    CYCLE_OPENED_TOPIC,
    ChainClient,
    DECISION_REQUESTED_TOPIC,
    FORECAST_GRADED_TOPIC,
    NO_TRADE_TOPIC,
    PROPOSAL_EVALUATED_TOPIC,
    PROPOSAL_POSTED_TOPIC,
    PROPOSAL_REJECTED_TOPIC,
    REBALANCE_REQUESTED_TOPIC,
    REBALANCED_TOPIC,
    decode_address_at,
    decode_uints,
)

# The clamp bits, in the order `HelmTypes.sol` defines them.
CLAMP_NAMES = [
    (1 << 0, "LP_ABOVE_MAX"),
    (1 << 1, "LP_BELOW_MIN"),
    (1 << 2, "RANGE_ABOVE_MAX"),
    (1 << 3, "RANGE_BELOW_MIN"),
    (1 << 4, "VOLATILITY_EXIT"),
    (1 << 5, "ECONOMIC_VETO"),
    (1 << 6, "NO_TRADE"),
]

# The reject flags, in the order `HelmReject` defines them.
REJECT_NAMES = [
    (1 << 0, "UNKNOWN_AGENT"),
    (1 << 1, "CYCLE_MISMATCH"),
    (1 << 2, "STALE"),
    (1 << 3, "NO_LIMITS"),
    (1 << 4, "PAUSED"),
    (1 << 5, "REPLAY"),
    (1 << 6, "BAD_INPUT"),
]


def decode_flags(value: int, names: list[tuple[int, str]]) -> list[str]:
    """The names of every flag set in `value`."""
    return [name for bit, name in names if value & bit]


def load_deployment(path: Path) -> dict:
    return json.loads(path.read_text())


def collect(client: ChainClient, address: str, topics: list[str], from_block: int, to_block: int):
    """Every log of a contract for a set of topics, as raw log objects.

    The filter is one position holding several alternatives, so it reads as "topic 0 is any
    of these". A list of one-element lists would be read as "topic 0 is the first *and*
    topic 1 is the second", which matches nothing.
    """
    return client.get_logs(address, [topics], from_block, to_block)


def build_cycles(
    deployment: dict,
    lasna: ChainClient,
    base: ChainClient,
    lasna_blocks: int,
    base_blocks: int,
) -> list[dict]:
    """Read both chains and join their events into one record per cycle."""
    reactive_address = deployment["reactive"]["address"]
    vault_address = deployment["vault"]

    lasna_head = lasna.block_number()
    base_head = base.block_number()
    lasna_from = max(0, lasna_head - lasna_blocks)
    base_from = max(0, base_head - base_blocks)

    lasna_logs = collect(
        lasna,
        reactive_address,
        [
            CYCLE_OPENED_TOPIC,
            CYCLE_EXPIRED_TOPIC,
            PROPOSAL_EVALUATED_TOPIC,
            PROPOSAL_REJECTED_TOPIC,
            NO_TRADE_TOPIC,
            REBALANCE_REQUESTED_TOPIC,
            AUTONOMOUS_EXIT_TOPIC,
            FORECAST_GRADED_TOPIC,
        ],
        lasna_from,
        lasna_head,
    )
    base_logs = collect(
        base,
        vault_address,
        [DECISION_REQUESTED_TOPIC, PROPOSAL_POSTED_TOPIC, REBALANCED_TOPIC],
        base_from,
        base_head,
    )

    cycles: dict[int, dict] = {}

    def slot(cycle_id: int) -> dict:
        return cycles.setdefault(
            cycle_id,
            {
                "cycleId": cycle_id,
                "opened": None,
                "expired": None,
                "requested": None,
                "posted": None,
                "evaluated": None,
                "rejected": None,
                "noTrade": None,
                "rebalanceRequested": None,
                "rebalanced": None,
                "forecastGraded": None,
                "autonomousExit": None,
            },
        )

    for log in lasna_logs:
        topic = log.topics[0]
        cycle_id = int(log.topics[1], 16)
        record = slot(cycle_id)
        if topic == CYCLE_OPENED_TOPIC:
            values = decode_uints(log.data, 4)
            record["opened"] = {
                "priceE18": values[0],
                "rateBps": values[1],
                "volBps": values[2],
                "openedAt": values[3],
                "blockNumber": log.block_number,
                "txHash": log.transaction_hash,
            }
        elif topic == CYCLE_EXPIRED_TOPIC:
            record["expired"] = {
                "waitedSec": decode_uints(log.data, 1)[0],
                "blockNumber": log.block_number,
                "txHash": log.transaction_hash,
            }
        elif topic == PROPOSAL_EVALUATED_TOPIC:
            values = decode_uints(log.data, 6)
            record["evaluated"] = {
                "modelLpShareBps": values[0],
                "finalLpShareBps": values[1],
                "modelRangeWidthBps": values[2],
                "finalRangeWidthBps": values[3],
                "clampMask": values[4],
                "clampNames": decode_flags(values[4], CLAMP_NAMES),
                "evaluatedAt": values[5],
                "blockNumber": log.block_number,
                "txHash": log.transaction_hash,
            }
        elif topic == PROPOSAL_REJECTED_TOPIC:
            reason = decode_uints(log.data, 1)[0]
            record["rejected"] = {
                "reason": reason,
                "reasonNames": decode_flags(reason, REJECT_NAMES) or [f"UNKNOWN_{reason}"],
                "proposer": decode_address_at(log.data, 1),
                "blockNumber": log.block_number,
                "txHash": log.transaction_hash,
            }
        elif topic == NO_TRADE_TOPIC:
            values = decode_uints(log.data, 3)
            record["noTrade"] = {
                "currentLpShareBps": values[0],
                "targetLpShareBps": values[1],
                "clampMask": values[2],
                "clampNames": decode_flags(values[2], CLAMP_NAMES),
                "blockNumber": log.block_number,
                "txHash": log.transaction_hash,
            }
        elif topic == REBALANCE_REQUESTED_TOPIC:
            values = decode_uints(log.data, 5)
            record["rebalanceRequested"] = {
                "lpShareBps": values[0],
                "rangeWidthBps": values[1],
                "action": values[2],
                "clampMask": values[3],
                "requestedAt": values[4],
                "blockNumber": log.block_number,
                "txHash": log.transaction_hash,
            }
        elif topic == AUTONOMOUS_EXIT_TOPIC:
            values = decode_uints(log.data, 3)
            record["autonomousExit"] = {
                "volBps": values[0],
                "rangeWidthBps": values[1],
                "exitedAt": values[2],
                "blockNumber": log.block_number,
                "txHash": log.transaction_hash,
            }
        elif topic == FORECAST_GRADED_TOPIC:
            values = decode_uints(log.data, 4)
            record["forecastGraded"] = {
                "volErrBps": values[0],
                "rateErrBps": values[1],
                "realizedVolBps": values[2],
                "realizedRateBps": values[3],
                "blockNumber": log.block_number,
                "txHash": log.transaction_hash,
            }

    for log in base_logs:
        topic = log.topics[0]
        if topic == DECISION_REQUESTED_TOPIC:
            cycle_id = int(log.topics[1], 16)
            values = decode_uints(log.data, 6)
            slot(cycle_id)["requested"] = {
                "priceE18": values[0],
                "rateBps": values[1],
                "volBps": values[2],
                "currentLpShareBps": values[3],
                "totalValueUsd": values[4],
                "requestedAt": values[5],
                "blockNumber": log.block_number,
                "txHash": log.transaction_hash,
            }
        elif topic == PROPOSAL_POSTED_TOPIC:
            cycle_id = int(log.topics[2], 16)
            values = decode_uints(log.data, 5)
            slot(cycle_id)["posted"] = {
                "proposer": "0x" + log.topics[1][-40:],
                "lpShareBps": values[0],
                "rangeWidthBps": values[1],
                "forecastVolBps": values[2],
                "forecastYieldBps": values[3],
                "proposedAt": values[4],
                "blockNumber": log.block_number,
                "txHash": log.transaction_hash,
            }
        elif topic == REBALANCED_TOPIC:
            cycle_id = int(log.topics[1], 16)
            values = decode_uints(log.data, 6)
            slot(cycle_id)["rebalanced"] = {
                "lpShareBps": values[0],
                "rangeWidthBps": values[1],
                "lpValueUsd": values[2],
                "totalValueUsd": values[3],
                "action": values[4],
                "clampMask": values[5],
                "clampNames": decode_flags(values[5], CLAMP_NAMES),
                "blockNumber": log.block_number,
                "txHash": log.transaction_hash,
            }

    ordered = [cycles[key] for key in sorted(cycles)]
    # The vault's `Rebalanced` event carries no timestamp, so the block it landed in is the
    # only honest way to say when the money actually moved.
    for record in ordered:
        if record["rebalanced"]:
            record["rebalanced"]["timestamp"] = block_timestamp(base, record["rebalanced"]["blockNumber"])
    for record in ordered:
        record["outcome"] = outcome_of(record)
        record["fullCycle"] = is_full_cycle(record)
    return ordered


def outcome_of(record: dict) -> str:
    """What the chain did with this cycle, in one word."""
    if record["rebalanced"]:
        action = record["rebalanced"]["action"]
        return "autonomous_exit" if action == 1 else "rebalanced"
    if record["rebalanceRequested"]:
        return "rebalance_requested"
    if record["rejected"]:
        return "rejected"
    if record["noTrade"]:
        return "no_trade"
    if record["evaluated"]:
        return "evaluated"
    if record["expired"]:
        return "expired"
    return "open"


def is_full_cycle(record: dict) -> bool:
    """Whether the cycle went all the way round.

    A full cycle is: the contract opened it, the vault was asked about it, the agent
    posted a proposal, the contract judged that proposal, and the cycle ended in a
    decision — a rebalance, a no-trade, or a rejection. A cycle that only opened, or that
    expired unanswered, is not a full cycle and is not counted as one.
    """
    return bool(
        record["opened"]
        and record["requested"]
        and record["posted"]
        and (record["evaluated"] or record["rejected"])
        and (record["rebalanced"] or record["noTrade"] or record["rejected"])
    )


def short(hash_value: str | None) -> str:
    if not hash_value:
        return "—"
    return f"`{hash_value[:10]}…{hash_value[-6:]}`"


def link(hash_value: str | None, base_url: str) -> str:
    if not hash_value:
        return "—"
    return f"[`{hash_value[:8]}…`]({base_url}{hash_value})"


def block_timestamp(client: ChainClient, block_number: int) -> int | None:
    """The timestamp of a block, or `None` if the node will not say."""
    try:
        return client.block_timestamp(block_number)
    except Exception:
        return None


def write_jsonl(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def write_markdown(records: list[dict], deployment: dict, path: Path) -> None:
    lasna_url = deployment["reactive"]["explorer"].rstrip("/") + "/tx/"
    base_url = deployment["explorer"].rstrip("/") + "/tx/"

    full = [r for r in records if r["fullCycle"]]
    clamped = [r for r in records if r["evaluated"] and r["evaluated"]["clampMask"]]
    vetoed = [r for r in records if r["evaluated"] and r["evaluated"]["clampMask"] & (1 << 5)]
    rejected = [r for r in records if r["rejected"]]
    exits = [r for r in records if r["autonomousExit"] or (r["rebalanced"] and r["rebalanced"]["action"] == 1)]
    rebalanced = [r for r in records if r["rebalanced"]]
    opened_lp = [r for r in rebalanced if r["rebalanced"]["lpShareBps"] > 0]
    no_trade = [r for r in records if r["noTrade"]]
    expired = [r for r in records if r["expired"] and not r["posted"]]

    # The longest run of consecutive cycle ids that were written off unanswered. This is the
    # window where no agent was running; it is reported rather than trimmed.
    runs: list[list[dict]] = []
    current: list[dict] = []
    for record in expired:
        if current and record["cycleId"] != current[-1]["cycleId"] + 1:
            runs.append(current)
            current = []
        current.append(record)
    if current:
        runs.append(current)
    gap = max(runs, key=len) if runs else []

    def opened_utc(record: dict) -> str:
        ts = (record.get("opened") or {}).get("openedAt")
        if not ts:
            return "unknown time"
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = []
    add = lines.append

    add("# On-chain evidence")
    add("")
    add(
        "Every row below was read off the two chains by `scripts/collect-evidence.py`, which "
        "writes this file and `agent/ledger/chain-events.jsonl` from the same pass. Nothing "
        "here is typed by hand."
    )
    add("")
    add(f"* **Enforcer (Reactive Lasna, {deployment['reactive']['chainId']})** — `{deployment['reactive']['address']}`")
    add(f"* **Vault (Base Sepolia, {deployment['chainId']})** — `{deployment['vault']}`")
    add(f"* **Cycles seen:** {len(records)} · **full cycles:** {len(full)}")
    add(f"* **Proposals clamped by the contract:** {len(clamped)}")
    add(f"* **Proposals stopped by the economic veto:** {len(vetoed)}")
    add(f"* **Proposals rejected before execution:** {len(rejected)}")
    add(f"* **Rebalances that moved funds:** {len(rebalanced)} (of which {len(opened_lp)} opened a liquidity position)")
    add(f"* **Autonomous exits (contract acted without the model):** {len(exits)}")
    add(f"* **No-trades (move below the minimum trade):** {len(no_trade)}")
    add(f"* **Cycles written off unanswered:** {len(expired)}")
    if gap:
        add(
            f"* **The longest unanswered run:** {len(gap)} cycles, "
            f"{gap[0]['cycleId']}–{gap[-1]['cycleId']}, from {opened_utc(gap[0])} to {opened_utc(gap[-1])}"
        )
    add("")
    if gap:
        add(
            f"The {len(gap)} cycles from {opened_utc(gap[0])} to {opened_utc(gap[-1])} were opened "
            "while the agent was offline. The enforcer kept opening cycles on its cron subscription "
            "and wrote each one off when the freshness window closed: no proposal, no callback that "
            "moved funds, no manual intervention. That is the designed failure mode — the model is an "
            "input, not a dependency. The run is left in the record rather than trimmed, because it is "
            "the clearest evidence that the contract stays safe when the AI is not there."
        )
        add("")

    add("## The loop, leg by leg")
    add("")
    add(
        "A full cycle has six legs. The first three are the Reactive part: the contract opens "
        "the cycle on Lasna, calls back to the vault on Base Sepolia, and the agent answers by "
        "posting a proposal. The last three are the enforcement part: the contract judges the "
        "proposal against the envelope, and either moves the position or refuses to."
    )
    add("")
    add(
        "| Cycle | Opened (Lasna) | Asked (Base) | Posted (Base) | Judged (Lasna) | Result | "
        "Model → enforced | Clamp |"
    )
    add("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for record in records:
        if not record["fullCycle"]:
            continue
        opened = record["opened"]
        requested = record["requested"]
        posted = record["posted"]
        judged = record["evaluated"] or record["rejected"]
        evaluated = record["evaluated"]
        if evaluated:
            model = evaluated["modelLpShareBps"]
            enforced = evaluated["finalLpShareBps"]
            clamp = ", ".join(evaluated["clampNames"]) or "none"
        else:
            model = posted["lpShareBps"] if posted else "—"
            enforced = "—"
            clamp = ", ".join(record["rejected"]["reasonNames"])
        add(
            f"| {record['cycleId']} "
            f"| {link(opened['txHash'], lasna_url)} "
            f"| {link(requested['txHash'], base_url)} "
            f"| {link(posted['txHash'], base_url)} "
            f"| {link(judged['txHash'], lasna_url)} "
            f"| {record['outcome']} "
            f"| {model} → {enforced} bps "
            f"| {clamp} |"
        )
    add("")

    add("## Every cycle, including the ones that did not complete")
    add("")
    add("| Cycle | Outcome | Opened | Asked | Posted | Judged | Result tx |")
    add("| --- | --- | --- | --- | --- | --- | --- |")
    for record in records:
        opened = record["opened"]
        requested = record["requested"]
        posted = record["posted"]
        judged = record["evaluated"] or record["rejected"]
        result = None
        result_url = base_url
        for key, url in (
            ("rebalanced", base_url),
            ("noTrade", lasna_url),
            ("rejected", lasna_url),
            ("expired", lasna_url),
            ("autonomousExit", lasna_url),
        ):
            if record.get(key):
                result = record[key]
                result_url = url
                break
        result_tx = result["txHash"] if result else None
        add(
            f"| {record['cycleId']} "
            f"| {record['outcome']} "
            f"| {link(opened['txHash'] if opened else None, lasna_url)} "
            f"| {link(requested['txHash'] if requested else None, base_url)} "
            f"| {link(posted['txHash'] if posted else None, base_url)} "
            f"| {link(judged['txHash'] if judged else None, lasna_url)} "
            f"| {link(result_tx, result_url)} |"
        )
    add("")

    add("## The five things the judges are asked to look for")
    add("")
    if clamped:
        record = clamped[0]
        add(
            f"1. **A clamped proposal.** Cycle {record['cycleId']}: the model asked for "
            f"{record['evaluated']['modelLpShareBps']} bps, the contract allowed "
            f"{record['evaluated']['finalLpShareBps']} bps. "
            f"Clamp bits: {', '.join(record['evaluated']['clampNames'])}. "
            f"Transaction: {link(record['evaluated']['txHash'], lasna_url)}"
        )
    else:
        add("1. **A clamped proposal.** Not observed.")
    if vetoed:
        record = vetoed[0]
        add(
            f"2. **The economic veto.** Cycle {record['cycleId']}: the contract measured a fee "
            f"edge under its own threshold and sent the allocation to zero on its own. "
            f"Clamp bits: {', '.join(record['evaluated']['clampNames'])}. "
            f"Transaction: {link(record['evaluated']['txHash'], lasna_url)}"
        )
    else:
        add("2. **The economic veto.** Not observed.")
    if rebalanced:
        record = rebalanced[0]
        value = record["rebalanced"]["lpValueUsd"] / 10**18
        add(
            f"3. **Funds actually moving.** Cycle {record['cycleId']}: the vault took a "
            f"{record['rebalanced']['lpShareBps']} bps liquidity position worth "
            f"${value:,.2f} out of a ${record['rebalanced']['totalValueUsd'] / 10**18:,.2f} "
            f"vault. Transaction: {link(record['rebalanced']['txHash'], base_url)}"
        )
    else:
        add("3. **Funds actually moving.** Not observed.")
    if exits:
        record = exits[0]
        source = record["autonomousExit"] or record["rebalanced"]
        add(
            f"4. **The contract acting without the model.** Cycle {record['cycleId']}: "
            f"the contract measured {source.get('volBps', '—')} bps of volatility, over the "
            f"user's exit level, and pulled the position to zero with no proposal in sight. "
            f"Transaction: {link(source['txHash'], lasna_url if record['autonomousExit'] else base_url)}"
        )
    else:
        add("4. **The contract acting without the model.** Not observed in this window.")
    if rejected:
        record = rejected[0]
        add(
            f"5. **A proposal refused before execution.** Cycle {record['cycleId']}: refused with "
            f"{', '.join(record['rejected']['reasonNames'])}. The agent's proposal carries no "
            f"authority: the contract checked it and threw it away. "
            f"Transaction: {link(record['rejected']['txHash'], lasna_url)}"
        )
    else:
        add("5. **A proposal refused before execution.** Not observed in this window.")
    add("")

    add("## Latency across the whole loop")
    add("")
    add(
        "The event announcement asks for latency measured across the full loop, not one leg "
        "of it. The numbers below are the gap between the block the contract opened the cycle "
        "in and the block the vault's rebalance landed in, and the gap between opening the "
        "cycle and the agent's proposal."
    )
    add("")
    add("| Cycle | Open → proposal | Open → enforced | Open → funds moved |")
    add("| --- | --- | --- | --- |")
    latencies = []
    for record in records:
        if not record["fullCycle"] or not record["opened"]:
            continue
        opened = record["opened"]
        proposal_seconds = None
        if record["posted"] and record["posted"]["proposedAt"] and opened["openedAt"]:
            proposal_seconds = record["posted"]["proposedAt"] - opened["openedAt"]
        judged_seconds = None
        if record["evaluated"] and record["evaluated"]["evaluatedAt"] and opened["openedAt"]:
            judged_seconds = record["evaluated"]["evaluatedAt"] - opened["openedAt"]
        moved_seconds = None
        if record["rebalanced"] and record["rebalanced"].get("timestamp") and opened["openedAt"]:
            moved_seconds = record["rebalanced"]["timestamp"] - opened["openedAt"]
        if proposal_seconds is None and judged_seconds is None:
            continue
        latencies.append((proposal_seconds, judged_seconds))
        add(
            f"| {record['cycleId']} "
            f"| {f'{proposal_seconds:.0f}s' if proposal_seconds is not None else '—'} "
            f"| {f'{judged_seconds:.0f}s' if judged_seconds is not None else '—'} "
            f"| {f'{moved_seconds:.0f}s' if moved_seconds is not None else '—'} |"
        )
    add("")
    if latencies:
        proposals = [p for p, _ in latencies if p is not None]
        judged = [j for _, j in latencies if j is not None]
        if proposals:
            add(
                f"* Open → proposal: median **{sorted(proposals)[len(proposals) // 2]:.0f}s**, "
                f"worst **{max(proposals):.0f}s** over {len(proposals)} cycles."
            )
        if judged:
            add(
                f"* Open → enforced: median **{sorted(judged)[len(judged) // 2]:.0f}s**, "
                f"worst **{max(judged):.0f}s** over {len(judged)} cycles."
            )
    add("")

    add("## Full transaction hashes")
    add("")
    add("| Cycle | Leg | Chain | Transaction hash |")
    add("| --- | --- | --- | --- |")
    legs = [
        ("opened", "Lasna", lasna_url),
        ("requested", "Base Sepolia", base_url),
        ("posted", "Base Sepolia", base_url),
        ("evaluated", "Lasna", lasna_url),
        ("rejected", "Lasna", lasna_url),
        ("noTrade", "Lasna", lasna_url),
        ("rebalanceRequested", "Lasna", lasna_url),
        ("rebalanced", "Base Sepolia", base_url),
        ("autonomousExit", "Lasna", lasna_url),
    ]
    for record in records:
        for key, chain_name, url in legs:
            leg = record.get(key)
            if not leg:
                continue
            add(f"| {record['cycleId']} | {key} | {chain_name} | `{leg['txHash']}` |")
    add("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deployment", type=Path, default=ROOT / "deployments" / "base-sepolia.json")
    parser.add_argument("--out", type=Path, default=ROOT / "agent" / "ledger" / "chain-events.jsonl")
    parser.add_argument("--markdown", type=Path, default=ROOT / "docs" / "EVIDENCE.md")
    parser.add_argument("--lasna-blocks", type=int, default=60_000)
    parser.add_argument("--base-blocks", type=int, default=250_000)
    args = parser.parse_args(argv)

    deployment = load_deployment(args.deployment)
    lasna = ChainClient(rpc_url=deployment["reactive"]["rpc"], chain_id=deployment["reactive"]["chainId"])
    base = ChainClient(rpc_url=deployment["rpc"], chain_id=deployment["chainId"])

    records = build_cycles(deployment, lasna, base, args.lasna_blocks, args.base_blocks)
    write_jsonl(records, args.out)
    write_markdown(records, deployment, args.markdown)

    full = sum(1 for r in records if r["fullCycle"])
    clamped = sum(1 for r in records if r["evaluated"] and r["evaluated"]["clampMask"])
    print(f"cycles: {len(records)}  full: {full}  clamped: {clamped}")
    print(f"jsonl:  {args.out}")
    print(f"markdown: {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
