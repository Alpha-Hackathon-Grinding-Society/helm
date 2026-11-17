"""A very small on-chain client for the Helm agent.

The agent needs exactly four things from the chain: read the vault's approved limits, read
the reactive contract's state, notice when a cycle was opened, and post one proposal. That
is a small enough surface to write directly against JSON-RPC instead of pulling in a web3
library, and it keeps the dependency list to `eth-account` (for signing) and the standard
library.

Everything here is deliberately dumb: it encodes and decodes the handful of solidity types
the Helm contracts use, and it refuses to guess. A silent default that points at the wrong
contract is worse than a loud failure, so every address has to be given explicitly.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from helm_agent.keccak import event_topic, selector

# Event signatures the agent reads.
DECISION_REQUESTED_TOPIC = event_topic(
    "DecisionRequested(uint256,uint256,uint256,uint256,uint256,uint256,uint256)"
)
PROPOSAL_POSTED_TOPIC = event_topic(
    "ProposalPosted(address,uint256,uint256,uint256,uint256,uint256,uint256)"
)
REBALANCED_TOPIC = event_topic(
    "Rebalanced(uint256,uint256,uint256,uint256,uint256,uint8,uint8)"
)

# The enforcer's events, read off Lasna.
CYCLE_OPENED_TOPIC = event_topic("CycleOpened(uint256,uint256,uint256,uint256,uint256)")
CYCLE_EXPIRED_TOPIC = event_topic("CycleExpired(uint256,uint256)")
PROPOSAL_EVALUATED_TOPIC = event_topic(
    "ProposalEvaluated(uint256,uint256,uint256,uint256,uint256,uint8,uint256)"
)
REBALANCE_REQUESTED_TOPIC = event_topic(
    "RebalanceRequested(uint256,uint256,uint256,uint8,uint8,uint256)"
)
PROPOSAL_REJECTED_TOPIC = event_topic("ProposalRejected(uint256,uint8,address)")
NO_TRADE_TOPIC = event_topic("NoTrade(uint256,uint256,uint256,uint8)")
AUTONOMOUS_EXIT_TOPIC = event_topic("AutonomousExit(uint256,uint256,uint256,uint256)")
FORECAST_GRADED_TOPIC = event_topic("ForecastGraded(uint256,uint256,uint256,uint256,uint256)")
MARKET_OBSERVED_TOPIC = event_topic("MarketObserved(uint256,uint256,uint256,uint256)")


class ChainError(RuntimeError):
    """The chain refused a request or the answer could not be understood."""


def rpc_call(
    method: str,
    params: list,
    url: str,
    retries: int = 4,
    timeout: float = 45.0,
) -> Any:
    """One JSON-RPC call, with a backoff for the rate limits public nodes impose."""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last: Exception | None = None
    for attempt in range(retries):
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "User-Agent": "helm-agent/0.1"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read())
            if "error" in payload:
                raise ChainError(str(payload["error"]))
            return payload["result"]
        except (urllib.error.URLError, urllib.error.HTTPError, ChainError, TimeoutError, OSError) as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise ChainError(f"{method} failed after {retries} attempts: {last}")


# ---------------------------------------------------------------------------------------------
# ABI helpers. Only the static types the Helm contracts use are supported, on purpose.
# ---------------------------------------------------------------------------------------------


def encode_uint(value: int) -> str:
    """One `uint256` as 32 bytes of hex."""
    if value < 0 or value >= 1 << 256:
        raise ValueError(f"value out of range for uint256: {value}")
    return f"{value:064x}"


def encode_uints(values: Iterable[int]) -> str:
    """A list of `uint256` as 32-byte words."""
    return "".join(encode_uint(int(value)) for value in values)


def decode_uints(data: str, count: int) -> list[int]:
    """Read `count` `uint256` words out of a hex string."""
    raw = data[2:] if data.startswith("0x") else data
    if len(raw) < count * 64:
        raise ChainError(f"expected {count} words, got {len(raw) // 64}")
    return [int(raw[i * 64 : (i + 1) * 64], 16) for i in range(count)]


def decode_bool(data: str) -> bool:
    raw = data[2:] if data.startswith("0x") else data
    if not raw:
        raise ChainError("empty return data")
    return int(raw[-64:], 16) != 0


def decode_address(data: str) -> str:
    raw = data[2:] if data.startswith("0x") else data
    if len(raw) < 64:
        raise ChainError("short return data")
    return "0x" + raw[-40:].lower()


def decode_address_at(data: str, index: int) -> str:
    """Read the `index`-th word of `data` as an address.

    Solidity packs an `address` into one 32-byte word, left-padded with zeros, so the
    address is the last twenty bytes of that word.
    """
    raw = data[2:] if data.startswith("0x") else data
    start = index * 64
    if len(raw) < start + 64:
        raise ChainError(f"expected {index + 1} words, got {len(raw) // 64}")
    return "0x" + raw[start + 24 : start + 64].lower()


def call_data(function_signature: str, args: Sequence[int] = ()) -> str:
    """Calldata for a solidity function whose arguments are all `uint256`."""
    return selector(function_signature) + encode_uints(args)


@dataclass
class Log:
    """One event log, decoded far enough for the agent to use it."""

    address: str
    topics: list[str]
    data: str
    block_number: int
    transaction_hash: str
    log_index: int


@dataclass
class ChainClient:
    """JSON-RPC access to one chain, with transaction sending."""

    rpc_url: str
    chain_id: int
    private_key: str = ""
    from_address: str = ""

    def call(self, to: str, data: str, block: str = "latest") -> str:
        result = rpc_call("eth_call", [{"to": to, "data": data}, block], self.rpc_url)
        return result if isinstance(result, str) else "0x"

    def call_uint(self, to: str, function_signature: str, args: Sequence[int] = ()) -> int:
        data = self.call(to, call_data(function_signature, args))
        return decode_uints(data, 1)[0]

    def call_uints(self, to: str, function_signature: str, count: int, args: Sequence[int] = ()) -> list[int]:
        data = self.call(to, call_data(function_signature, args))
        return decode_uints(data, count)

    def call_bool(self, to: str, function_signature: str, args: Sequence[int] = ()) -> bool:
        data = self.call(to, call_data(function_signature, args))
        return decode_bool(data)

    def call_address(self, to: str, function_signature: str, args: Sequence[int] = ()) -> str:
        data = self.call(to, call_data(function_signature, args))
        return decode_address(data)

    def block_number(self) -> int:
        return int(rpc_call("eth_blockNumber", [], self.rpc_url), 16)

    def block_timestamp(self, block_number: int) -> int | None:
        """The timestamp of a block, or `None` if the node will not say."""
        raw = rpc_call("eth_getBlockByNumber", [hex(block_number), False], self.rpc_url)
        if not isinstance(raw, dict) or "timestamp" not in raw:
            return None
        return int(raw["timestamp"], 16)

    def get_logs(
        self,
        address: str,
        topics: list[str | list[str] | None],
        from_block: int,
        to_block: int,
        max_range: int = 25_000,
    ) -> list[Log]:
        """Every log of a contract between two blocks, decoded into `Log` objects.

        Public nodes cap how many blocks one `eth_getLogs` may span — Lasna refuses
        anything over thirty thousand — so a wide window is read in slices and the slices
        are stitched back together. One wide request that the node refuses is a silent
        dead end; slices are not.
        """
        logs: list[Log] = []
        start = from_block
        while start <= to_block:
            end = min(start + max_range - 1, to_block)
            raw = rpc_call(
                "eth_getLogs",
                [
                    {
                        "fromBlock": hex(start),
                        "toBlock": hex(end),
                        "address": address,
                        "topics": topics,
                    }
                ],
                self.rpc_url,
            )
            for entry in raw:
                logs.append(
                    Log(
                        address=entry["address"].lower(),
                        topics=[topic.lower() for topic in entry["topics"]],
                        data=entry["data"],
                        block_number=int(entry["blockNumber"], 16),
                        transaction_hash=entry["transactionHash"],
                        log_index=int(entry["logIndex"], 16),
                    )
                )
            if end >= to_block:
                break
            start = end + 1
        return logs

    # ------------------------------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------------------------------
    def send_transaction(
        self,
        to: str,
        data: str,
        value: int = 0,
        gas: int | None = None,
    ) -> str:
        """Sign and send one transaction. Returns the transaction hash."""
        if not self.private_key or not self.from_address:
            raise ChainError("no signing key configured")

        from eth_account import Account

        account = Account.from_key(self.private_key)
        nonce = int(rpc_call("eth_getTransactionCount", [self.from_address, "pending"], self.rpc_url), 16)
        if gas is None:
            gas = int(
                rpc_call(
                    "eth_estimateGas",
                    [{"from": self.from_address, "to": to, "data": data, "value": hex(value)}],
                    self.rpc_url,
                ),
                16,
            )
            gas = int(gas * 1.4) + 20_000
        gas_price = int(rpc_call("eth_gasPrice", [], self.rpc_url), 16)

        transaction = {
            "from": self.from_address,
            "to": to,
            "data": data,
            "value": value,
            "gas": gas,
            "gasPrice": gas_price,
            "nonce": nonce,
            "chainId": self.chain_id,
        }
        signed = account.sign_transaction(transaction)
        raw = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction")
        return rpc_call("eth_sendRawTransaction", [raw.hex()], self.rpc_url)

    def wait_for_receipt(self, tx_hash: str, timeout_sec: float = 120.0) -> dict:
        """Poll for a transaction receipt until it shows up."""
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            receipt = rpc_call("eth_getTransactionReceipt", [tx_hash], self.rpc_url)
            if receipt:
                return receipt
            time.sleep(2.0)
        raise ChainError(f"no receipt for {tx_hash} after {timeout_sec:.0f}s")


@dataclass
class VaultState:
    """Everything the agent reads from the vault before it decides."""

    address: str
    owner: str
    agent: str
    paused: bool
    limits_set: bool
    total_value_usd: int
    lp_share_bps: int
    lending_share_bps: int
    current_lp_share_bps: int
    current_range_width_bps: int
    last_requested_cycle_id: int
    last_executed_cycle_id: int
    price_e18: int
    rate_bps: int
    limits: dict[str, int] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "address": self.address,
            "owner": self.owner,
            "agent": self.agent,
            "paused": self.paused,
            "limitsSet": self.limits_set,
            "totalValueUsd": self.total_value_usd,
            "lpShareBps": self.lp_share_bps,
            "lendingShareBps": self.lending_share_bps,
            "currentLpShareBps": self.current_lp_share_bps,
            "currentRangeWidthBps": self.current_range_width_bps,
            "lastRequestedCycleId": self.last_requested_cycle_id,
            "lastExecutedCycleId": self.last_executed_cycle_id,
            "priceE18": self.price_e18,
            "rateBps": self.rate_bps,
            "limits": self.limits,
        }


LIMIT_KEYS = (
    "lpShareMinBps",
    "lpShareMaxBps",
    "rangeWidthMinBps",
    "rangeWidthMaxBps",
    "cooldownSec",
    "volExitLevelBps",
    "minTradeBps",
    "freshnessSec",
)


def read_vault_state(client: ChainClient, vault: str) -> VaultState:
    """Read the vault's state in one pass over the chain."""
    limits_values = client.call_uints(vault, "limits()", 8)
    limits = dict(zip(LIMIT_KEYS, limits_values))
    return VaultState(
        address=vault.lower(),
        owner=client.call_address(vault, "owner()"),
        agent=client.call_address(vault, "agent()"),
        paused=client.call_bool(vault, "paused()"),
        limits_set=client.call_bool(vault, "limitsSet()"),
        total_value_usd=client.call_uint(vault, "totalValueUsd()"),
        lp_share_bps=client.call_uint(vault, "lpShareBps()"),
        lending_share_bps=client.call_uint(vault, "lendingShareBps()"),
        current_lp_share_bps=client.call_uint(vault, "currentLpShareBps()"),
        current_range_width_bps=client.call_uint(vault, "currentRangeWidthBps()"),
        last_requested_cycle_id=client.call_uint(vault, "lastRequestedCycleId()"),
        last_executed_cycle_id=client.call_uint(vault, "lastExecutedCycleId()"),
        price_e18=client.call_uint(vault, "priceE18()"),
        rate_bps=client.call_uint(vault, "rateBps()"),
        limits=limits,
    )


