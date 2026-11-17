"""Real Base mainnet market history.

Helm's quantitative claims have to rest on something real, so this module pulls the
actual swap history of the Uniswap v3 ETH/USDC pool on Base mainnet and caches it on
disk. Nothing here is simulated: the prices, the volumes and the fees all come out of
`Swap` events emitted by the pool at a specific block.

The pool
--------
`POOL_CANDIDATES` lists the Uniswap v3 ETH/USDC pools on Base. `resolve_pool` asks the
chain which one it is looking at: token0, token1, the decimals and the fee tier, and it
verifies that the quote token really is USDC. The pool with the deepest liquidity is
chosen, because that is the pool a real position would sit in.

The cache
---------
`cache_path` holds a JSON Lines file with one row per hourly bar. Fetching is chunked
because a public archive node will not serve a multi-million block range in one call,
and it is resumable: a run that is interrupted keeps whatever it already downloaded.
"""
from __future__ import annotations

import json
import math
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

# Base mainnet. Public archive nodes serve the swap logs, but every free tier caps how wide
# a log range may be and how far back its archive window reaches. The fetcher therefore
# starts wide, shrinks the range when a node complains about it, and asks each node for
# its own archive boundary.
BASE_MAINNET_RPC = "https://base-rpc.publicnode.com"
BASE_MAINNET_RPC_FALLBACKS = (
    "https://base.gateway.tenderly.co",
    "https://base.drpc.org",
    "https://mainnet.base.org",
)
MAX_LOG_CHUNK = 20_000
MIN_LOG_CHUNK = 1_000

# Uniswap v3 ETH/USDC pools on Base mainnet, most liquid first. The 0.05% pool is the one
# a real position would sit in, and it is also the one with the longest history.
POOL_CANDIDATES = (
    "0xd0b53D9277642d899DF5C87A3966A349A798F224",  # 0.05% - the deep ETH/USDC pool
    "0x6c561B446416E1A00E8E93E221854d6eA4171372",  # 0.30%
    "0xb4CB800910B228ED3d0834cF79D697127BBB00e5",  # 0.01%
)

USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
WETH = "0x4200000000000000000000000000000000000006"

SWAP_TOPIC = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"

# Base's block time is measured from the chain rather than assumed, because the range a
# node serves and the amount of history a number of days means both depend on it.
BASE_BLOCK_TIME_SEC = 0.2


class RpcError(RuntimeError):
    """The node refused or failed a request."""


def rpc_call(method: str, params: list, url: str = BASE_MAINNET_RPC, retries: int = 4) -> dict:
    """One JSON-RPC call, with a backoff for the rate limits public nodes impose.

    The call is tried against the primary node first and then against the fallbacks, so a
    node that is rate limiting does not fail the download on its own.
    """
    candidates = [url] + [candidate for candidate in BASE_MAINNET_RPC_FALLBACKS if candidate != url]
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last: Exception | None = None
    for attempt in range(retries):
        for candidate in candidates:
            request = urllib.request.Request(
                candidate,
                data=body,
                headers={"Content-Type": "application/json", "User-Agent": "helm-agent/0.1"},
            )
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    payload = json.loads(response.read())
                if "error" in payload:
                    raise RpcError(str(payload["error"]))
                return payload["result"]
            except (urllib.error.URLError, urllib.error.HTTPError, RpcError, TimeoutError, OSError) as exc:
                last = exc
                continue
        time.sleep(1.5 * (attempt + 1))
    raise RpcError(f"{method} failed after {retries} attempts: {last}")


def _eth_call(to: str, data: str, url: str = BASE_MAINNET_RPC) -> str:
    return rpc_call("eth_call", [{"to": to, "data": data}, "latest"], url=url)


def _keccak_selector(signature: str) -> str:
    """keccak256 of a function signature, first four bytes.

    `eth_hash` (installed with `eth-account`) is preferred; the pure-python Keccak in
    `helm_agent.keccak` is the fallback, so the agent never needs a native extension.
    """
    try:
        from eth_hash.auto import keccak

        return "0x" + keccak(signature.encode()).hex()[:8]
    except Exception:  # noqa: BLE001 - any import problem falls back
        from helm_agent.keccak import selector

        return selector(signature)


