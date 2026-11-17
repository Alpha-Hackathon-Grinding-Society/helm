"""The backtest's arithmetic, and the baselines it compares against."""

import math

from helm_agent.backtest import (
    _fee_share,
    _lp_value_multiplier,
    best_rate_now_weights,
    simulate_path,
    simulate_window,
)
from helm_agent.data import Bar


def bar(timestamp: int, price: float, volume: float = 0.0, fees: float = 0.0, tvl: float = 0.0, liquidity: float = 0.0) -> Bar:
    return Bar(
        timestamp=timestamp,
        price=price,
        volume_usd=volume,
        fees_usd=fees,
        swaps=1 if volume else 0,
        liquidity=liquidity,
        tvl_usd=tvl,
    )


def test_the_lp_value_follows_the_constant_product_formula() -> None:
    # A full range position's value grows by sqrt(P1/P0). A 2x price is +41.4%.
    assert math.isclose(_lp_value_multiplier(2000.0, 4000.0), math.sqrt(2.0), rel_tol=1e-12)
    assert math.isclose(_lp_value_multiplier(2000.0, 2000.0), 1.0, rel_tol=1e-12)


def test_the_fee_share_is_the_position_value_over_the_pool_value() -> None:
    # A full range position earns the share of the pool's fees that its value is worth.
    assert math.isclose(_fee_share(100_000.0, 10_000_000.0), 0.01, rel_tol=1e-12)
    assert math.isclose(_fee_share(0.0, 10_000_000.0), 0.0)
    assert math.isclose(_fee_share(100_000.0, 0.0), 0.0)
    # a position bigger than the pool cannot earn more than the pool has
    assert _fee_share(20_000_000.0, 10_000_000.0) == 1.0


def test_the_liquidity_position_actually_earns_the_fees() -> None:
    # 10,000 dollars of fees in a pool worth 10 million, for a position worth 100,000:
    # the position is one percent of the pool, so it earns one percent of the fees.
    # The position grows as it earns, so the three bars earn 100, 100.10 and 100.20.
    bars = [bar(i * 3600, 2000.0, fees=10_000.0, tvl=10_000_000.0, liquidity=1e19) for i in range(4)]
    lp = simulate_path(bars, [1.0] * len(bars), 0.0, 100_000.0, 0.0, "all_lp")
    assert math.isclose(lp.fees_earned, 300.3001, rel_tol=1e-9)


def test_all_lending_beats_all_lp_when_the_fees_do_not_pay() -> None:
    bars = [bar(i * 3600, 2000.0, fees=1.0, tvl=10_000_000.0, liquidity=1e19) for i in range(48)]
    lending = simulate_path(bars, [0.0] * len(bars), 300.0, 100_000.0, 0.0, "all_lending")
    lp = simulate_path(bars, [1.0] * len(bars), 300.0, 100_000.0, 0.0, "all_lp")
    assert lending.total_return > lp.total_return


def test_the_window_simulation_is_the_same_mathematics_as_the_path() -> None:
    bars = [bar(i * 3600, 2000.0 + i * 5, fees=2.0, tvl=1_000_000.0, liquidity=1e19) for i in range(30)]
    window_value = simulate_window(bars, 0, 24, 0.5, 300.0, 100_000.0, 0.0)
    path = simulate_path(bars[:25], [0.5] * 25, 300.0, 100_000.0, 0.0, "model")
    assert math.isclose(window_value, path.equity[-1], rel_tol=1e-9)


def test_the_backtest_is_deterministic() -> None:
    bars = [bar(i * 3600, 2000.0 + (i % 7), fees=1.5, tvl=1_000_000.0, liquidity=1e19) for i in range(100)]
    first = simulate_path(bars, [0.3] * len(bars), 300.0, 100_000.0, 5.0, "model")
    second = simulate_path(bars, [0.3] * len(bars), 300.0, 100_000.0, 5.0, "model")
    assert first.to_json() == second.to_json()


def test_rebalancing_costs_money() -> None:
    bars = [bar(i * 3600, 2000.0) for i in range(20)]
    free = simulate_path(bars, [0.0, 0.5] + [0.5] * 18, 300.0, 100_000.0, 0.0, "free")
    costly = simulate_path(bars, [0.0, 0.5] + [0.5] * 18, 300.0, 100_000.0, 50.0, "costly")
    assert costly.total_return < free.total_return
    assert costly.trades == free.trades


def test_best_rate_now_moves_to_whichever_venue_pays_more() -> None:
    # hour 0: the pool paid a fee yield above lending, so the next hour it is all LP
    bars = [
        bar(0, 2000.0, fees=1000.0, tvl=1_000_000.0, liquidity=1e19),  # 876% a year
        bar(3600, 2000.0, fees=1.0, tvl=1_000_000.0, liquidity=1e19),  # 0.88% a year
        bar(7200, 2000.0, fees=1000.0, tvl=1_000_000.0, liquidity=1e19),
    ]
    weights = best_rate_now_weights(bars, 300.0)
    assert weights[0] == 0.0  # nothing is known before the first hour
    assert weights[1] == 1.0  # the first hour paid well
    assert weights[2] == 0.0  # the second hour did not