@dataclass
class ReactiveState:
    """Everything the agent reads from the reactive contract."""

    address: str
    cycle_id: int
    pending_cycle_id: int
    current_lp_share_bps: int
    vol_bps: int
    rate_bps: int
    fee_apr_bps: int
    last_executed_cycle_id: int
    graded_forecasts: int
    limits_set: bool
    paused: bool
    fee_edge_measured: bool
    fee_edge_bps: int

    def to_json(self) -> dict:
        return {
            "address": self.address,
            "cycleId": self.cycle_id,
            "pendingCycleId": self.pending_cycle_id,
            "currentLpShareBps": self.current_lp_share_bps,
            "volBps": self.vol_bps,
            "rateBps": self.rate_bps,
            "feeAprBps": self.fee_apr_bps,
            "lastExecutedCycleId": self.last_executed_cycle_id,
            "gradedForecasts": self.graded_forecasts,
            "limitsSet": self.limits_set,
            "paused": self.paused,
            "feeEdgeMeasured": self.fee_edge_measured,
            "feeEdgeBps": self.fee_edge_bps,
        }


def read_reactive_state(client: ChainClient, reactive: str) -> ReactiveState:
    """Read the reactive contract's state.

    `state()` returns ten words: eight unsigned integers and two booleans, which are
    encoded as ordinary words.
    """
    values = client.call_uints(reactive, "state()", 10)
    return ReactiveState(
        address=reactive.lower(),
        cycle_id=values[0],
        pending_cycle_id=values[1],
        current_lp_share_bps=values[2],
        vol_bps=values[3],
        rate_bps=values[4],
        fee_apr_bps=values[5],
        last_executed_cycle_id=values[6],
        graded_forecasts=values[7],
        limits_set=values[8] != 0,
        paused=values[9] != 0,
        fee_edge_measured=client.call_bool(reactive, "feeEdgeMeasured()"),
        fee_edge_bps=client.call_uint(reactive, "feeEdgeBps()"),
    )


