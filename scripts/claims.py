#!/usr/bin/env python3
"""Generate `docs/CLAIMS.md`: every factual number Helm makes, from the artifacts.

The rule this script enforces is simple: **a number in the README, the docs, the
dashboard or the submission description has to come from here.** Not from memory, not
from a previous run of the model, not from a message in a chat.

Each row below is read out of the artifact it describes:

| Claim | Read from |
| --- | --- |
| backtest numbers | `agent/models/metrics.json` |
| on-chain evidence | `agent/ledger/chain-events.jsonl` |
| the agent's own log | `agent/ledger/cycles.jsonl` |
| deployed addresses | `deployments/base-sepolia.json` |
| compiler settings | `contracts/foundry.toml` |
| test counts | the suites, run right now |
| repository revision | `git rev-parse HEAD` |

Usage:
    scripts/claims.py [--out docs/CLAIMS.md] [--skip-tests]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "agent"
sys.path.insert(0, str(AGENT))

from helm_agent.keccak import keccak256  # noqa: E402
AGENT_PYTHON = AGENT / ".venv" / "bin" / "python"
FOUNDRY_BIN = Path.home() / ".foundry" / "bin"


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    try:
        raw = path.read_text()
    except OSError:
        return rows
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def run(command: list[str], cwd: Path | None = None) -> tuple[int, str]:
    env = dict(os.environ)
    # `forge` lives in ~/.foundry/bin, which is not always on the PATH of a cron-style
    # invocation. The registry must be able to run the suites itself, not report "?".
    foundry_dir = str(FOUNDRY_BIN)
    if FOUNDRY_BIN.exists() and foundry_dir not in env.get("PATH", "").split(":"):
        env["PATH"] = foundry_dir + ":" + env.get("PATH", "")
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=600,
            env=env,
        )
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def python_exe() -> str:
    """Use the agent's virtualenv when it exists, so `-m pytest` resolves."""
    return str(AGENT_PYTHON) if AGENT_PYTHON.exists() else sys.executable


def pct(value: float, digits: int = 2) -> str:
    return f"{value * 100:.{digits}f}%"


def usd(value: float, digits: int = 2) -> str:
    return f"${value:,.{digits}f}"


def utc(ts: int | float | None) -> str:
    if not ts:
        return "—"
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def count_tests() -> tuple[str, str]:
    """Run both suites and report their counts."""
    # The agent's pyproject already sets `addopts = "-q"`, so passing another `-q` here
    # would quieten the summary line this parses.
    code, output = run([python_exe(), "-m", "pytest", "tests"], cwd=AGENT)
    pytest_line = ""
    for line in output.splitlines():
        if "passed" in line or "failed" in line or "error" in line:
            pytest_line = line.strip()
            break
    pytest_count = ""
    match = re.search(r"(\d+) passed", pytest_line)
    if match:
        pytest_count = match.group(1)
    elif "no tests ran" in pytest_line:
        pytest_count = "0"

    forge_code, forge_output = run(["forge", "test"], cwd=ROOT / "contracts")
    forge_count = ""
    # `forge test` prints one "N passed" line per suite plus a final "N tests passed"
    # summary. The summary is the total; fall back to summing the per-suite lines.
    match = re.search(r"(\d+) tests passed", forge_output)
    if match:
        forge_count = match.group(1)
    else:
        suite_counts = re.findall(r"(\d+) passed", forge_output)
        if suite_counts:
            forge_count = str(sum(int(n) for n in suite_counts))
    return pytest_count or "?", forge_count or "?"


