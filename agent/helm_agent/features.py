"""Features and labels for the Helm allocation model.

Everything here is computed from the raw Base mainnet history that `helm_agent.data`
downloads. The rule this module follows is simple: a feature at bar `t` may only use data
from bars `<= t`, and a label at bar `t` may only use data from bars `> t`. That split is
what makes the backtest honest, so it is enforced here rather than in the training
script.

The same code path serves training and inference. `build_dataset` produces the labelled,
normalised matrix the network is fitted on; `live_features` produces one normalised row
for the most recent bar of history, which is what the running agent feeds the model.
If those two ever disagree, the backtest is measuring a different network than the one
that is deployed, so they share one implementation on purpose.

Every window in this file is expressed in hours and converted to bars at runtime, so the
same code works whether the history was downloaded at 15 minute bars or at hourly bars.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from helm_agent.data import Bar

HOURS_PER_YEAR = 8766.0  # 365.25 days

FEATURE_NAMES = (
    "fee_apr_bps",       # trailing fee yield the pool actually paid, annualised
    "fee_edge_bps",      # that yield minus the lending rate: the economic edge
    "vol_bps",           # EWMA of the bar returns, annualised
    "ret_24h",           # 24 hour log return
    "ret_72h",           # 72 hour log return
    "drawdown_7d",       # distance below the 7 day high
    "volume_z",          # volume z-score over 7 days
    "fee_momentum",      # trailing fee yield minus the 7 day average fee yield
    "liquidity_trend",   # log change in pool liquidity over 24 hours
    "tvl_trend",         # log change in pool TVL over 24 hours
    "hour_sin",          # time of day, cyclical
    "hour_cos",
)

LABEL_NAMES = ("allocation", "vol_bps", "yield_bps")

# Window lengths, in hours.
FEE_WINDOW_HOURS = 24.0
TREND_WINDOW_HOURS = 24.0
MOMENTUM_WINDOW_HOURS = 72.0
WEEK_HOURS = 168.0
VOL_HALF_LIFE_HOURS = 24.0


@dataclass
class Dataset:
    """A feature matrix, a label matrix and the metadata that goes with them."""

    features: np.ndarray  # (n, len(FEATURE_NAMES)), already normalised
    labels: np.ndarray  # (n, len(LABEL_NAMES)); column 0 is filled in by the oracle
    timestamps: list[int]
    prices: np.ndarray
    bars: list[Bar]
    mean: np.ndarray
    std: np.ndarray
    raw_features: np.ndarray  # the same rows before normalisation
    bar_hours: float = 1.0

    def __len__(self) -> int:
        return len(self.timestamps)


def bar_hours(bars: list[Bar]) -> float:
    """How many hours one bar of this history covers.

    It is measured from the timestamps rather than assumed, because the archive window on
    Base decides how long a bar has to be, and a feature window that quietly assumes a
    different bar size is a feature window that is measuring the wrong thing.
    """
    if len(bars) < 2:
        return 1.0
    diffs = [bars[i].timestamp - bars[i - 1].timestamp for i in range(1, len(bars))]
    diffs = [d for d in diffs if d > 0]
    if not diffs:
        return 1.0
    diffs.sort()
    return diffs[len(diffs) // 2] / 3600.0


def annualise_fee_yield(fees_usd: float, tvl_usd: float, hours: float) -> float:
    """Annualise a fee flow against the pool's depth, in basis points."""
    if tvl_usd <= 0 or hours <= 0:
        return 0.0
    return (fees_usd / tvl_usd) * (HOURS_PER_YEAR / hours) * 10_000


def annualise_vol(returns: np.ndarray, hours_per_bar: float = 1.0) -> float:
    """Annualise a return series measured per bar, in basis points."""
    if len(returns) < 2:
        return 0.0
    periods_per_year = HOURS_PER_YEAR / hours_per_bar
    return float(np.std(returns, ddof=1) * math.sqrt(periods_per_year) * 10_000)


def _bars_for(hours: float, bar_h: float) -> int:
    return max(1, int(round(hours / bar_h)))


def _rolling_sum(values: np.ndarray, window: int) -> np.ndarray:
    """Sum over the trailing `window` entries, inclusive of the current one."""
    padded = np.concatenate([np.zeros(window - 1), values])
    cumulative = np.concatenate([[0.0], np.cumsum(padded)])
    return cumulative[window:] - cumulative[:-window]


def _rolling_mean(values: np.ndarray, window: int) -> np.ndarray:
    padded = np.concatenate([np.zeros(window - 1), values])
    cumulative = np.concatenate([[0.0], np.cumsum(padded)])
    total = cumulative[window:] - cumulative[:-window]
    return total / window


