"""The agent loop: watch for a cycle, answer it, post the proposal, record what happened.

The loop is deliberately boring. It polls the vault for `DecisionRequested`, answers every
cycle exactly once, and writes down everything it did and everything the chain did about
it. The ledger it writes is the evidence a judge can read: the model's own number, the
proposal that was posted, the transaction hash that posted it, the clamp the contract
applied, the transaction hash of the rebalance, and the latency between the three.

Two rules shape the code:

* **Answer once.** A cycle is answered once. If the agent crashes halfway through, it
  picks the cycle back up from the ledger instead of posting twice.
* **Never block the chain.** The agent's key can only post proposals. It cannot move
  money, it cannot widen the envelope and it cannot change the contract's settings, so a
  bug here can waste gas and nothing else.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from helm_agent import chain as chain_mod
from helm_agent import policy as policy_mod
from helm_agent.chain import ChainClient, DecisionRequest
from helm_agent.data import read_bars, sync_history
from helm_agent.features import FEATURE_NAMES, live_features
from helm_agent.llm import explain
from helm_agent.model import AllocationModel
from helm_agent.policy import Envelope, decide

LEDGER_DIR = Path(__file__).resolve().parents[1] / "ledger"
LEDGER_PATH = LEDGER_DIR / "cycles.jsonl"

# How far back the agent looks when it starts. Base Sepolia blocks are two seconds apart, so
# twenty thousand blocks is about eleven hours: long enough to catch a cycle that opened while
# the agent was starting, short enough for the node to answer in one call.
STARTUP_LOOKBACK_BLOCKS = 20_000

# How far back the agent looks on Lasna when it recovers an unfinished ledger entry. Lasna
# blocks are one second apart.
LASNA_LOOKBACK_BLOCKS = 25_000


def load_ledger(path: Path = LEDGER_PATH) -> list[dict]:
    """Every cycle the agent has already answered."""
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def append_ledger(entry: dict, path: Path = LEDGER_PATH) -> None:
    """Append one cycle to the ledger."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def rewrite_ledger(entries: list[dict], path: Path = LEDGER_PATH) -> None:
    """Replace the ledger with the given entries."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")


@dataclass
class Agent:
    """The running agent: one model, one chain, one ledger."""

    base: ChainClient
    reactive: ChainClient
    vault: str
    reactive_address: str
    model: AllocationModel
    feature_mean: list[float]
    feature_std: list[float]
    history_path: Path
    ledger_path: Path = LEDGER_PATH
    lending_rate_bps: float = 300.0
    min_fee_edge_bps: int = 50
    llm_enabled: bool = True
    poll_interval_sec: float = 4.0
    entries: list[dict] = field(default_factory=list)
    lasna_cursor: int = 0
    base_cursor: int = 0

    # ------------------------------------------------------------------------------------------
    # setup
    # ------------------------------------------------------------------------------------------
    @classmethod
    def load(cls, model_path: Path, history_path: Path, **kwargs) -> "Agent":
        model = AllocationModel.load(model_path)
        meta = json.loads(model_path.with_suffix(".json").read_text())
        agent = cls(
            base=kwargs.pop("base"),
            reactive=kwargs.pop("reactive"),
            vault=kwargs.pop("vault"),
            reactive_address=kwargs.pop("reactive_address"),
            model=model,
            feature_mean=list(meta["feature_mean"]),
            feature_std=list(meta["feature_std"]),
            history_path=history_path,
            **kwargs,
        )
        agent.entries = load_ledger(agent.ledger_path)
        return agent

    def answered_cycles(self) -> set[int]:
        return {int(entry["cycleId"]) for entry in self.entries}

    # ------------------------------------------------------------------------------------------
    # one cycle
    # ------------------------------------------------------------------------------------------
    def predict(self, history: list) -> dict:
        """Run the model on the newest bar of real market history."""
        row = live_features(history, self.feature_mean, self.feature_std, self.lending_rate_bps)
        raw = row * self.feature_std + self.feature_mean
        prediction = self.model.predict(row)[0]
        return {
            "allocation": float(prediction[0]),
            "forecastVolBps": float(prediction[1]),
            "forecastYieldBps": float(prediction[2]),
            "features": {name: float(value) for name, value in zip(FEATURE_NAMES, raw)},
            "historyBars": len(history),
            "lastBarTs": history[-1].timestamp,
        }

    def handle_cycle(self, request: DecisionRequest, history: list, llm_timeout_sec: float = 10.0) -> dict:
        """Answer one cycle: predict, explain, post, then read back what the chain did."""
        vault_state = chain_mod.read_vault_state(self.base, self.vault)
        reactive_state = chain_mod.read_reactive_state(self.reactive, self.reactive_address)

        envelope = Envelope.from_dict(vault_state.limits)
        envelope = Envelope(
            **{
                **{k: v for k, v in envelope.__dict__.items()},
                "min_fee_edge_bps": self.min_fee_edge_bps,
            }
        )

        prediction = self.predict(history)
        proposal = decide(
            cycle_id=request.cycle_id,
            model_allocation=prediction["allocation"],
            forecast_vol_bps=prediction["forecastVolBps"],
            forecast_yield_bps=prediction["forecastYieldBps"],
            envelope=envelope,
            current_lp_share_bps=reactive_state.current_lp_share_bps,
            lending_rate_bps=self.lending_rate_bps,
            chain_vol_bps=reactive_state.vol_bps,
            fee_edge_bps=reactive_state.fee_edge_bps,
            fee_edge_measured=reactive_state.fee_edge_measured,
        )

        context = {
            "limits": envelope.to_dict(),
            "rateBps": int(self.lending_rate_bps),
            "chainVolBps": reactive_state.vol_bps,
            "feeEdgeBps": reactive_state.fee_edge_bps,
            "feeEdgeMeasured": reactive_state.fee_edge_measured,
            "totalValueUsd": vault_state.total_value_usd,
            "currentLpShareBps": reactive_state.current_lp_share_bps,
        }
        fallback = proposal.rationale
        explanation = explain(
            proposal.to_json(),
            context,
            fallback_text=fallback,
            enabled=self.llm_enabled,
            timeout_sec=llm_timeout_sec,
        )
        if explanation.text:
            proposal.rationale = explanation.text

        posted_at = time.time()
        tx_hash = chain_mod.post_proposal(
            self.base,
            self.vault,
            proposal.cycle_id,
            proposal.lp_share_bps,
            proposal.range_width_bps,
            proposal.forecast_vol_bps,
            proposal.forecast_yield_bps,
        )

        entry = {
            "cycleId": request.cycle_id,
            "openedAt": request.requested_at,
            "decisionRequestTx": request.transaction_hash,
            "decisionRequestBlock": request.block_number,
            "market": {
                "priceE18": request.price_e18,
                "rateBps": request.rate_bps,
                "volBps": request.vol_bps,
                "currentLpShareBps": request.current_lp_share_bps,
                "totalValueUsd": request.total_value_usd,
            },
            "model": prediction,
            "proposal": proposal.to_json(),
            "explanation": explanation.to_json(),
            "posted": {
                "txHash": tx_hash,
                "at": posted_at,
                "agent": vault_state.agent,
            },
            "chain": {},
        }
        self.entries.append(entry)
        append_ledger(entry, self.ledger_path)
        return entry

    # ------------------------------------------------------------------------------------------
    # reconciliation
    # ------------------------------------------------------------------------------------------
    def reconcile(self, entry: dict, wait_sec: float = 45.0) -> dict:
        """Read back what the chain did with the proposal, and finish the ledger entry.

        The chain's verdict arrives on two chains: the enforcer answers on Lasna, and the
        vault executes on Base Sepolia. Both are read here, so the ledger ends up with the
        whole round trip in it rather than only the agent's half.
        """
        cycle_id = int(entry["cycleId"])
        deadline = time.time() + wait_sec

        evaluated = None
        rejected = None
        no_trade = None
        while (
            time.time() < deadline
            and evaluated is None
            and rejected is None
            and no_trade is None
        ):
            try:
                head = self.reactive.block_number()
                logs = self.reactive.get_logs(
                    self.reactive_address,
                    # One filter position, several alternatives: a bare list would be read as
                    # "topic0 is X *and* topic1 is Y", which never matches anything.
                    [[
                        chain_mod.PROPOSAL_EVALUATED_TOPIC,
                        chain_mod.PROPOSAL_REJECTED_TOPIC,
                        chain_mod.NO_TRADE_TOPIC,
                    ]],
                    max(0, self.lasna_cursor),
                    head,
                )
            except chain_mod.ChainError as exc:
                print(f"could not read the enforcer ({exc}); retrying", flush=True)
                time.sleep(2.0)
                continue
            self.lasna_cursor = head
            for log in logs:
                if log.topics[0] == chain_mod.PROPOSAL_EVALUATED_TOPIC and int(log.topics[1], 16) == cycle_id:
                    values = chain_mod.decode_uints(log.data, 6)
                    evaluated = {
                        "modelLpShareBps": values[0],
                        "finalLpShareBps": values[1],
                        "modelRangeWidthBps": values[2],
                        "finalRangeWidthBps": values[3],
                        "clampMask": values[4],
                        "evaluatedAt": values[5],
                        "txHash": log.transaction_hash,
                        "blockNumber": log.block_number,
                    }
                elif log.topics[0] == chain_mod.PROPOSAL_REJECTED_TOPIC and int(log.topics[1], 16) == cycle_id:
                    # `ProposalRejected(uint256 indexed cycleId, uint8 reason, address proposer)`
                    # has exactly one indexed parameter, so the cycle id is in topic 1 and
                    # *both* the reason and the proposer arrive in the data: the reason in
                    # the first word, the proposer in the second.
                    rejected = {
                        "reason": chain_mod.decode_uints(log.data, 1)[0],
                        "reasonName": policy_mod.reject_reason_name(
                            chain_mod.decode_uints(log.data, 1)[0]
                        ),
                        "proposer": chain_mod.decode_address_at(log.data, 1),
                        "txHash": log.transaction_hash,
                        "blockNumber": log.block_number,
                    }
                elif log.topics[0] == chain_mod.NO_TRADE_TOPIC and int(log.topics[1], 16) == cycle_id:
                    values = chain_mod.decode_uints(log.data, 3)
                    no_trade = {
                        "currentLpShareBps": values[0],
                        "targetLpShareBps": values[1],
                        "clampMask": values[2],
                        "txHash": log.transaction_hash,
                        "blockNumber": log.block_number,
                    }
            if evaluated is None and rejected is None and no_trade is None:
                time.sleep(2.0)

        # A cycle that was rejected or skipped has no rebalance coming, so waiting for one would
        # just burn the whole timeout. Only a cycle that actually moved has a rebalance to read.
        rebalance = None
        if evaluated is not None and rejected is None and no_trade is None:
            deadline = time.time() + wait_sec
            while time.time() < deadline and rebalance is None:
                try:
                    head = self.base.block_number()
                    items = chain_mod.read_rebalances(
                        self.base, self.vault, max(0, self.base_cursor), head
                    )
                except chain_mod.ChainError as exc:
                    print(f"could not read the vault ({exc}); retrying", flush=True)
                    time.sleep(2.0)
                    continue
                for item in items:
                    if item["cycleId"] == cycle_id:
                        rebalance = item
                        break
                self.base_cursor = head
                if rebalance is None:
                    time.sleep(2.0)

        entry["chain"] = {
            "evaluated": evaluated,
            "rejected": rejected,
            "noTrade": no_trade,
            "rebalance": rebalance,
        }

        opened_at = float(entry.get("openedAt") or 0)
        posted_at = float(entry.get("posted", {}).get("at") or 0)
        latency = {
            "openToPostMs": int((posted_at - opened_at) * 1000) if opened_at and posted_at else None,
        }
        if evaluated and evaluated.get("evaluatedAt"):
            latency["openToEvaluatedMs"] = int((float(evaluated["evaluatedAt"]) - opened_at) * 1000)
        entry["latency"] = latency

        self._rewrite()
        return entry

    def _rewrite(self) -> None:
        rewrite_ledger(self.entries, self.ledger_path)

    # ------------------------------------------------------------------------------------------
    # the loop
    # ------------------------------------------------------------------------------------------
    def run(
        self,
        max_cycles: int = 0,
        reconcile_wait: float = 45.0,
        sync_history_each_cycle: bool = True,
        llm_timeout_sec: float = 10.0,
    ) -> list[dict]:
        """Watch for cycles until `max_cycles` have been answered (0 means forever)."""
        history = self.refresh_history() if sync_history_each_cycle else read_bars(self.history_path)
        answered = self.answered_cycles()
        handled = 0
        # Start a little way back so a cycle that opened while the agent was starting up is
        # still picked up instead of being missed. Base Sepolia blocks are two seconds apart,
        # so this looks back about eleven hours.
        self.lasna_cursor = max(0, self._block_number(self.reactive, 500) - STARTUP_LOOKBACK_BLOCKS)
        self.base_cursor = max(0, self._block_number(self.base, 500) - STARTUP_LOOKBACK_BLOCKS)

        # A cycle the agent posted but never read the verdict of is still worth reading: the
        # chain's answer is on chain whether or not this process was awake to see it.
        self._recover_unreconciled(reconcile_wait)

        while max_cycles == 0 or handled < max_cycles:
            try:
                head = self.base.block_number()
                requests = chain_mod.read_decision_requests(self.base, self.vault, max(0, self.base_cursor), head)
                self.base_cursor = head
            except chain_mod.ChainError as exc:
                # A public node having a bad minute is not a reason to stop answering cycles.
                print(f"could not read the vault ({exc}); retrying", flush=True)
                time.sleep(self.poll_interval_sec)
                continue
            for request in requests:
                if request.cycle_id in answered:
                    continue
                if self._is_expired(request):
                    # The contract will refuse a proposal that arrives after its freshness
                    # window closed. Posting one anyway would only burn gas to prove a rule
                    # the chain already proved when it wrote the cycle off.
                    print(
                        f"cycle {request.cycle_id}: skipped, the freshness window closed "
                        f"{(int(time.time()) - request.requested_at)}s ago",
                        flush=True,
                    )
                    answered.add(request.cycle_id)
                    continue
                print(
                    f"cycle {request.cycle_id}: answering (model says "
                    f"{self.predict(history)['allocation']:.3f} LP)",
                    flush=True,
                )
                try:
                    entry = self.handle_cycle(request, history, llm_timeout_sec=llm_timeout_sec)
                except chain_mod.ChainError as exc:
                    # One failed chain read must not end the process. The live agent died once
                    # on a Lasna TLS drop in the middle of a cycle; the contract wrote that
                    # cycle off on its own, which is the safe outcome, but there is no reason
                    # for the agent to stop answering every cycle after it.
                    print(f"cycle {request.cycle_id}: chain read failed ({exc}); carrying on", flush=True)
                    time.sleep(self.poll_interval_sec)
                    continue
                answered.add(request.cycle_id)
                handled += 1
                self.reconcile(entry, wait_sec=reconcile_wait)
                if sync_history_each_cycle:
                    history = self.refresh_history()
                if max_cycles and handled >= max_cycles:
                    break
            time.sleep(self.poll_interval_sec)
        return self.entries

    def _is_expired(self, request: DecisionRequest) -> bool:
        """Whether the contract's freshness window for this cycle has already closed."""
        try:
            limits = chain_mod.read_vault_state(self.base, self.vault).limits
        except chain_mod.ChainError:
            return False
        freshness = int(limits.get("freshnessSec", 600))
        return int(time.time()) - request.requested_at > freshness

    def _recover_unreconciled(self, reconcile_wait: float) -> None:
        """Read back the chain's verdict for cycles this agent posted but never resolved.

        The ledger is written when the proposal goes out, before the chain has answered. If the
        agent is restarted between those two moments, the entry is left half-finished. The
        answer is on chain either way, so the agent goes and reads it.
        """
        pending = [
            entry
            for entry in self.entries
            if not (
                (entry.get("chain") or {}).get("evaluated")
                or (entry.get("chain") or {}).get("rejected")
                or (entry.get("chain") or {}).get("noTrade")
            )
        ]
        if not pending:
            return
        oldest = min(int(entry.get("decisionRequestBlock", 0)) for entry in pending)
        self.base_cursor = max(0, oldest - 10)
        self.lasna_cursor = max(0, self._block_number(self.reactive, 500) - LASNA_LOOKBACK_BLOCKS)
        for entry in pending:
            print(f"cycle {entry['cycleId']}: recovering the chain's verdict", flush=True)
            self.reconcile(entry, wait_sec=reconcile_wait)

    @staticmethod
    def _block_number(client: ChainClient, fallback: int = 0) -> int:
        """The head of a chain, or a fallback when the node is having a bad minute."""
        try:
            return client.block_number()
        except chain_mod.ChainError:
            return fallback

    def refresh_history(self) -> list:
        """Bring the real market history up to date and return it."""
        try:
            sync_history(self.history_path)
        except Exception as exc:  # noqa: BLE001 - a network problem must not kill the agent
            print(f"history sync failed ({exc}); using the cached history", flush=True)
        return read_bars(self.history_path)