def post_proposal(
    client: ChainClient,
    vault: str,
    cycle_id: int,
    lp_share_bps: int,
    range_width_bps: int,
    forecast_vol_bps: int,
    forecast_yield_bps: int,
) -> str:
    """Post one proposal to the vault. Returns the transaction hash.

    This is the only thing the agent key is allowed to do. The function encodes the call
    itself rather than using an ABI library, because there is exactly one call and it has
    five unsigned arguments.
    """
    data = selector("postProposal(uint256,uint256,uint256,uint256,uint256)") + encode_uints(
        [
            cycle_id,
            lp_share_bps,
            range_width_bps,
            forecast_vol_bps,
            forecast_yield_bps,
        ]
    )
    return client.send_transaction(vault, data)


@dataclass
class DecisionRequest:
    """A cycle the vault is asking about."""

    cycle_id: int
    price_e18: int
    rate_bps: int
    vol_bps: int
    current_lp_share_bps: int
    total_value_usd: int
    requested_at: int
    block_number: int
    transaction_hash: str

    def to_json(self) -> dict:
        return {
            "cycleId": self.cycle_id,
            "priceE18": self.price_e18,
            "rateBps": self.rate_bps,
            "volBps": self.vol_bps,
            "currentLpShareBps": self.current_lp_share_bps,
            "totalValueUsd": self.total_value_usd,
            "requestedAt": self.requested_at,
            "blockNumber": self.block_number,
            "transactionHash": self.transaction_hash,
        }


