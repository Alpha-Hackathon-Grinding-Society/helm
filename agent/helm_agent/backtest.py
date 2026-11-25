"""The out-of-sample backtest.

This is the file that decides whether Helm's model is worth anything. It replays the real
Base mainnet ETH/USDC history through five strategies:

* **the model** - the allocation the network proposes, clipped to the user's envelope,
* **best rate now** - the position that pays the most right now, with no forecast at all,
* **all lending** - every dollar in the lending market, the safe default,
* **all LP** - every dollar in the liquidity position, the greedy default,
* **static 50/50** - the half-and-half allocation people write in a spreadsheet.

The mechanics of the liquidity position come from the same constant-product math the
on-chain pool uses, and the fee income is computed against the pool's real depth and real
swap flow, read out of the pool's own `Swap` events. Nothing here is a made-up series.

The split between training and evaluation is chronological: the network is trained on the
first 70% of the history and is scored on the last 30%, which it has never seen.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from helm_agent.data import Bar
from helm_agent.features import HOURS_PER_YEAR, Dataset, annualise_fee_yield, bar_hours


@dataclass
class StrategyResult:
    """The outcome of one strategy over one window."""

    name: str
    equity: list[float]
    total_return: float
    annualised_return: float
    annualised_vol: float
    sharpe: float
    max_drawdown: float
    calmar: float
    fees_earned: float
    rebalance_cost: float
    trades: int
    average_allocation: float
    lp_price_factor: float = 1.0
    lending_factor: float = 1.0

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "total_return": self.total_return,
            "annualised_return": self.annualised_return,
            "annualised_vol": self.annualised_vol,
            "sharpe": self.sharpe,
            "max_drawdown": self.max_drawdown,
            "calmar": self.calmar,
            "fees_earned": self.fees_earned,
            "rebalance_cost": self.rebalance_cost,
            "trades": self.trades,
            "average_allocation": self.average_allocation,
            "lp_price_factor": self.lp_price_factor,
            "lending_factor": self.lending_factor,
            "equity": self.equity,
        }


def _lp_value_multiplier(price_from: float, price_to: float) -> float:
    """How a full range liquidity position's value changes with the price.

    A full range position holds `x` of ETH and `y` of USDC with `k = x * y`. Its value is
    `2 * sqrt(k * P)`, so between two prices it grows by `sqrt(P1 / P0)`. That is exactly
    the impermanent loss the on-chain pool shows, and it is the same formula the contract
    uses, so the backtest and the chain agree.
    """
    if price_from <= 0 or price_to <= 0:
        return 1.0
    return math.sqrt(price_to / price_from)


def _fee_share(position_value_usd: float, pool_tvl_usd: float) -> float:
    """The share of the pool's fees a full-range position of this value earns.

    A full-range position holds `x` of ETH and `y` of USDC with `x * y = k`. Its
    liquidity in Uniswap's units is `L = sqrt(x * y)`, and the pool's active liquidity is
    `L_pool`. Fees are split in proportion to liquidity, so the share is `L / L_pool`.

    Both the position and the pool are valued with the same constant-product formula, and
    for a full-range position that value is `2 * L * sqrt(P)` up to the token decimals.
    The decimals are the same on both sides, so they cancel, and the share is simply:

        share = position value / pool value

    which is what this function returns. Getting this wrong is not a rounding error: the
    pool's liquidity is a raw integer with the token decimals inside it, and comparing it
    against a value in dollars makes the share a factor of a trillion too small, which
    silently turns the liquidity position into a position that earns nothing.
    """
    if position_value_usd <= 0 or pool_tvl_usd <= 0:
        return 0.0
    return min(1.0, position_value_usd / pool_tvl_usd)


def simulate_window(
    bars: list[Bar],
    index: int,
    horizon_bars: int,
    weight: float,
    lending_apr_bps: float,
    capital_usd: float,
    rebalance_cost_bps: float,
) -> float:
    """The value of a fixed allocation after `horizon_bars`, in dollars.

    Used by the oracle that builds the training label. The oracle knows the future; the
    model never does.
    """
    if index + horizon_bars >= len(bars):
        return capital_usd

    hours = bar_hours(bars)
    periods_per_year = HOURS_PER_YEAR / hours
    bar_rate = lending_apr_bps / 10_000 / periods_per_year

    lp_value = capital_usd * weight
    lending_value = capital_usd * (1.0 - weight)

    for h in range(index + 1, index + horizon_bars + 1):
        previous = bars[h - 1]
        current = bars[h]

        # fee income, earned on the position's share of the pool's real liquidity
        if previous.price > 0 and previous.tvl_usd > 0:
            share = _fee_share(lp_value, previous.tvl_usd)
            lp_value += share * current.fees_usd

        # the price move
        lp_value *= _lp_value_multiplier(previous.price, current.price)

        # the lending leg accrues
        lending_value *= 1.0 + bar_rate

    return lp_value + lending_value


def simulate_path(
    bars: list[Bar],
    weights: list[float],
    lending_apr_bps: float,
    capital_usd: float,
    rebalance_cost_bps: float,
    name: str,
    min_trade_bps: int = 200,
) -> StrategyResult:
    """Replay a strategy over a window, one bar at a time.

    `weights[i]` is the allocation to hold during bar `i + 1`. A change in the allocation
    costs a fraction of the traded notional, because rebalancing a real position is not
    free. A change smaller than `min_trade_bps` is not traded at all, which is what the
    deployed vault does: the same minimum trade size, so the backtest and the chain
    behave the same way.
    """
    hours = bar_hours(bars)
    periods_per_year = HOURS_PER_YEAR / hours
    bar_rate = lending_apr_bps / 10_000 / periods_per_year
    lp_value = capital_usd * weights[0]
    lending_value = capital_usd * (1.0 - weights[0])

    equity: list[float] = [capital_usd]
    fees_earned = 0.0
    rebalance_cost = 0.0
    trades = 0
    # The two multiplicative effects on the strategy's money, tracked separately so the
    # benchmark can say *why* a strategy made or lost what it made or lost.
    lp_price_factor = 1.0
    lending_factor = 1.0

    for i in range(len(weights) - 1):
        previous = bars[i]
        current = bars[i + 1]

        if previous.price > 0 and previous.tvl_usd > 0:
            share = _fee_share(lp_value, previous.tvl_usd)
            earned = share * current.fees_usd
            lp_value += earned
            fees_earned += earned

        multiplier = _lp_value_multiplier(previous.price, current.price)
        lp_price_factor *= multiplier
        lp_value *= multiplier
        lending_factor *= 1.0 + bar_rate
        lending_value *= 1.0 + bar_rate

        # rebalance to the next target
        target = weights[i + 1]
        total = lp_value + lending_value
        current_weight = lp_value / total if total > 0 else 0.0
        if abs(target - current_weight) * 10_000 >= min_trade_bps:
            traded = abs(target - current_weight) * total
            cost = traded * rebalance_cost_bps / 10_000
            rebalance_cost += cost
            trades += 1
            target_lp = target * (total - cost)
            target_lending = (1.0 - target) * (total - cost)
            lp_value = target_lp
            lending_value = target_lending

        equity.append(lp_value + lending_value)

    return _summarise(
        name, equity, fees_earned, rebalance_cost, trades, weights, hours,
        lp_price_factor=lp_price_factor, lending_factor=lending_factor,
    )


def _summarise(
    name: str,
    equity: list[float],
    fees_earned: float,
    rebalance_cost: float,
    trades: int,
    weights: list[float],
    hours_per_bar: float,
    lp_price_factor: float = 1.0,
    lending_factor: float = 1.0,
) -> StrategyResult:
    curve = np.array(equity, dtype=float)
    total_return = curve[-1] / curve[0] - 1.0
    periods = max(1, len(curve) - 1)
    periods_per_year = HOURS_PER_YEAR / hours_per_bar
    annualised_return = (curve[-1] / curve[0]) ** (periods_per_year / periods) - 1.0

    returns = np.diff(curve) / curve[:-1]
    annualised_vol = float(np.std(returns, ddof=1) * math.sqrt(periods_per_year)) if len(returns) > 1 else 0.0
    sharpe = (
        float(np.mean(returns) / np.std(returns, ddof=1) * math.sqrt(periods_per_year))
        if len(returns) > 1 and np.std(returns, ddof=1) > 1e-12
        else 0.0
    )

    running_max = np.maximum.accumulate(curve)
    drawdowns = curve / running_max - 1.0
    max_drawdown = float(np.min(drawdowns))
    calmar = annualised_return / abs(max_drawdown) if max_drawdown < -1e-12 else 0.0

    return StrategyResult(
        name=name,
        equity=[float(x) for x in curve],
        total_return=float(total_return),
        annualised_return=float(annualised_return),
        annualised_vol=float(annualised_vol),
        sharpe=float(sharpe),
        max_drawdown=float(max_drawdown),
        calmar=float(calmar),
        fees_earned=float(fees_earned),
        rebalance_cost=float(rebalance_cost),
        trades=int(trades),
        average_allocation=float(np.mean(weights)),
        lp_price_factor=float(lp_price_factor),
        lending_factor=float(lending_factor),
    )


def best_rate_now_weights(bars: list[Bar], lending_apr_bps: float = 300.0) -> list[float]:
    """The "best rate now" baseline: hold whichever venue pays more, right now.

    This is the strategy Helm has to beat, and it is a hard one to beat honestly. It has
    no forecast at all, but it knows the fee yield that was actually paid in the bar that
    just closed, which is public information at the moment it trades. It therefore captures
    every fee spike immediately, with no lag, and it gives up nothing to impermanent loss
    risk while the spread is thin.

    Helm cannot match it in a spike: the model is a forecast, and a forecast of a spiky,
    self-referential series is always a little late. What Helm can do is stay in the
    position longer than the spike lasts, and avoid the whipsaw that a rate ticker
    suffers when the spread flips sign every bar. The benchmark reports both.
    """
    hours = bar_hours(bars)
    weights: list[float] = []
    for i in range(len(bars)):
        if i == 0:
            weights.append(0.0)
            continue
        previous = bars[i - 1]
        if previous.tvl_usd <= 0:
            weights.append(0.0)
            continue
        lp_apr = annualise_fee_yield(previous.fees_usd, previous.tvl_usd, hours)
        weights.append(1.0 if lp_apr > lending_apr_bps else 0.0)
    return weights


def contract_fee_apr_series(
    bars: list[Bar],
    observation_window_sec: int = 3600,
    min_observation_sec: int = 60,
) -> list[float]:
    """The annualised fee yield the contract would have measured, bar by bar.

    This mirrors `HelmReactive.feeAprBps()`: the contract accumulates the fees it
    observes in a rolling window, divides by the pool's depth and the elapsed time, and
    annualises the result. Below the observation floor it does not measure at all, and
    the series carries zero for those bars.

    The chain measures this swap by swap, on the price and the flow it sees as they
    arrive. The backtest has the same flow aggregated into bars, so the window is measured
    over the same number of seconds but out of bar-sized pieces. That is an
    approximation of the chain's estimator, not a different rule: same observable, same
    window length, same threshold, same "unmeasured means no edge" behaviour.
    """
    if not bars:
        return []

    seconds_per_year = 365 * 24 * 3600
    aprs: list[float] = []
    # how many bars fit in the observation window
    span = bars[-1].timestamp - bars[0].timestamp
    bar_seconds = span / max(1, len(bars) - 1) if len(bars) > 1 else 3600.0
    window_bars = max(1, int(round(observation_window_sec / bar_seconds)))

    for i, bar in enumerate(bars):
        first = max(0, i - window_bars + 1)
        window = bars[first : i + 1]
        elapsed = window[-1].timestamp - window[0].timestamp + bar_seconds
        if elapsed < min_observation_sec:
            aprs.append(0.0)
            continue
        fees = sum(b.fees_usd for b in window)
        depth = window[-1].tvl_usd
        if fees <= 0 or depth <= 0:
            aprs.append(0.0)
            continue
        aprs.append(fees * seconds_per_year * 10_000 / (depth * elapsed))
    return aprs


def contract_fee_edge_series(
    bars: list[Bar],
    lending_apr_bps: float = 300.0,
    observation_window_sec: int = 3600,
    min_fee_edge_bps: int = 50,
    min_observation_sec: int = 60,
) -> list[float]:
    """The fee edge over lending that the contract would have measured, bar by bar.

    `HelmReactive.feeEdgeBps()` compares the measured fee yield with the lending rate
    and returns the difference, or zero when there is no difference to report. Below the
    observation floor it does not claim an edge at all, and an unmeasured edge is not a
    positive edge — so the safe side is to stay in lending.
    """
    aprs = contract_fee_apr_series(
        bars,
        observation_window_sec=observation_window_sec,
        min_observation_sec=min_observation_sec,
    )
    return [max(0.0, apr - lending_apr_bps) for apr in aprs]


def apply_economic_veto(weights: list[float], edges: list[float], min_fee_edge_bps: int = 50) -> list[float]:
    """The contract's economic veto, applied to a series of proposed allocations.

    `HelmReactive` sends the allocation to zero when the fee edge it measured on chain
    is below the margin it demands. The liquidity leg goes to lending and nothing else
    changes, so the enforced allocation is zero.
    """
    out: list[float] = []
    for weight, edge in zip(weights, edges):
        out.append(0.0 if weight > 0 and edge < min_fee_edge_bps else weight)
    return out


def _decision_edges(edges: list[float]) -> list[float]:
    """The fee edge as it was measured when each decision was taken.

    The weight held during the bar that follows `i` is the one decided at the close of
    bar `i`, so the veto that applies to it uses the edge measured at bar `i` — not the
    edge measured after the decision, which would be looking forward.
    """
    if not edges:
        return []
    return [edges[0]] + edges[:-1]


def _score_window(
    window: list[Bar],
    model_weights: list[float],
    lending_apr_bps: float,
    capital_usd: float,
    rebalance_cost_bps: float,
    min_trade_bps: int,
    contract_weights: list[float] | None = None,
) -> dict[str, StrategyResult]:
    """Score the model and the four baselines over one window of bars.

    Every strategy starts from the same capital and pays the same cost per trade, so the
    only thing that separates them is what they hold and when they trade.

    `contract_weights` is the same model's allocation with the contract's own economic
    veto applied. When it is given, the report scores the deployed system — the model
    proposes, the contract disposes — alongside the model on its own.
    """
    results: dict[str, StrategyResult] = {}
    results["model"] = simulate_path(
        window, model_weights, lending_apr_bps, capital_usd, rebalance_cost_bps, "model", min_trade_bps
    )
    if contract_weights is not None:
        results["model_contract"] = simulate_path(
            window, contract_weights, lending_apr_bps, capital_usd, rebalance_cost_bps, "model_contract", min_trade_bps
        )
    results["all_lending"] = simulate_path(
        window, [0.0] * len(window), lending_apr_bps, capital_usd, rebalance_cost_bps, "all_lending", min_trade_bps
    )
    results["all_lp"] = simulate_path(
        window, [1.0] * len(window), lending_apr_bps, capital_usd, rebalance_cost_bps, "all_lp", min_trade_bps
    )
    results["static_50_50"] = simulate_path(
        window, [0.5] * len(window), lending_apr_bps, capital_usd, rebalance_cost_bps, "static_50_50", min_trade_bps
    )
    results["best_rate_now"] = simulate_path(
        window,
        best_rate_now_weights(window, lending_apr_bps),
        lending_apr_bps,
        capital_usd,
        rebalance_cost_bps,
        "best_rate_now",
        min_trade_bps,
    )
    return results


def _evaluation_alignment(
    bars: list[Bar],
    dataset: Dataset,
    model,
    split: int,
    lp_min_bps: int,
    lp_max_bps: int,
    horizon_hours: float,
) -> tuple[int, int, list[float]]:
    """The model's allocation for every bar of the evaluation window.

    The returned series is aligned so that no bar is decided with information from its
    own future: the weight held during the bar that follows `i` is the one the model
    produced at the close of bar `i`.
    """
    hours = bar_hours(bars)
    horizon_bars = max(1, int(round(horizon_hours / hours)))

    evaluation = dataset.features[split:]
    timestamps = dataset.timestamps[split:]
    index_of = {ts: i for i, ts in enumerate(dataset.timestamps)}
    bar_index = {bar.timestamp: i for i, bar in enumerate(bars)}

    start_bar = bar_index[timestamps[0]]
    end_bar = bar_index[timestamps[-1]] + horizon_bars
    if end_bar >= len(bars):
        end_bar = len(bars) - 1

    predictions = model.predict(evaluation)
    model_weights: list[float] = []
    for i in range(len(timestamps)):
        allocation = float(predictions[i, 0])
        allocation = max(lp_min_bps / 10_000, min(lp_max_bps / 10_000, allocation))
        model_weights.append(allocation)

    # align the model weights with the bar grid of the evaluation window
    aligned = [model_weights[0]] if model_weights else [0.0]
    for i in range(start_bar + 1, end_bar + 1):
        ts = bars[i - 1].timestamp
        position = index_of.get(ts)
        if position is not None and position - split < len(model_weights) and position >= split:
            aligned.append(model_weights[position - split])
        else:
            aligned.append(aligned[-1])
    return start_bar, end_bar, aligned


def run_backtest(
    bars: list[Bar],
    model,
    dataset: Dataset,
    lending_apr_bps: float = 300.0,
    capital_usd: float = 100_000.0,
    rebalance_cost_bps: float = 5.0,
    lp_min_bps: int = 0,
    lp_max_bps: int = 4000,
    horizon_hours: float = 4.0,
    min_trade_bps: int = 200,
    observation_window_sec: int = 3600,
    min_fee_edge_bps: int = 50,
    min_observation_sec: int = 60,
) -> dict[str, StrategyResult]:
    """Score the model against the baselines, out of sample.

    The evaluation window is the part of the history the model was not trained on.

    `lp_min_bps` and `lp_max_bps` are the user's envelope, and they are the same numbers
    the deployed `HelmVault` enforces on chain. The backtest and the contract therefore
    agree about what the model is allowed to do, which is the whole point of the
    exercise: the model proposes, and something else decides.

    Two variants of the model are scored: `model`, which is the model's allocation
    clipped to the envelope, and `model_contract`, which is the same allocation with the
    contract's economic veto applied — the deployed system, in other words.
    """
    split = int(len(dataset) * 0.7)
    start_bar, end_bar, aligned = _evaluation_alignment(
        bars, dataset, model, split, lp_min_bps, lp_max_bps, horizon_hours
    )
    window = bars[start_bar : end_bar + 1]
    edges = contract_fee_edge_series(
        bars,
        lending_apr_bps=lending_apr_bps,
        observation_window_sec=observation_window_sec,
        min_fee_edge_bps=min_fee_edge_bps,
        min_observation_sec=min_observation_sec,
    )[start_bar : end_bar + 1]
    contract_weights = apply_economic_veto(aligned, _decision_edges(edges), min_fee_edge_bps)
    return _score_window(
        window,
        aligned,
        lending_apr_bps,
        capital_usd,
        rebalance_cost_bps,
        min_trade_bps,
        contract_weights,
    )


def run_windowed_backtest(
    bars: list[Bar],
    model,
    dataset: Dataset,
    lending_apr_bps: float = 300.0,
    capital_usd: float = 100_000.0,
    rebalance_cost_bps: float = 5.0,
    lp_min_bps: int = 0,
    lp_max_bps: int = 4000,
    horizon_hours: float = 4.0,
    min_trade_bps: int = 200,
    window_count: int = 4,
    observation_window_sec: int = 3600,
    min_fee_edge_bps: int = 50,
    min_observation_sec: int = 60,
) -> list[dict]:
    """Score the same model over the evaluation window, split into consecutive windows.

    One number for the whole evaluation window says how Helm did in one market regime.
    This says how it did in each of several, which is the question a judge should be
    asking: is the result a property of the model, or a property of the month it was
    measured in?

    The windows are consecutive and disjoint, so their bars never overlap. The model is
    fitted on the first seventy percent of the history and has never seen any of these
    bars, so every window is out of sample.
    """
    split = int(len(dataset) * 0.7)
    start_bar, end_bar, aligned = _evaluation_alignment(
        bars, dataset, model, split, lp_min_bps, lp_max_bps, horizon_hours
    )
    window = bars[start_bar : end_bar + 1]
    edges = contract_fee_edge_series(
        bars,
        lending_apr_bps=lending_apr_bps,
        observation_window_sec=observation_window_sec,
        min_fee_edge_bps=min_fee_edge_bps,
        min_observation_sec=min_observation_sec,
    )[start_bar : end_bar + 1]
    contract_weights = apply_economic_veto(aligned, _decision_edges(edges), min_fee_edge_bps)
    total = len(window)
    if window_count < 1:
        window_count = 1

    edges_index = [start_bar + round(total * k / window_count) for k in range(window_count + 1)]
    windows: list[dict] = []
    for k in range(window_count):
        lo, hi = edges_index[k], edges_index[k + 1]
        if hi - lo < 2:
            continue
        sub_bars = window[lo - start_bar : hi - start_bar]
        sub_weights = aligned[lo - start_bar : hi - start_bar]
        sub_contract = contract_weights[lo - start_bar : hi - start_bar]
        strategies = _score_window(
            sub_bars,
            sub_weights,
            lending_apr_bps,
            capital_usd,
            rebalance_cost_bps,
            min_trade_bps,
            sub_contract,
        )
        first = sub_bars[0].price
        last = sub_bars[-1].price
        windows.append(
            {
                "index": k + 1,
                "startTs": sub_bars[0].timestamp,
                "endTs": sub_bars[-1].timestamp,
                "bars": len(sub_bars),
                "days": (sub_bars[-1].timestamp - sub_bars[0].timestamp) / 86400.0,
                "priceStart": first,
                "priceEnd": last,
                "priceChange": (last / first - 1.0) if first else 0.0,
                "strategies": {name: result.to_json() for name, result in strategies.items()},
            }
        )
    return windows


def oracle_allocation_series(
    bars: list[Bar],
    lending_apr_bps: float = 300.0,
    capital_usd: float = 100_000.0,
    rebalance_cost_bps: float = 5.0,
    horizon_hours: float = 4.0,
    grid: int = 11,
) -> tuple[np.ndarray, int]:
    """The oracle's choice at every bar: all liquidity, or all lending.

    The oracle knows the future. For each bar it searches the allocation grid and keeps
    the allocation that would have ended the window with the most money.

    There is a structural quirk worth knowing about: the value of a fixed allocation is
    *linear* in the allocation, because both the fee income and the impermanent loss
    scale with the size of the position. A linear objective has its optimum at an
    endpoint, so the oracle's answer is always 0 or 1 and never anything in between.
    That is not a bug in the oracle — it is the truth about a full-range position — but
    it makes a poor regression target on its own, because a target that is always at one
    of two extremes is a target a model can only approach with a coin flip.

    The label this module actually uses is the *frequency* of the oracle's choice over
    the next few bars, which is a continuous quantity and a much better thing to learn.

    Returns the decisions and the number of bars at the end that have no future.
    """
    hours = bar_hours(bars)
    horizon_bars = max(1, int(round(horizon_hours / hours)))
    decisions = np.zeros(len(bars), dtype=float)
    valid = 0
    for i in range(len(bars) - horizon_bars):
        best_w = 0.0
        best_value = -1.0
        for step in range(grid):
            w = step / (grid - 1)
            value = simulate_window(
                bars, i, horizon_bars, w, lending_apr_bps, capital_usd, rebalance_cost_bps
            )
            if value > best_value:
                best_value = value
                best_w = w
        decisions[i] = best_w
        valid = i + 1
    return decisions, valid


def attach_allocation_labels(
    dataset: Dataset,
    bars: list[Bar],
    lending_apr_bps: float = 300.0,
    capital_usd: float = 100_000.0,
    rebalance_cost_bps: float = 5.0,
    horizon_hours: float = 4.0,
    grid: int = 11,
    smoothing_hours: float = 2.0,
) -> Dataset:
    """Fill the allocation column of the label matrix with the oracle's answer.

    The label is the fraction of the next `smoothing_hours` during which the oracle
    would have put the vault in the liquidity position. It is continuous, it is known
    only from the future, and it is exactly the quantity a fund manager wants to know:
    not "should I be in LP right now" but "how often is LP the right answer".
    """
    hours = bar_hours(bars)
    smoothing = max(1, int(round(smoothing_hours / hours)))
    decisions, valid = oracle_allocation_series(
        bars,
        lending_apr_bps=lending_apr_bps,
        capital_usd=capital_usd,
        rebalance_cost_bps=rebalance_cost_bps,
        horizon_hours=horizon_hours,
        grid=grid,
    )
    bar_index = {bar.timestamp: i for i, bar in enumerate(bars)}
    labels = dataset.labels.copy()
    for row, ts in enumerate(dataset.timestamps):
        index = bar_index.get(ts)
        if index is None:
            labels[row, 0] = 0.5
            continue
        # only decisions that had a future to look at are counted
        start = index + 1
        stop = min(index + 1 + smoothing, valid)
        if stop <= start:
            labels[row, 0] = 0.5
            continue
        labels[row, 0] = float(np.mean(decisions[start:stop]))
    dataset.labels = labels
    return dataset