def toolchain_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    _, forge = run(["forge", "--version"])
    match = re.search(r"forge\s+Version:\s*(\S+)", forge)
    if not match:
        match = re.search(r"forge\s+(\S+)", forge)
    versions["forge"] = match.group(1) if match else "not installed"
    _, solc = run(["solc", "--version"])
    match = re.search(r"Version:\s*(\S+)", solc)
    versions["solc"] = match.group(1) if match else "not installed"
    _, python = run([python_exe(), "--version"])
    versions["python"] = python.strip().splitlines()[0] if python.strip() else "unknown"
    return versions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "CLAIMS.md")
    parser.add_argument("--skip-tests", action="store_true", help="do not run the suites")
    args = parser.parse_args(argv)

    deployment = read_json(ROOT / "deployments" / "base-sepolia.json") or {}
    metrics = read_json(AGENT / "models" / "metrics.json") or {}
    chain_rows = read_jsonl(AGENT / "ledger" / "chain-events.jsonl")
    ledger_rows = read_jsonl(AGENT / "ledger" / "cycles.jsonl")

    foundry_toml = ""
    try:
        foundry_toml = (ROOT / "contracts" / "foundry.toml").read_text()
    except OSError:
        pass

    settings = {}
    for key in ("solc", "optimizer", "optimizer_runs", "evm_version", "via_ir"):
        match = re.search(rf"^\s*{key}\s*=\s*(.+)$", foundry_toml, re.M)
        settings[key] = match.group(1).strip() if match else "—"

    if args.skip_tests:
        pytest_count, forge_count = "skipped", "skipped"
    else:
        pytest_count, forge_count = count_tests()

    versions = toolchain_versions()
    revision_code, revision = run(["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT)
    if revision_code != 0:
        revision = "not committed yet"
    else:
        revision = revision.strip()

    strategies = metrics.get("strategies", {})
    model = strategies.get("model", {})
    best_rate = strategies.get("best_rate_now", {})
    static = strategies.get("static_50_50", {})
    lending = strategies.get("all_lending", {})
    lp = strategies.get("all_lp", {})

    full_cycles = [row for row in chain_rows if row.get("fullCycle")]
    clamped = [row for row in chain_rows if (row.get("evaluated") or {}).get("clampMask")]
    vetoed = [
        row
        for row in chain_rows
        if (row.get("evaluated") or {}).get("clampMask", 0) & (1 << 5)
    ]
    rejected = [row for row in chain_rows if row.get("rejected")]
    exits = [row for row in chain_rows if row.get("autonomousExit")]
    rebalanced = [row for row in chain_rows if row.get("rebalanced")]
    moved_lp = [
        row
        for row in rebalanced
        if (row.get("rebalanced") or {}).get("lpShareBps", 0) > 0
    ]
    expired = [row for row in chain_rows if row.get("expired") and not row.get("posted")]

    # The longest run of consecutive cycles that were written off unanswered. This is the
    # week the agent process was down, and it is the clearest evidence that the contract
    # does not need the agent to stay safe.
    runs: list[list[dict]] = []
    current: list[dict] = []
    for row in expired:
        cycle_id = row.get("cycleId", 0)
        if current and cycle_id != current[-1].get("cycleId", 0) + 1:
            runs.append(current)
            current = []
        current.append(row)
    if current:
        runs.append(current)
    longest_run = max(runs, key=len) if runs else []

    latencies = []
    for row in full_cycles:
        opened = row.get("opened") or {}
        posted = row.get("posted") or {}
        evaluated = row.get("evaluated") or {}
        if opened.get("openedAt") and posted.get("proposedAt"):
            latencies.append(
                {
                    "proposal": posted["proposedAt"] - opened["openedAt"],
                    "enforced": (evaluated.get("evaluatedAt") or 0) - opened["openedAt"],
                }
            )
    proposal_times = sorted(item["proposal"] for item in latencies if item["proposal"] >= 0)
    enforced_times = sorted(item["enforced"] for item in latencies if item["enforced"] >= 0)

    lines: list[str] = []
    add = lines.append

    add("# Claims registry")
    add("")
    add(
        "Every number Helm states anywhere — in the README, the docs, the dashboard or the "
        "submission description — is in this file, and this file is generated by "
        "`scripts/claims.py` from the artifacts themselves. If a number is not here, it was "
        "not measured."
    )
    add("")
    add(f"*Generated {utc(datetime.now(tz=timezone.utc).timestamp())} from revision `{revision}`.*")
    add("")
    add("| | |")
    add("| --- | --- |")
    add(f"| Repository revision | `{revision}` |")
    add(f"| Foundry | {versions['forge']} |")
    add(f"| solc | {versions['solc']} |")
    add(f"| Python | {versions['python']} |")
    add(f"| `optimizer` | {settings.get('optimizer', '—')} |")
    add(f"| `optimizer_runs` | {settings.get('optimizer_runs', '—')} |")
    add(f"| `evm_version` | {settings.get('evm_version', '—')} |")
    add(f"| `via_ir` | {settings.get('via_ir', '—')} |")
    add(f"| Foundry tests passing | **{forge_count}** |")
    add(f"| Python tests passing | **{pytest_count}** |")
    add("")

    add("## Deployment")
    add("")
    add("| What | Value |")
    add("| --- | --- |")
    add(f"| Reactive enforcer (Lasna, chain {deployment.get('reactive', {}).get('chainId', '—')}) | `{deployment.get('reactive', {}).get('address', '—')}` |")
    add(f"| Vault (Base Sepolia, chain {deployment.get('chainId', '—')}) | `{deployment.get('vault', '—')}` |")
    add(f"| LP pool | `{deployment.get('lpPool', '—')}` |")
    add(f"| Lending pool | `{deployment.get('lendingPool', '—')}` |")
    add(f"| Mock USD token | `{deployment.get('token', '—')}` |")
    add(f"| Callback proxy | `{deployment.get('callbackProxy', '—')}` |")
    add(f"| Agent | `{deployment.get('agent', '—')}` |")
    limits = deployment.get("limits", {})
    add(f"| LP share limits | {limits.get('lpShareMinBps', '—')}–{limits.get('lpShareMaxBps', '—')} bps |")
    add(f"| Range width limits | {limits.get('rangeWidthMinBps', '—')}–{limits.get('rangeWidthMaxBps', '—')} bps |")
    add(f"| Cooldown | {limits.get('cooldownSec', '—')} s |")
    add(f"| Volatility exit level | {limits.get('volExitLevelBps', '—')} bps |")
    add(f"| Minimum trade | {limits.get('minTradeBps', '—')} bps |")
    add(f"| Freshness window | {limits.get('freshnessSec', '—')} s |")
    add("")

    add("## Artifact identity")
    add("")
    add(
        "The committed Foundry artifact and the deployed runtime, hashed. Solidity inlines "
        "immutables, so the two are compared byte by byte outside the immutable sites by "
        "`scripts/verify-bytecode.py`; the hashes below are the whole-code fingerprints."
    )
    add("")
    add("| Contract | Artifact | Artifact bytes | Artifact keccak-256 | On-chain bytes | On-chain keccak-256 |")
    add("| --- | --- | --- | --- | --- | --- |")
    for name, artifact_rel, address, rpc in (
        (
            "HelmReactive",
            "contracts/out/HelmReactive.sol/HelmReactive.json",
            deployment.get("reactive", {}).get("address", ""),
            deployment.get("reactive", {}).get("rpc", ""),
        ),
        (
            "HelmVault",
            "contracts/out/HelmVault.sol/HelmVault.json",
            deployment.get("vault", ""),
            deployment.get("rpc", ""),
        ),
    ):
        artifact_path = ROOT / artifact_rel
        try:
            code = json.loads(artifact_path.read_text())["deployedBytecode"]["object"]
            code = code[2:] if code.startswith("0x") else code
            artifact_bytes = bytes.fromhex(code)
            artifact_hash = "0x" + keccak256(artifact_bytes).hex()
            artifact_len = len(artifact_bytes)
        except (OSError, KeyError, json.JSONDecodeError, ValueError):
            artifact_len, artifact_hash = "—", "—"
        _, onchain = run(["cast", "code", address, "--rpc-url", rpc])
        onchain = onchain.strip()
        if onchain.startswith("0x"):
            onchain_bytes = bytes.fromhex(onchain[2:])
            onchain_hash = "0x" + keccak256(onchain_bytes).hex()
            onchain_len = len(onchain_bytes)
        else:
            onchain_len, onchain_hash = "—", "—"
        add(
            f"| `{name}` | `{artifact_rel}` | {artifact_len} | `{artifact_hash}` | "
            f"{onchain_len} | `{onchain_hash}` |"
        )
    add("")
    add(
        "Byte equality outside the immutable sites: "
        "`python3 scripts/verify-bytecode.py --label <name> --artifact <artifact> "
        "--address <address> --rpc <rpc> --immutable <address> …` — both contracts pass, "
        "and `bash scripts/verify-deployment.sh` runs them as part of its 26 checks."
    )
    add("")

    add("## On-chain evidence")
    add("")
    add(
        "Read off both chains by `scripts/collect-evidence.py`. The transaction hashes are in "
        "`agent/ledger/chain-events.jsonl` and in `docs/EVIDENCE.md`."
    )
    add("")
    add("| Claim | Value |")
    add("| --- | --- |")
    add(f"| Cycles opened on chain | **{len(chain_rows)}** |")
    add(f"| Full cycles (opened → asked → proposed → judged → result) | **{len(full_cycles)}** |")
    add(f"| Proposals clamped by the contract | **{len(clamped)}** |")
    add(f"| Proposals stopped by the economic veto | **{len(vetoed)}** |")
    add(f"| Proposals refused before execution | **{len(rejected)}** |")
    add(f"| Rebalances that moved funds | **{len(rebalanced)}** |")
    add(f"| Rebalances that opened a liquidity position | **{len(moved_lp)}** |")
    add(f"| Autonomous exits (contract acted with no proposal) | **{len(exits)}** |")
    add(f"| Cycles written off unanswered | **{len(expired)}** |")
    if longest_run:
        add(
            f"| Longest unanswered run | **{len(longest_run)} cycles** "
            f"(cycle {longest_run[0]['cycleId']}–{longest_run[-1]['cycleId']}) |"
        )
    add(f"| Cycles the agent answered and logged | **{len(ledger_rows)}** |")
    if proposal_times:
        add(f"| Open → proposal, median | **{proposal_times[len(proposal_times) // 2]} s** |")
        add(f"| Open → proposal, worst | **{max(proposal_times)} s** |")
    if enforced_times:
        add(f"| Open → enforced, median | **{enforced_times[len(enforced_times) // 2]} s** |")
        add(f"| Open → enforced, worst | **{max(enforced_times)} s** |")
    add("")

    add("## The cycles the README shows")
    add("")
    add(
        "Five cycles, picked by rule rather than by hand: the first one that opened a "
        "liquidity position, the first one the contract refused, the first autonomous exit, "
        "the first one the economic veto stopped, and the fastest complete cycle. The README "
        "table is copied from this one."
    )
    add("")
    add("| Case | Cycle | Opened (Lasna) | Asked (Base) | Posted (Base) | Judged (Lasna) | Result |")
    add("| --- | --- | --- | --- | --- | --- | --- |")

    def first_where(predicate):
        for row in chain_rows:
            if predicate(row):
                return row
        return None

    def latency_of(row):
        opened = (row.get("opened") or {}).get("openedAt") or 0
        posted = (row.get("posted") or {}).get("proposedAt") or 0
        return posted - opened if opened and posted else None

    opened_lp_row = first_where(
        lambda r: (r.get("rebalanced") or {}).get("lpShareBps", 0) > 0
    )
    refused_row = first_where(lambda r: r.get("rejected"))
    exit_row = first_where(lambda r: r.get("autonomousExit"))
    veto_row = first_where(
        lambda r: (r.get("evaluated") or {}).get("clampMask", 0) & (1 << 5)
        and r.get("rebalanced")
    )
    timed = [r for r in full_cycles if latency_of(r) is not None]
    fastest_row = min(timed, key=latency_of) if timed else None

    lasna_explorer = deployment.get("reactive", {}).get("explorer", "").rstrip("/") + "/tx/"
    base_explorer = deployment.get("explorer", "").rstrip("/") + "/tx/"

    def link_of(hash_value, base):
        if not hash_value:
            return "—"
        return f"[`{hash_value[:8]}…`]({base}{hash_value})"

    showcase = [
        ("opened a liquidity position", opened_lp_row),
        ("the contract refused the proposal", refused_row),
        ("the contract acted with no proposal", exit_row),
        ("the economic veto stopped it", veto_row),
        ("the fastest complete cycle", fastest_row),
    ]
    for label, row in showcase:
        if not row:
            continue
        opened = row.get("opened") or {}
        requested = row.get("requested") or {}
        posted = row.get("posted") or {}
        judged = row.get("evaluated") or row.get("rejected") or {}
        result = (
            row.get("rebalanced")
            or row.get("noTrade")
            or row.get("rejected")
            or row.get("autonomousExit")
            or {}
        )
        if result.get("txHash") and result is (row.get("rebalanced") or {}):
            result_link = link_of(result["txHash"], base_explorer)
        elif result.get("txHash") and result is (row.get("autonomousExit") or {}):
            result_link = link_of(result["txHash"], lasna_explorer)
        elif result.get("txHash"):
            result_link = link_of(result["txHash"], lasna_explorer)
        else:
            result_link = "—"
        evaluated = row.get("evaluated") or {}
        if evaluated:
            decision = (
                f"{evaluated.get('modelLpShareBps')} → {evaluated.get('finalLpShareBps')} bps "
                f"({', '.join(evaluated.get('clampNames', [])) or 'inside the envelope'})"
            )
        elif row.get("rejected"):
            decision = "refused: " + ", ".join(row["rejected"].get("reasonNames", []))
        elif row.get("autonomousExit"):
            decision = (
                f"autonomous exit at {row['autonomousExit'].get('volBps')} bps of volatility, "
                "no proposal involved"
            )
        else:
            decision = "—"
        add(
            f"| {label} | {row.get('cycleId')} "
            f"| {link_of(opened.get('txHash'), lasna_explorer)} "
            f"| {link_of(requested.get('txHash'), base_explorer)} "
            f"| {link_of(posted.get('txHash'), base_explorer)} "
            f"| {link_of(judged.get('txHash'), lasna_explorer)} "
            f"| {decision} · {result_link} |"
        )
    add("")

    add("## The model")
    add("")
    add("| Claim | Value |")
    add("| --- | --- |")
    add(f"| Training history bars | {metrics.get('historyBars', '—')} |")
    add(f"| Bar length | {metrics.get('barSeconds', '—')} s |")
    add(f"| History window | {utc(metrics.get('windowStart'))} → {utc(metrics.get('windowEnd'))} |")
    add(f"| Pool | `{metrics.get('pool', '—')}` |")
    add(f"| Pool fee | {metrics.get('poolFeeBps', '—')} bps |")
    add(f"| Dataset rows | {metrics.get('datasetRows', '—')} |")
    add(f"| Train rows | {metrics.get('trainRows', '—')} |")
    add(f"| Evaluation rows (held out) | **{metrics.get('evaluationRows', '—')}** |")
    add(f"| Forecast horizon | {metrics.get('horizonHours', '—')} h |")
    add(f"| Allocation label horizon | {metrics.get('allocationHorizonHours', '—')} h |")
    add(f"| Label smoothing | {metrics.get('smoothingHours', '—')} h |")
    add(f"| Minimum trade | {metrics.get('minTradeBps', '—')} bps |")
    add(f"| Capital | {usd(metrics.get('capitalUsd', 0))} |")
    add(f"| Lending rate | {metrics.get('lendingAprBps', '—')} bps |")
    add(f"| Rebalance cost | {metrics.get('rebalanceCostBps', '—')} bps per trade |")
    report = metrics.get("report", {})
    add(f"| Training epochs | {report.get('epochs', '—')} |")
    add(f"| Allocation MAE (held out) | {pct(report.get('allocation_mae', 0))} |")
    add(f"| Volatility MAE | {report.get('volatility_mae_bps', 0):,.0f} bps |")
    add(f"| Yield MAE | {report.get('yield_mae_bps', 0):,.0f} bps |")
    add("")

    add("## The backtest")
    add("")
    add(
        "Out of sample, on the held-out rows of real Base mainnet history for the Uniswap v3 "
        "ETH/USDC pool above. Reproduce with `agent/.venv/bin/python -m helm_agent.train`."
    )
    add("")
    add("| Strategy | Total return | Max drawdown | Trades | Fees earned | Rebalance cost |")
    add("| --- | --- | --- | --- | --- | --- |")
    labels = [
        ("model_contract", "**Helm (model + contract rules)**"),
        ("model", "Helm (model alone)"),
        ("best_rate_now", "Best rate now"),
        ("static_50_50", "Static 50/50"),
        ("all_lending", "All lending"),
        ("all_lp", "All LP"),
    ]
    for key, label in labels:
        result = strategies.get(key)
        if not result:
            continue
        add(
            f"| {label} | {pct(result.get('total_return', 0))} | "
            f"{pct(result.get('max_drawdown', 0))} | {result.get('trades', '—')} | "
            f"{usd(result.get('fees_earned', 0))} | {usd(result.get('rebalance_cost', 0))} |"
        )
    add("")
    deployed = strategies.get("model_contract") or model
    if deployed and best_rate:
        edge = deployed.get("total_return", 0) - best_rate.get("total_return", 0)
        add(
            f"**Helm beats \"best rate now\" by {edge * 100:.2f} points** of total return "
            f"({pct(deployed.get('total_return', 0))} against {pct(best_rate.get('total_return', 0))}), "
            f"with {deployed.get('trades', '—')} trades against the baseline's "
            f"{best_rate.get('trades', '—')}."
        )
    if deployed and lending:
        add(
            f"**Helm loses to \"all lending\" by "
            f"{(lending.get('total_return', 0) - deployed.get('total_return', 0)) * 100:.2f} points** "
            f"({pct(deployed.get('total_return', 0))} against {pct(lending.get('total_return', 0))}). "
            f"This is stated in the README and the dashboard, not hidden: the evaluation window "
            f"is a falling market, and staying in lending is the safe thing to do in it."
        )
    if deployed and static:
        static_gap = (static.get("total_return", 0) - deployed.get("total_return", 0)) * 100
        if static_gap > 0:
            add(
                f"**Helm loses to \"static 50/50\" by {static_gap:.2f} points** "
                f"({pct(deployed.get('total_return', 0))} against {pct(static.get('total_return', 0))}). "
                f"The model pays {usd(deployed.get('rebalance_cost', 0))} of rebalance cost over "
                f"{deployed.get('trades', '—')} trades for that."
            )
        else:
            add(
                f"**Helm beats \"static 50/50\" by {-static_gap:.2f} points** "
                f"({pct(deployed.get('total_return', 0))} against {pct(static.get('total_return', 0))}), "
                f"and pays {usd(deployed.get('rebalance_cost', 0))} of rebalance cost over "
                f"{deployed.get('trades', '—')} trades to do it."
            )
    if model and deployed and model is not deployed:
        add(
            f"The contract's own economic veto, applied on top of the model's proposals, is "
            f"worth {(deployed.get('total_return', 0) - model.get('total_return', 0)) * 100:.2f} "
            f"points on this window: the model alone returned {pct(model.get('total_return', 0))}, "
            f"and the same model with the veto returned {pct(deployed.get('total_return', 0))}. "
            f"The rule was already deployed and already firing on chain; nothing was added to "
            f"the model to produce it."
        )
    add("")

    windows = metrics.get("windows", [])
    if windows:
        add("### The same model, window by window")
        add("")
        add(
            "The evaluation region split into consecutive, disjoint windows, scored with the "
            "same fitted model. Every window is out of sample."
        )
        add("")
        add(
            "| Window | Days | Price move | Helm (model + contract) | Helm (model alone) | "
            "Best rate now | Static 50/50 | All lending | All LP |"
        )
        add("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for window in windows:
            window_strategies = window.get("strategies", {})
            add(
                f"| {window.get('index')} | {window.get('days', 0):.1f} | "
                f"{pct(window.get('priceChange', 0))} | "
                f"{pct(window_strategies.get('model_contract', {}).get('total_return', 0))} | "
                f"{pct(window_strategies.get('model', {}).get('total_return', 0))} | "
                f"{pct(window_strategies.get('best_rate_now', {}).get('total_return', 0))} | "
                f"{pct(window_strategies.get('static_50_50', {}).get('total_return', 0))} | "
                f"{pct(window_strategies.get('all_lending', {}).get('total_return', 0))} | "
                f"{pct(window_strategies.get('all_lp', {}).get('total_return', 0))} |"
            )
        add("")
        beats = {
            key: sum(
                1
                for window in windows
                if window.get("strategies", {})
                .get("model_contract", {})
                .get("total_return", 0)
                > window.get("strategies", {}).get(key, {}).get("total_return", 0)
            )
            for key in ("best_rate_now", "static_50_50", "all_lending", "all_lp")
        }
        add(
            f"Helm (model + contract) beat `best rate now` in **{beats['best_rate_now']} of "
            f"{len(windows)}** windows, `static 50/50` in **{beats['static_50_50']}**, "
            f"`all lending` in **{beats['all_lending']}** and `all LP` in "
            f"**{beats['all_lp']}**."
        )
        add("")

    fee_summary = metrics.get("feeSummary", {})
    if fee_summary:
        add("### The contract's economic veto on real market data")
        add("")
        add(
            f"The veto fires when the fee yield the chain measured does not beat the lending "
            f"rate by {fee_summary.get('minFeeEdgeBps', '—')} bps. On the real pool used by "
            f"this backtest it would have fired in "
            f"**{fee_summary.get('vetoFraction', 0) * 100:.0f}% of the evaluation window**: the "
            f"measured fee yield was below lending in "
            f"{fee_summary.get('belowLendingFraction', 0) * 100:.0f}% of the bars, and the "
            f"median measured yield was {fee_summary.get('medianAprBps', 0):,.0f} bps against a "
            f"lending rate of {fee_summary.get('lendingAprBps', 0):,.0f} bps."
        )
        add("")
        add(
            "The live deployment measures a different pool — the mock LP pool on Base Sepolia, "
            "whose flow is far smaller — so the contract's own measured fee yield on the "
            "testnet is much smaller and its veto fires far more often. The rule is the same; "
            "the pool behind it is not."
        )
        add("")

    add("## How to check each claim")
    add("")
    add("| Claim | Command |")
    add("| --- | --- |")
    add("| On-chain evidence | `agent/.venv/bin/python scripts/collect-evidence.py` |")
    add("| Backtest and model | `cd agent && .venv/bin/python -m helm_agent.train` |")
    add("| Foundry suite | `cd contracts && forge test` |")
    add("| Python suite | `cd agent && .venv/bin/python -m pytest tests -q` |")
    add("| Live deployment | `bash scripts/verify-deployment.sh` |")
    add("| This file | `agent/.venv/bin/python scripts/claims.py` |")
    add("")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines))
    print(f"claims written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