def read_decision_requests(client: ChainClient, vault: str, from_block: int, to_block: int) -> list[DecisionRequest]:
    """Every `DecisionRequested` event the vault emitted between two blocks.

    `cycleId` is an indexed parameter, so it arrives in topic 1 and not in the data. The
    data carries the six values that are not indexed.
    """
    logs = client.get_logs(vault, [DECISION_REQUESTED_TOPIC], from_block, to_block)
    requests: list[DecisionRequest] = []
    for log in logs:
        values = decode_uints(log.data, 6)
        requests.append(
            DecisionRequest(
                cycle_id=int(log.topics[1], 16),
                price_e18=values[0],
                rate_bps=values[1],
                vol_bps=values[2],
                current_lp_share_bps=values[3],
                total_value_usd=values[4],
                requested_at=values[5],
                block_number=log.block_number,
                transaction_hash=log.transaction_hash,
            )
        )
    return requests


def read_proposal_posts(client: ChainClient, vault: str, from_block: int, to_block: int) -> list[dict]:
    """Every `ProposalPosted` event the vault emitted between two blocks."""
    logs = client.get_logs(vault, [PROPOSAL_POSTED_TOPIC], from_block, to_block)
    posts: list[dict] = []
    for log in logs:
        values = decode_uints(log.data, 5)
        posts.append(
            {
                "proposer": "0x" + log.topics[1][-40:],
                "cycleId": int(log.topics[2], 16),
                "lpShareBps": values[0],
                "rangeWidthBps": values[1],
                "forecastVolBps": values[2],
                "forecastYieldBps": values[3],
                "proposedAt": values[4],
                "blockNumber": log.block_number,
                "transactionHash": log.transaction_hash,
            }
        )
    return posts


def read_rebalances(client: ChainClient, vault: str, from_block: int, to_block: int) -> list[dict]:
    """Every `Rebalanced` event the vault emitted between two blocks.

    `cycleId` is indexed, so it arrives in topic 1 and the data carries the six values that
    are not indexed.
    """
    logs = client.get_logs(vault, [REBALANCED_TOPIC], from_block, to_block)
    rebalances: list[dict] = []
    for log in logs:
        values = decode_uints(log.data, 6)
        rebalances.append(
            {
                "cycleId": int(log.topics[1], 16),
                "lpShareBps": values[0],
                "rangeWidthBps": values[1],
                "lpValueUsd": values[2],
                "totalValueUsd": values[3],
                "action": values[4],
                "clampMask": values[5],
                "blockNumber": log.block_number,
                "transactionHash": log.transaction_hash,
            }
        )
    return rebalances