def _rolling_max(values: np.ndarray, window: int) -> np.ndarray:
    padded = np.concatenate([np.full(window - 1, -np.inf), values])
    return np.array(
        [float(np.max(padded[i : i + window])) for i in range(len(values))],
        dtype=float,
    )


def compute_raw_features(
    bars: list[Bar],
    lending_apr_bps: float = 300.0,
) -> tuple[np.ndarray, np.ndarray]:
    """The un-normalised feature matrix for every bar, plus the per-bar log returns.

    Row `i` only ever looks at bars `0..i`. The function returns one row per bar, with
    the warm-up rows filled with zeros; `build_dataset` decides which rows are usable.
    """
    n = len(bars)
    hours = bar_hours(bars)
    fee_window = _bars_for(FEE_WINDOW_HOURS, hours)
    trend_window = _bars_for(TREND_WINDOW_HOURS, hours)
    momentum_window = _bars_for(MOMENTUM_WINDOW_HOURS, hours)
    week_window = _bars_for(WEEK_HOURS, hours)

    prices = np.array([b.price for b in bars], dtype=float)
    volumes = np.array([b.volume_usd for b in bars], dtype=float)
    fees = np.array([b.fees_usd for b in bars], dtype=float)
    liquidity = np.array([b.liquidity for b in bars], dtype=float)
    tvl = np.array([b.tvl_usd for b in bars], dtype=float)

    log_returns = np.zeros(n, dtype=float)
    if n > 1:
        log_returns[1:] = np.log(prices[1:] / prices[:-1])

    # ---- trailing fee yield -----------------------------------------------------------------
    fee_sum = _rolling_sum(fees, fee_window)
    tvl_positive = np.where(tvl > 0, tvl, 0.0)
    tvl_sum = _rolling_sum(tvl_positive, fee_window)
    tvl_count = _rolling_sum((tvl > 0).astype(float), fee_window)
    tvl_mean = np.divide(tvl_sum, tvl_count, out=np.zeros_like(tvl_sum), where=tvl_count > 0)
    window_hours = fee_window * hours
    fee_apr = np.array(
        [annualise_fee_yield(float(fee_sum[i]), float(tvl_mean[i]), window_hours) for i in range(n)],
        dtype=float,
    )
    fee_week = _rolling_mean(fee_apr, week_window)

    # ---- volatility --------------------------------------------------------------------------
    ewma_var = 0.0
    ewma_alpha = 2.0 / (_bars_for(VOL_HALF_LIFE_HOURS, hours) + 1)
    periods_per_year = HOURS_PER_YEAR / hours
    vol_bps = np.zeros(n, dtype=float)
    for i in range(n):
        ewma_var = ewma_alpha * (log_returns[i] ** 2) + (1 - ewma_alpha) * ewma_var
        vol_bps[i] = math.sqrt(max(ewma_var, 0.0)) * math.sqrt(periods_per_year) * 10_000

    # ---- momentum ----------------------------------------------------------------------------
    ret_24h = np.zeros(n, dtype=float)
    ret_72h = np.zeros(n, dtype=float)
    for i in range(n):
        ret_24h[i] = float(np.sum(log_returns[max(0, i - fee_window + 1) : i + 1]))
        ret_72h[i] = float(np.sum(log_returns[max(0, i - momentum_window + 1) : i + 1]))

    high_7d = _rolling_max(prices, week_window)
    drawdown = np.zeros(n, dtype=float)
    for i in range(n):
        if high_7d[i] > 0:
            drawdown[i] = math.log(prices[i] / high_7d[i])

    volume_mean = _rolling_mean(volumes, week_window)
    volume_sq_mean = _rolling_mean(volumes**2, week_window)
    volume_std = np.sqrt(np.maximum(volume_sq_mean - volume_mean**2, 0.0))
    volume_z = np.divide(
        volumes - volume_mean, volume_std, out=np.zeros(n), where=volume_std > 1e-9
    )

    liquidity_trend = np.zeros(n, dtype=float)
    tvl_trend = np.zeros(n, dtype=float)
    for i in range(n):
        previous = max(0, i - trend_window)
        if liquidity[previous] > 0 and liquidity[i] > 0:
            liquidity_trend[i] = math.log(liquidity[i] / liquidity[previous])
        if tvl[previous] > 0 and tvl[i] > 0:
            tvl_trend[i] = math.log(tvl[i] / tvl[previous])

    day_fraction = np.array([((bar.timestamp // 3600) % 24) / 24.0 for bar in bars], dtype=float)
    angle = 2 * np.pi * day_fraction

    raw = np.zeros((n, len(FEATURE_NAMES)), dtype=float)
    raw[:, 0] = fee_apr
    raw[:, 1] = fee_apr - lending_apr_bps
    raw[:, 2] = vol_bps
    raw[:, 3] = ret_24h
    raw[:, 4] = ret_72h
    raw[:, 5] = drawdown
    raw[:, 6] = volume_z
    raw[:, 7] = fee_apr - fee_week
    raw[:, 8] = liquidity_trend
    raw[:, 9] = tvl_trend
    raw[:, 10] = np.sin(angle)
    raw[:, 11] = np.cos(angle)
    return raw, log_returns


def compute_forward_labels(
    bars: list[Bar],
    horizon_hours: float = 1.0,
    lending_apr_bps: float = 300.0,
) -> np.ndarray:
    """The labels for every bar, with NaN where the future is not known yet.

    Column 0 (the allocation) is left as NaN: that label comes from the oracle in
    `helm_agent.backtest`, which has to search the allocation grid.
    """
    n = len(bars)
    hours = bar_hours(bars)
    horizon = _bars_for(horizon_hours, hours)

    fees = np.array([b.fees_usd for b in bars], dtype=float)
    tvl = np.array([b.tvl_usd for b in bars], dtype=float)
    _, log_returns = compute_raw_features(bars, lending_apr_bps)

    labels = np.full((n, len(LABEL_NAMES)), np.nan, dtype=float)

    for i in range(n - horizon):
        window = slice(i + 1, i + horizon + 1)
        horizon_hours_real = horizon * hours

        depth_values = tvl[window]
        depth = float(depth_values[depth_values > 0].mean()) if np.any(depth_values > 0) else 0.0
        realized_yield = annualise_fee_yield(float(fees[window].sum()), depth, horizon_hours_real)

        returns = log_returns[window]
        mean_return = float(np.mean(returns))
        variance = float(np.var(returns, ddof=1)) if len(returns) > 1 else 0.0
        realized_vol = math.sqrt(variance) * math.sqrt(HOURS_PER_YEAR / hours) * 10_000

        labels[i, 1] = realized_vol
        labels[i, 2] = realized_yield
    return labels


def build_dataset(
    bars: list[Bar],
    lending_apr_bps: float = 300.0,
    horizon_hours: float = 1.0,
    warmup_hours: float = 72.0,
) -> Dataset:
    """Turn the history into a supervised dataset.

    Parameters
    ----------
    bars:
        The history, oldest first.
    lending_apr_bps:
        The annualised rate the lending market pays on the stablecoin leg. The default is
        the rate the deployed mock lending pool publishes (300 bps).
    horizon_hours:
        How far ahead the volatility and yield labels look.
    warmup_hours:
        How much history the feature windows need before the first row is usable.
    """
    hours = bar_hours(bars)
    horizon = _bars_for(horizon_hours, hours)
    warmup = _bars_for(warmup_hours, hours)
    if len(bars) < warmup + horizon + 2:
        raise ValueError(f"need at least {warmup + horizon + 2} bars, got {len(bars)}")

    raw, _ = compute_raw_features(bars, lending_apr_bps)
    labels = compute_forward_labels(bars, horizon_hours, lending_apr_bps)

    keep = np.isfinite(raw).all(axis=1)
    keep[:warmup] = False
    keep &= ~np.isnan(labels[:, 1])

    idx = np.flatnonzero(keep)
    mean = raw[idx].mean(axis=0)
    std = raw[idx].std(axis=0)
    std[std < 1e-9] = 1.0

    return Dataset(
        features=(raw[idx] - mean) / std,
        labels=labels[idx],
        timestamps=[bars[i].timestamp for i in idx],
        prices=np.array([bars[i].price for i in idx], dtype=float),
        bars=[bars[i] for i in idx],
        mean=mean,
        std=std,
        raw_features=raw[idx],
        bar_hours=hours,
    )


def live_features(
    bars: list[Bar],
    mean: np.ndarray,
    std: np.ndarray,
    lending_apr_bps: float = 300.0,
    index: int | None = None,
) -> np.ndarray:
    """One normalised feature row for the newest bar of history.

    This is the inference path. It uses exactly the same computation as the training
    matrix, so a reviewer can compare the two without holding two implementations in
    their head.
    """
    if not bars:
        raise ValueError("no history to build features from")
    if index is None:
        index = len(bars) - 1
    raw, _ = compute_raw_features(bars, lending_apr_bps)
    row = raw[index]
    return (row - mean) / std
