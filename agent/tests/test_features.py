"""The features must not be able to see the future.

This is the test that decides whether the backtest means anything. If a feature at hour
`t` can see hour `t + 1`, then the model is being trained on the answer.
"""

import math

import numpy as np

from helm_agent.data import Bar, fill_gaps
from helm_agent.features import build_dataset, compute_raw_features, live_features


def make_bars(count: int = 600, seed: int = 3) -> list[Bar]:
    """A synthetic but well behaved hourly market: a random walk with real depth."""
    rng = np.random.default_rng(seed)
    price = 2000.0
    start = 1_700_000_000 - (count % 24) * 3600
    bars: list[Bar] = []
    for i in range(count):
        price *= math.exp(float(rng.normal(0.0, 0.004)))
        volume = float(abs(rng.normal(250_000.0, 60_000.0))) + 1_000.0
        bars.append(
            Bar(
                timestamp=start + i * 3600,
                price=price,
                volume_usd=volume,
                fees_usd=volume * 0.0005,
                swaps=int(rng.integers(5, 200)),
                liquidity=2.0e19 * (1.0 + 0.01 * float(rng.normal())),
                tvl_usd=1.2e9 * (1.0 + 0.01 * float(rng.normal())),
            )
        )
    return bars


def test_a_feature_row_does_not_change_when_the_future_changes() -> None:
    bars = make_bars()
    before, _ = compute_raw_features(bars)

    # rewrite the second half of the market, violently
    changed = [Bar(**{**bar.__dict__}) for bar in bars]
    for bar in changed[len(bars) // 2 :]:
        bar.price *= 3.0
        bar.volume_usd *= 10.0
        bar.fees_usd *= 10.0
    after, _ = compute_raw_features(changed)

    cutoff = len(bars) // 2
    assert np.allclose(before[:cutoff], after[:cutoff]), "a trailing feature used future data"


def test_live_features_match_the_training_matrix() -> None:
    bars = make_bars()
    dataset = build_dataset(bars)
    row = live_features(bars, dataset.mean, dataset.std)

    # the same bar, computed through the dataset path
    index = len(bars) - 1
    raw, _ = compute_raw_features(bars)
    expected = (raw[index] - dataset.mean) / dataset.std
    assert np.allclose(row, expected)


def test_the_dataset_has_no_rows_without_a_known_future() -> None:
    bars = make_bars(400)
    dataset = build_dataset(bars, horizon_hours=24, warmup_hours=168)
    assert len(dataset) == 400 - 168 - 24
    assert np.isfinite(dataset.features).all()
    assert np.isfinite(dataset.labels[:, 1]).all()
    assert np.isfinite(dataset.labels[:, 2]).all()


def test_fill_gaps_makes_the_series_contiguous() -> None:
    bars = [
        Bar(timestamp=0, price=100.0, volume_usd=10.0, fees_usd=1.0, swaps=2, liquidity=1.0, tvl_usd=100.0),
        Bar(timestamp=7200, price=110.0, volume_usd=20.0, fees_usd=2.0, swaps=3, liquidity=1.0, tvl_usd=100.0),
    ]
    filled = fill_gaps(bars)
    assert [bar.timestamp for bar in filled] == [0, 3600, 7200]
    assert filled[1].volume_usd == 0.0
    assert filled[1].fees_usd == 0.0
    assert filled[1].price == 100.0  # carried forward


def test_the_fee_yield_is_annualised_against_the_depth() -> None:
    # 10 USD of fees on 1,000,000 USD of depth for one hour is 8.77% a year.
    from helm_agent.features import annualise_fee_yield

    apr = annualise_fee_yield(10.0, 1_000_000.0, 1.0)
    assert math.isclose(apr, 10.0 / 1_000_000.0 * 8766.0 * 10_000, rel_tol=1e-9)
    assert apr < 1000.0