@dataclass(frozen=True)
class PoolInfo:
    """What the pool actually is, read from the chain."""

    address: str
    token0: str
    token1: str
    decimals0: int
    decimals1: int
    fee_bps: int  # fee tier in basis points: 500 -> 0.05%

    @property
    def usdc_is_token0(self) -> bool:
        return self.token0.lower() == USDC.lower()


def resolve_pool(candidates: Sequence[str] = POOL_CANDIDATES, url: str = BASE_MAINNET_RPC) -> PoolInfo:
    """Identify the ETH/USDC pool and read its parameters from the chain.

    Raises if none of the candidates is a Uniswap v3 pool quoted in USDC.
    """
    for address in candidates:
        try:
            token0 = _eth_call(address, _keccak_selector("token0()"), url)
            token1 = _eth_call(address, _keccak_selector("token1()"), url)
            fee = _eth_call(address, _keccak_selector("fee()"), url)
        except RpcError:
            continue
        token0 = "0x" + token0[-40:]
        token1 = "0x" + token1[-40:]
        if {token0.lower(), token1.lower()} != {USDC.lower(), WETH.lower()}:
            continue
        decimals0 = int(_eth_call(token0, _keccak_selector("decimals()"), url), 16)
        decimals1 = int(_eth_call(token1, _keccak_selector("decimals()"), url), 16)
        fee_bps = int(fee, 16) // 100  # Uniswap charges in hundredths of a bip
        return PoolInfo(
            address=address,
            token0=token0,
            token1=token1,
            decimals0=decimals0,
            decimals1=decimals1,
            fee_bps=fee_bps,
        )
    raise RpcError("no Uniswap v3 ETH/USDC pool on Base could be identified")


def get_block_number(url: str = BASE_MAINNET_RPC) -> int:
    return int(rpc_call("eth_blockNumber", [], url=url), 16)


def get_block_timestamp(block: int, url: str = BASE_MAINNET_RPC) -> int:
    block_obj = rpc_call("eth_getBlockByNumber", [hex(block), False], url=url)
    return int(block_obj["timestamp"], 16)


def measure_block_time(url: str = BASE_MAINNET_RPC, sample_blocks: int = 20_000) -> float:
    """How many seconds a block takes, right now, read from the chain.

    This is measured rather than assumed. Base's block time has changed over its life,
    and a history download that assumes the wrong one asks for the wrong range: it either
    fetches a fraction of the window it was asked for, or it asks for more than the chain
    has.
    """
    latest = get_block_number(url)
    if latest <= sample_blocks:
        return BASE_BLOCK_TIME_SEC
    older = max(0, latest - sample_blocks)
    span = get_block_timestamp(latest, url) - get_block_timestamp(older, url)
    if span <= 0:
        return BASE_BLOCK_TIME_SEC
    return span / (latest - older)


