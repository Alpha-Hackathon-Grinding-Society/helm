"""The agent's command line: watch the vault, answer every cycle, write the ledger.

    python -m helm_agent.cli --cycles 12

The command is the whole runtime in one place. It loads the live deployment, builds the
two chain clients, loads the trained model, and then does the only thing the agent is
allowed to do: post a proposal when the vault asks for one, and record what the chain
did about it.

The agent key can only call `postProposal`. It cannot move money, widen the envelope or
change the contract's settings, so a bug here costs gas and nothing else.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from helm_agent.chain import ChainClient
from helm_agent.config import DATA_DIR, MODEL_DIR
from helm_agent.deployment import Deployment
from helm_agent.listener import Agent, load_ledger


def build_agent(args: argparse.Namespace) -> Agent:
    """Assemble the running agent from the deployment record and the trained model."""
    deployment = Deployment.load(args.deployment) if args.deployment else Deployment.load()

    base = ChainClient(
        rpc_url=deployment.base_rpc,
        chain_id=deployment.chain_id,
        private_key=deployment.agent_key,
        from_address=deployment.agent,
    )
    reactive = ChainClient(
        rpc_url=deployment.lasna_rpc,
        chain_id=deployment.lasna_chain_id,
    )

    history_path = args.history or (DATA_DIR / "base_eth_usdc_15m.jsonl")
    model_path = args.model or (MODEL_DIR / "model.npz")
    if not model_path.exists():
        raise SystemExit(
            f"no model at {model_path}. Train one first:\n"
            f"  python -m helm_agent.train --history {history_path}"
        )
    if not history_path.exists():
        raise SystemExit(
            f"no history at {history_path}. Download it first:\n"
            f"  python -m helm_agent.data --out {history_path} --bucket 900"
        )

    return Agent.load(
        model_path,
        history_path,
        base=base,
        reactive=reactive,
        vault=deployment.vault,
        reactive_address=deployment.reactive,
        lending_rate_bps=float(args.lending_rate_bps),
        min_fee_edge_bps=int(args.min_fee_edge_bps),
        llm_enabled=not args.no_llm,
        poll_interval_sec=float(args.poll),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Helm agent against the live deployment.")
    parser.add_argument("--deployment", type=Path, default=None)
    parser.add_argument("--history", type=Path, default=None)
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--cycles", type=int, default=0, help="how many cycles to answer (0 = forever)")
    parser.add_argument("--poll", type=float, default=4.0, help="seconds between polls")
    parser.add_argument("--reconcile-wait", type=float, default=45.0)
    parser.add_argument("--lending-rate-bps", type=float, default=300.0)
    parser.add_argument("--min-fee-edge-bps", type=int, default=50)
    parser.add_argument("--no-llm", action="store_true", help="use the deterministic explanation only")
    parser.add_argument(
        "--llm-timeout",
        type=float,
        default=10.0,
        help="how long to wait for the paid explanation before answering with the template",
    )
    parser.add_argument(
        "--no-sync",
        action="store_true",
        help="use the cached market history instead of syncing it from Base mainnet",
    )
    parser.add_argument("--status", action="store_true", help="print what is deployed and exit")
    args = parser.parse_args(argv)

    deployment = Deployment.load(args.deployment) if args.deployment else Deployment.load()

    if args.status:
        print(json.dumps(deployment.to_json(), indent=2))
        return 0

    agent = build_agent(args)
    if args.ledger:
        agent.ledger_path = args.ledger
        agent.entries = load_ledger(args.ledger)

    print(
        f"helm agent running against vault {agent.vault} "
        f"(agent {deployment.agent}), enforcer {agent.reactive_address}",
        flush=True,
    )
    print(f"model {args.model or MODEL_DIR / 'model.npz'}, history {agent.history_path}", flush=True)

    try:
        agent.run(
            max_cycles=args.cycles,
            reconcile_wait=args.reconcile_wait,
            sync_history_each_cycle=not args.no_sync,
            llm_timeout_sec=args.llm_timeout,
        )
    except KeyboardInterrupt:
        print("\nstopped by the operator", flush=True)
    finally:
        print(f"\nledger: {agent.ledger_path} ({len(agent.entries)} cycles)", flush=True)
        for entry in agent.entries:
            chain = entry.get("chain") or {}
            evaluated = chain.get("evaluated") or {}
            rejected = chain.get("rejected") or {}
            rebalance = chain.get("rebalance") or {}
            proposal = entry.get("proposal") or {}
            verdict = (
                f"model {proposal.get('lpShareBps')} -> {evaluated.get('finalLpShareBps')} bps"
                if evaluated
                else (f"rejected (reason {rejected.get('reason')})" if rejected else "no verdict yet")
            )
            tx = (rebalance or {}).get("transactionHash") or (entry.get("posted") or {}).get("txHash") or ""
            print(f"  cycle {entry.get('cycleId')}: {verdict}  {tx}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