class BlockClock:
    """Maps block numbers to timestamps, piecewise.

    Base did not produce blocks at a constant rate for its whole life: it ran at two
    seconds a block for most of its history and now runs at 0.2 seconds. Interpolating
    timestamps linearly across a window that spans that change puts every swap in the
    wrong bar, which is enough to make a fee yield wrong by a factor of ten.

    So the clock asks the chain for a handful of anchor points and interpolates between
    them. Inside one segment the block time is constant to within a second, which is
    finer than the bar size.
    """

    def __init__(self, anchors: list[tuple[int, int]]) -> None:
        if not anchors:
            raise ValueError("a clock needs at least one anchor")
        self.anchors = sorted(anchors)

    @classmethod
    def build(cls, from_block: int, to_block: int, url: str = BASE_MAINNET_RPC, segments: int = 12) -> "BlockClock":
        """Ask the chain for anchor points spread evenly across the window."""
        if to_block <= from_block:
            return cls([(from_block, get_block_timestamp(from_block, url))])
        step = max(1, (to_block - from_block) // max(1, segments))
        anchors: list[tuple[int, int]] = []
        block = from_block
        while block <= to_block:
            anchors.append((block, get_block_timestamp(block, url)))
            block += step
        anchors.append((to_block, get_block_timestamp(to_block, url)))
        # dedupe, keeping the last anchor for each block
        unique: dict[int, int] = {}
        for block_number, timestamp in anchors:
            unique[block_number] = timestamp
        return cls(sorted(unique.items()))

    def timestamp(self, block: int) -> int:
        """The timestamp of a block, to the second."""
        anchors = self.anchors
        if block <= anchors[0][0]:
            return anchors[0][1]
        if block >= anchors[-1][0]:
            return anchors[-1][1]
        low, high = 0, len(anchors) - 1
        while high - low > 1:
            middle = (low + high) // 2
            if anchors[middle][0] <= block:
                low = middle
            else:
                high = middle
        (b0, t0), (b1, t1) = anchors[low], anchors[high]
        if b1 == b0:
            return t0
        return int(t0 + (t1 - t0) * (block - b0) / (b1 - b0))

    def span_seconds(self) -> int:
        return self.anchors[-1][1] - self.anchors[0][1]


def max_range_for(pool: str, url: str, start: int, ceiling: int = MAX_LOG_CHUNK) -> int:
    """The widest log range this node will serve, found by halving until it agrees.

    The free tiers all cap the range differently, and the cap is not documented
    consistently, so it is measured: try the widest range, and if the node refuses it
    for being too wide, halve and try again.
    """
    span = ceiling
    while span >= MIN_LOG_CHUNK:
        try:
            raw_rpc_call(
                "eth_getLogs",
                [
                    {
                        "fromBlock": hex(start),
                        "toBlock": hex(start + span),
                        "address": pool,
                        "topics": [SWAP_TOPIC],
                    }
                ],
                url=url,
            )
            return span
        except RpcError as exc:
            if classify_rpc_error(exc) == "too_wide":
                span //= 2
                continue
            return span
    return MIN_LOG_CHUNK


def fetch_swap_logs(
    pool: str,
    from_block: int,
    to_block: int,
    chunk_size: int = MAX_LOG_CHUNK,
    url: str = BASE_MAINNET_RPC,
    progress: bool = True,
    nodes: Sequence[str] | None = None,
    workers: int = 6,
) -> Iterator[dict]:
    """Yield every `Swap` log the pool emitted between two blocks.

    The range is walked in chunks because public archive nodes refuse very wide ranges.
    The widest range the node will serve is measured first, so the walk does not have to
    discover the limit by failing at it.

    Each chunk is tried against the nodes in turn. A node whose archive window does not
    reach the chunk is skipped for that chunk, so one node's window never stops the
    download when another node can still serve the range.

    The chunks are fetched by a small pool of threads, because the nodes are network
    services rather than CPUs and the work is almost entirely waiting. A chunk that gets
    rate limited is put back on the queue rather than failing the download: the public
    nodes throttle hard, and the download has to survive that.
    """
    candidates = [url] + [n for n in (nodes or BASE_MAINNET_RPC_FALLBACKS) if n != url]
    chunk_size = max(MIN_LOG_CHUNK, min(chunk_size, max_range_for(pool, url, from_block)))

    ranges: list[tuple[int, int]] = []
    block = from_block
    while block <= to_block:
        end = min(block + chunk_size - 1, to_block)
        ranges.append((block, end))
        block = end + 1

    def fetch_one(bounds: tuple[int, int]) -> list[dict]:
        start, end = bounds
        last_error = ""
        for candidate in candidates:
            try:
                return raw_rpc_call(
                    "eth_getLogs",
                    [
                        {
                            "fromBlock": hex(start),
                            "toBlock": hex(end),
                            "address": pool,
                            "topics": [SWAP_TOPIC],
                        }
                    ],
                    url=candidate,
                )
            except RpcError as exc:
                last_error = str(exc)
                if classify_rpc_error(exc) == "too_old":
                    continue
        raise RpcError(f"no node served blocks {start}..{end}: {last_error}")

    pending = list(ranges)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        in_flight: dict = {}
        while pending or in_flight:
            while pending and len(in_flight) < workers:
                bounds = pending.pop(0)
                in_flight[executor.submit(fetch_one, bounds)] = bounds
            time.sleep(0.5)
            done = [future for future in in_flight if future.done()]
            for future in done:
                bounds = in_flight.pop(future)
                try:
                    logs = future.result()
                except RpcError as exc:
                    # the node is throttling: wait and try this range again
                    print(f"    chunk {bounds[0]}..{bounds[1]} failed ({exc}); retrying", flush=True)
                    time.sleep(5.0)
                    pending.insert(0, bounds)
                    continue
                for log in logs:
                    yield log
                if progress:
                    print(
                        f"    scanned blocks {bounds[0]}..{bounds[1]} ({len(logs)} swaps)",
                        flush=True,
                    )


def decode_swap(log: dict, pool: PoolInfo) -> tuple[float, float, float, float, float]:
    """Decode one `Swap` log into (price, volume USD, fees USD, pool liquidity, pool TVL USD).

    The event data is `(int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick)`.
    The price comes out of the pool's own square-root price, which is the authoritative
    price of the pool at that moment, not an estimate.

    The pool's liquidity and its virtual reserves are decoded from the same event, so the
    fee income a position earns can be computed against the pool's real depth rather than
    against an assumed one.
    """
    data = log["data"][2:]
    amount0 = int.from_bytes(bytes.fromhex(data[0:64]), "big", signed=True)
    amount1 = int.from_bytes(bytes.fromhex(data[64:128]), "big", signed=True)
    sqrt_price_x96 = int.from_bytes(bytes.fromhex(data[128:192]), "big")

    ratio = (sqrt_price_x96 / (2**96)) ** 2  # token1 per token1 in raw units
    # Convert the raw ratio into human units: raw_ratio * 10^(dec0 - dec1)
    price = ratio * (10 ** (pool.decimals0 - pool.decimals1))

    amount0_abs = abs(amount0) / (10**pool.decimals0)
    amount1_abs = abs(amount1) / (10**pool.decimals1)

    # Volume in USD: the USDC side of the swap, when there is one.
    if pool.usdc_is_token0:
        volume_usd = amount0_abs
    else:
        volume_usd = amount1_abs
    fees_usd = volume_usd * pool.fee_bps / 10_000

    # Virtual reserves from the pool's own liquidity: x = L / sqrt(P), y = L * sqrt(P).
    sqrt_price = sqrt_price_x96 / (2**96)
    liquidity = int.from_bytes(bytes.fromhex(data[192:256]), "big")
    reserve0 = liquidity / sqrt_price if sqrt_price > 0 else 0.0
    reserve1 = liquidity * sqrt_price
    tvl_usd = reserve1 / (10**pool.decimals1) + (reserve0 / (10**pool.decimals0)) * price

    return price, volume_usd, fees_usd, float(liquidity), tvl_usd


@dataclass
class Bar:
    """One hour of Base mainnet ETH/USDC history."""

    timestamp: int
    price: float
    volume_usd: float
    fees_usd: float
    swaps: int
    liquidity: float = 0.0
    tvl_usd: float = 0.0


def aggregate_bars(
    swaps: Iterable[tuple[int, float, float, float, float, float]],
    bucket_sec: int = 3600,
) -> list[Bar]:
    """Fold a stream of (timestamp, price, volume_usd, fees_usd) into fixed buckets."""
    buckets: dict[int, dict] = {}
    for timestamp, price, volume, fees, liquidity, tvl in swaps:
        key = timestamp - (timestamp % bucket_sec)
        bucket = buckets.get(key)
        if bucket is None:
            bucket = {
                "price": price,
                "volume": 0.0,
                "fees": 0.0,
                "swaps": 0,
                "liquidity": liquidity,
                "tvl": tvl,
            }
            buckets[key] = bucket
        # The last price seen in the bucket is the close, and the last depth seen is the depth.
        bucket["price"] = price
        bucket["liquidity"] = liquidity
        bucket["tvl"] = tvl
        bucket["volume"] += volume
        bucket["fees"] += fees
        bucket["swaps"] += 1
    return [
        Bar(
            timestamp=key,
            price=bucket["price"],
            volume_usd=bucket["volume"],
            fees_usd=bucket["fees"],
            swaps=bucket["swaps"],
            liquidity=bucket["liquidity"],
            tvl_usd=bucket["tvl"],
        )
        for key, bucket in sorted(buckets.items())
    ]


def fill_gaps(bars: Sequence[Bar], bucket_sec: int = 3600) -> list[Bar]:
    """Make the series contiguous at the bar size it was bucketed at.

    A pool can go quiet for a bar or two. The feature windows are measured in hours, so
    a missing bar has to be a bar with no volume and no fees, not a hole that silently
    shortens the window. The price, the liquidity and the TVL are carried forward, because
    they are still true when nothing trades.

    The bucket size is a parameter rather than a constant because the archive window on
    Base decides how long a bar has to be: a fifteen-minute bar and an hourly bar are
    the same market read at two different resolutions, and mixing them up silently
    quarters the fee income the model sees.
    """
    if not bars:
        return []
    by_timestamp = {bar.timestamp: bar for bar in bars}
    start = min(by_timestamp)
    end = max(by_timestamp)
    out: list[Bar] = []
    previous: Bar | None = None
    for timestamp in range(start, end + bucket_sec, bucket_sec):
        bar = by_timestamp.get(timestamp)
        if bar is None:
            if previous is None:
                continue
            out.append(
                Bar(
                    timestamp=timestamp,
                    price=previous.price,
                    volume_usd=0.0,
                    fees_usd=0.0,
                    swaps=0,
                    liquidity=previous.liquidity,
                    tvl_usd=previous.tvl_usd,
                )
            )
            continue
        out.append(bar)
        previous = bar
    return out


def write_bars(bars: Sequence[Bar], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for bar in bars:
            handle.write(
                json.dumps(
                    {
                        "ts": bar.timestamp,
                        "price": bar.price,
                        "volume_usd": bar.volume_usd,
                        "fees_usd": bar.fees_usd,
                        "swaps": bar.swaps,
                        "liquidity": bar.liquidity,
                        "tvl_usd": bar.tvl_usd,
                    }
                )
                + "\n"
            )


def read_bars(path: Path) -> list[Bar]:
    bars: list[Bar] = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            bars.append(
                Bar(
                    timestamp=int(row["ts"]),
                    price=float(row["price"]),
                    volume_usd=float(row["volume_usd"]),
                    fees_usd=float(row["fees_usd"]),
                    swaps=int(row["swaps"]),
                    liquidity=float(row.get("liquidity", 0.0)),
                    tvl_usd=float(row.get("tvl_usd", 0.0)),
                )
            )
    return bars


def raw_rpc_call(method: str, params: list, url: str, timeout: float = 60.0) -> Any:
    """One JSON-RPC call against exactly one node, with no fallback.

    The archive probe needs to know what a *particular* node will and will not serve,
    so this call deliberately does not wander over to the other nodes the way
    `rpc_call` does.
    """
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "helm-agent/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raise RpcError(f"HTTP {exc.code}: {exc.read().decode()[:160]}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RpcError(f"{type(exc).__name__}: {exc}") from exc
    if "error" in payload:
        raise RpcError(str(payload["error"]))
    return payload["result"]


def classify_rpc_error(exc: Exception) -> str:
    """What kind of refusal this was: too old, too wide, or just busy."""
    message = str(exc).lower()
    if "archive" in message or "403" in message or "missing trie" in message or "not available" in message:
        return "too_old"
    if "range" in message or "too large" in message or "exceed maximum" in message:
        return "too_wide"
    return "busy"


def node_serves(pool: str, url: str, block: int, span: int = 999) -> bool:
    """Does this node serve logs for this block range?

    A `False` means the node refused because the block is outside its archive window.
    A busy node counts as refusing: the caller moves on to the next node rather than
    waiting, which is what keeps the archive probe from stalling.
    """
    try:
        raw_rpc_call(
            "eth_getLogs",
            [
                {
                    "fromBlock": hex(block),
                    "toBlock": hex(block + span),
                    "address": pool,
                    "topics": [SWAP_TOPIC],
                }
            ],
            url=url,
        )
        return True
    except RpcError as exc:
        return classify_rpc_error(exc) != "too_old"


def find_archive_start(pool: str, latest: int, nodes: Sequence[str]) -> tuple[int, str]:
    """The oldest block whose logs the public nodes will still serve, and the node that serves it.

    Free archive access is windowed, and the window moves: a node that serves the last
    two weeks today may serve three weeks tomorrow. Rather than assume, the fetcher
    probes each node for its own boundary and downloads from there, so the model is
    trained on as much real history as the network is willing to give.

    The probe is bounded. It walks a coarse ladder of candidate ages, and for the
    oldest candidate that works it refines with a binary search. A node that is busy
    for every candidate is skipped rather than retried forever.
    """
    ladder_blocks = [
        int(latest * fraction) for fraction in (0.05, 0.15, 0.3, 0.45, 0.6, 0.75, 0.85, 0.93)
    ]
    for node in nodes:
        best = latest
        for candidate in ladder_blocks:
            if node_serves(pool, node, candidate):
                best = candidate
                break
        if best >= latest:
            # this node serves nothing in the ladder; try the next one
            continue

        # refine between the last age that failed and the one that worked
        low, high = 1, best
        while high - low > 20_000:
            middle = (low + high) // 2
            if node_serves(pool, node, middle):
                high = middle
            else:
                low = middle
        return high, node
    return latest, nodes[0] if nodes else BASE_MAINNET_RPC


def fetch_history(
    days: int,
    cache_path: Path,
    pool_address: str | None = None,
    url: str = BASE_MAINNET_RPC,
    chunk_size: int = MAX_LOG_CHUNK,
    checkpoint_every: int = 25,
    bucket_sec: int = 3600,
    workers: int = 6,
) -> list[Bar]:
    """Download `days` of hourly ETH/USDC history and cache it.

    The download is long and it is checkpointed: every `checkpoint_every` chunks the
    bars are written and the last scanned block is remembered, so an interrupted run
    resumes instead of starting over. The history it writes is the history the model is
    trained on, so it is also the part of Helm that has to be reproducible.
    """
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    pool = resolve_pool(url=url) if pool_address is None else resolve_pool((pool_address,), url=url)
    block_time = measure_block_time(url)
    latest = get_block_number(url)

    # The archive window is what decides how much history there is. Ask the nodes.
    candidates = [url] + [n for n in BASE_MAINNET_RPC_FALLBACKS if n != url]
    archive_start, serving_node = find_archive_start(pool.address, latest, candidates)
    # The archive boundary is the real limit, so the download takes all of it and the
    # `days` argument only decides how much of it to *try* for.
    wanted = max(0, latest - int(days * 86400 / block_time))
    from_block = max(wanted, archive_start)
    to_block = latest

    # Base's block time changed during the window this download covers, so the mapping
    # from block number to timestamp has to be piecewise rather than linear. The clock
    # also tells us how much wall time the window really covers, which is the number the
    # `days` argument was asking for.
    clock = BlockClock.build(from_block, to_block, url=url)
    span_seconds = max(1, clock.span_seconds())
    span_days = span_seconds / 86400.0
    if span_days < days * 0.5:
        # the archive window is shorter than the caller asked for; take all of it
        print(
            f"only {span_days:.1f} days of history are available "
            f"(the caller asked for {days})",
            flush=True,
        )

    print(
        f"pool {pool.address} token0={pool.token0} token1={pool.token1} "
        f"fee={pool.fee_bps}bps decimals=({pool.decimals0},{pool.decimals1})",
        flush=True,
    )
    print(
        f"block time {block_time:.3f}s now; archive starts at block {archive_start} "
        f"(node {serving_node}); downloading {from_block}..{to_block} "
        f"({(to_block - from_block) // max(1, chunk_size) + 1} requests, "
        f"{span_days:.1f} days, {bucket_sec}s bars)",
        flush=True,
    )

    meta = read_meta(cache_path)
    start_block = from_block
    if meta.get("pool") == pool.address and int(meta.get("from_block", -1)) == from_block:
        start_block = int(meta.get("last_block", from_block - 1)) + 1
        if start_block <= to_block:
            print(f"resuming from block {start_block}", flush=True)

    def timestamp_of(block: int) -> int:
        return clock.timestamp(block)

    cached = read_bars(cache_path) if cache_path.exists() else []
    bars_by_ts: dict[int, Bar] = {bar.timestamp: bar for bar in cached}
    scanned = start_block - 1
    chunks = 0

    def flush(last_block: int) -> None:
        bars = fill_gaps([bars_by_ts[key] for key in sorted(bars_by_ts)], bucket_sec=bucket_sec)
        write_bars(bars, cache_path)
        write_meta(
            cache_path,
            {
                "pool": pool.address,
                "fee_bps": pool.fee_bps,
                "from_block": from_block,
                "last_block": last_block,
                "last_synced_at": timestamp_of(last_block),
                "bars": len(bars),
                "block_time_sec": block_time,
                "days": days,
                "bucket_sec": bucket_sec,
            },
        )

    for log in fetch_swap_logs(
        pool.address,
        start_block,
        to_block,
        chunk_size=chunk_size,
        url=serving_node,
        nodes=candidates,
        workers=workers,
    ):
        block = int(log["blockNumber"], 16)
        price, volume, fees, liquidity, tvl = decode_swap(log, pool)
        for bar in aggregate_bars([(timestamp_of(block), price, volume, fees, liquidity, tvl)], bucket_sec=bucket_sec):
            existing = bars_by_ts.get(bar.timestamp)
            if existing is None:
                bars_by_ts[bar.timestamp] = bar
            else:
                bars_by_ts[bar.timestamp] = Bar(
                    timestamp=bar.timestamp,
                    price=bar.price,
                    volume_usd=existing.volume_usd + bar.volume_usd,
                    fees_usd=existing.fees_usd + bar.fees_usd,
                    swaps=existing.swaps + bar.swaps,
                    liquidity=bar.liquidity,
                    tvl_usd=bar.tvl_usd,
                )
        scanned = max(scanned, block)
        chunks += 1
        if chunks % checkpoint_every == 0:
            flush(scanned)
            print(f"    checkpoint at block {scanned} ({len(bars_by_ts)} bars so far)", flush=True)

    flush(scanned)
    bars = fill_gaps([bars_by_ts[key] for key in sorted(bars_by_ts)], bucket_sec=bucket_sec)
    print(f"cached {len(bars)} bars of {bucket_sec}s to {cache_path}", flush=True)
    return bars


def meta_path_for(cache_path: Path) -> Path:
    """The sidecar that remembers how far the history has been downloaded."""
    return cache_path.with_suffix(cache_path.suffix + ".meta.json")


def read_meta(cache_path: Path) -> dict:
    path = meta_path_for(cache_path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def write_meta(cache_path: Path, meta: dict) -> None:
    path = meta_path_for(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, indent=2))


def merge_bars(cached: list[Bar], fresh: list[Bar]) -> list[Bar]:
    """Merge freshly downloaded bars into the cached ones.

    A bar that exists in both is the same hour seen twice: the cached copy holds the part
    of the hour that was already downloaded, the fresh copy holds the rest. The volumes
    add up, and the price is the most recent one, which is the hour's close.
    """
    merged: dict[int, Bar] = {bar.timestamp: bar for bar in cached}
    for bar in fresh:
        existing = merged.get(bar.timestamp)
        if existing is None:
            merged[bar.timestamp] = bar
            continue
        merged[bar.timestamp] = Bar(
            timestamp=bar.timestamp,
            price=bar.price,
            volume_usd=existing.volume_usd + bar.volume_usd,
            fees_usd=existing.fees_usd + bar.fees_usd,
            swaps=existing.swaps + bar.swaps,
            liquidity=bar.liquidity,
            tvl_usd=bar.tvl_usd,
        )
    return [merged[key] for key in sorted(merged)]


def sync_history(
    cache_path: Path,
    pool_address: str | None = None,
    url: str = BASE_MAINNET_RPC,
    chunk_size: int = MAX_LOG_CHUNK,
    progress: bool = False,
) -> list[Bar]:
    """Bring the cached history up to date, downloading only what is new.

    This is what the running agent calls. The first call downloads the whole window; the
    calls after that fetch only the blocks that arrived since the last one, which keeps
    the trailing feature windows current without re-reading months of swaps.
    """
    pool = resolve_pool(url=url) if pool_address is None else resolve_pool((pool_address,), url=url)
    meta = read_meta(cache_path)
    cached = read_bars(cache_path) if cache_path.exists() else []

    latest = get_block_number(url)
    if not cached:
        block_time = measure_block_time(url)
        from_block = max(0, latest - int(180 * 86400 / block_time))
    else:
        from_block = int(meta.get("last_block", latest - int(7 * 86400 / BASE_BLOCK_TIME_SEC))) + 1
    if from_block > latest:
        print(f"history already current at block {latest}", flush=True)
        return cached

    start_ts = get_block_timestamp(from_block, url)
    end_ts = get_block_timestamp(latest, url)

    # The sync window is short, but it still has to use the same clock as the original
    # download or the same swap would land in two different bars.
    clock = BlockClock.build(from_block, latest, url=url)

    def timestamp_of(block: int) -> int:
        return clock.timestamp(block)

    swaps: list[tuple[int, float, float, float, float, float]] = []
    for log in fetch_swap_logs(pool.address, from_block, latest, chunk_size=chunk_size, url=url, progress=progress):
        block = int(log["blockNumber"], 16)
        price, volume, fees, liquidity, tvl = decode_swap(log, pool)
        swaps.append((timestamp_of(block), price, volume, fees, liquidity, tvl))

    bucket_sec = int(meta.get("bucket_sec", 3600))
    bars = fill_gaps(
        merge_bars(cached, aggregate_bars(swaps, bucket_sec=bucket_sec)), bucket_sec=bucket_sec
    )
    write_bars(bars, cache_path)
    # The meta is merged, not replaced: the bucket size and the archive boundary are
    # properties of the cache, and losing them would silently re-bucket the history.
    write_meta(
        cache_path,
        {
            **meta,
            "pool": pool.address,
            "fee_bps": pool.fee_bps,
            "last_block": latest,
            "last_synced_at": end_ts,
            "bars": len(bars),
        },
    )
    print(f"history synced to block {latest}: {len(bars)} bars in total", flush=True)
    return bars


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Fetch real Base mainnet ETH/USDC history.")
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "base_eth_usdc_1h.jsonl",
    )
    parser.add_argument("--pool", default=None)
    parser.add_argument("--rpc", default=BASE_MAINNET_RPC)
    parser.add_argument("--chunk", type=int, default=MAX_LOG_CHUNK)
    parser.add_argument("--bucket", type=int, default=3600, help="bar size in seconds")
    parser.add_argument("--workers", type=int, default=6, help="parallel chunk fetches")
    args = parser.parse_args(argv)

    bars = fetch_history(
        days=args.days,
        cache_path=args.out,
        pool_address=args.pool,
        url=args.rpc,
        chunk_size=args.chunk,
        bucket_sec=args.bucket,
        workers=args.workers,
    )
    if not bars:
        print("no swaps found")
        return 1
    print(f"bars={len(bars)} first={bars[0]} last={bars[-1]}")
    print(f"mean price={sum(b.price for b in bars) / len(bars):.2f}")
    print(f"total volume=${sum(b.volume_usd for b in bars):,.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
