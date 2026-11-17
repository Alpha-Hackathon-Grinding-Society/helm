"""The off-chain mirror of HelmReactive's rules has to agree with the contract.

The cases below are the same cases the Foundry suite in `contracts/test/HelmReactive.t.sol`
puts on chain. If the contract changes and this mirror does not, the dashboard starts
lying about what the chain is going to do.
"""

from helm_agent.policy import (
    CLAMP_ECONOMIC_VETO,
    CLAMP_LP_ABOVE_MAX,
    CLAMP_LP_BELOW_MIN,
    CLAMP_NONE,
    CLAMP_NO_TRADE,
    CLAMP_RANGE_ABOVE_MAX,
    CLAMP_RANGE_BELOW_MIN,
    CLAMP_VOLATILITY_EXIT,
    REJECT_BAD_INPUT,
    REJECT_CYCLE_MISMATCH,
    REJECT_NAMES,
    REJECT_NO_LIMITS,
    REJECT_PAUSED,
    REJECT_REPLAY,
    REJECT_STALE,
    REJECT_UNKNOWN_AGENT,
    Envelope,
    clamp_mask_name,
    decide,
    expect_no_trade,
    expected_chain_decision,
    reject_reason_name,
)

ENVELOPE = Envelope(
    lp_min_bps=1000,
    lp_max_bps=6000,
    range_min_bps=500,
    range_max_bps=4000,
    cooldown_sec=120,
    vol_exit_bps=1200,
    min_trade_bps=200,
    freshness_sec=600,
    min_fee_edge_bps=50,
)


def test_the_clamp_bits_are_the_bits_the_contract_uses() -> None:
    """The contract packs the rules it applied into one byte.

    `HelmTypes.sol` is the authority: the volatility exit is bit 4 and the economic veto is
    bit 5. If these two are swapped the agent predicts the wrong byte, and the dashboard
    labels a decision with the wrong reason.
    """
    assert CLAMP_LP_ABOVE_MAX == 1 << 0
    assert CLAMP_LP_BELOW_MIN == 1 << 1
    assert CLAMP_RANGE_ABOVE_MAX == 1 << 2
    assert CLAMP_RANGE_BELOW_MIN == 1 << 3
    assert CLAMP_VOLATILITY_EXIT == 1 << 4
    assert CLAMP_ECONOMIC_VETO == 1 << 5
    assert CLAMP_NO_TRADE == 1 << 6

    # and the names decode the same way
    assert clamp_mask_name(CLAMP_VOLATILITY_EXIT) == ["volatility_exit"]
    assert clamp_mask_name(CLAMP_ECONOMIC_VETO) == ["economic_veto"]
    assert clamp_mask_name(CLAMP_LP_ABOVE_MAX | CLAMP_ECONOMIC_VETO) == [
        "lp_above_max",
        "economic_veto",
    ]


def decision(lp: int, width: int, **kwargs):
    defaults = dict(
        chain_vol_bps=0,
        fee_edge_bps=0,
        fee_edge_measured=False,
        current_lp_share_bps=0,
    )
    defaults.update(kwargs)
    return expected_chain_decision(lp, width, ENVELOPE, **defaults)


def test_a_proposal_inside_the_envelope_is_left_alone() -> None:
    lp, width, mask = decision(3000, 1500, fee_edge_bps=200, fee_edge_measured=True)
    assert (lp, width, mask) == (3000, 1500, 0)


def test_a_proposal_above_the_cap_is_pulled_down() -> None:
    lp, _, mask = decision(9000, 1500, fee_edge_bps=200, fee_edge_measured=True)
    assert lp == 6000
    assert mask & CLAMP_LP_ABOVE_MAX


def test_a_proposal_below_the_floor_is_pushed_up() -> None:
    lp, _, mask = decision(0, 1500, fee_edge_bps=200, fee_edge_measured=True)
    assert lp == 1000
    assert mask & CLAMP_LP_BELOW_MIN


def test_the_range_is_clamped_on_both_sides() -> None:
    lp, width, mask = decision(3000, 9000, fee_edge_bps=200, fee_edge_measured=True)
    assert width == 4000
    assert mask & CLAMP_RANGE_ABOVE_MAX

    lp, width, mask = decision(3000, 10, fee_edge_bps=200, fee_edge_measured=True)
    assert width == 500
    assert mask & CLAMP_RANGE_BELOW_MIN


def test_high_volatility_forces_the_position_to_zero() -> None:
    lp, _, mask = decision(3000, 1500, chain_vol_bps=1500, fee_edge_bps=200, fee_edge_measured=True)
    assert lp == 0
    assert mask & CLAMP_VOLATILITY_EXIT


def test_an_unmeasured_fee_edge_is_not_a_positive_fee_edge() -> None:
    lp, _, mask = decision(3000, 1500, fee_edge_bps=0, fee_edge_measured=False)
    assert lp == 0
    assert mask & CLAMP_ECONOMIC_VETO


def test_a_measured_edge_below_the_margin_is_vetoed() -> None:
    lp, _, mask = decision(3000, 1500, fee_edge_bps=49, fee_edge_measured=True)
    assert lp == 0
    assert mask & CLAMP_ECONOMIC_VETO


def test_a_small_move_is_a_no_trade() -> None:
    # The contract does not put the no-trade bit in its clamp mask: a move that is too
    # small is reported by a separate `NoTrade` event carrying the same mask. The mirror
    # has to predict that event, and has to leave the mask byte alone.
    lp, _, mask = decision(1050, 1500, fee_edge_bps=200, fee_edge_measured=True, current_lp_share_bps=1000)
    assert lp == 1050
    assert mask == CLAMP_NONE
    assert expect_no_trade(lp, ENVELOPE, 1000) is True
    assert expect_no_trade(lp, ENVELOPE, 0) is False


def test_the_reject_reasons_are_the_bit_flags_the_contract_uses() -> None:
    """`HelmReject` is a set of flags, not a sequence.

    Reading them as 1, 2, 3 would label a `cycle_mismatch` (2) as "paused" and hide the
    real reason from the dashboard.
    """
    assert REJECT_UNKNOWN_AGENT == 1 << 0
    assert REJECT_CYCLE_MISMATCH == 1 << 1
    assert REJECT_STALE == 1 << 2
    assert REJECT_NO_LIMITS == 1 << 3
    assert REJECT_PAUSED == 1 << 4
    assert REJECT_REPLAY == 1 << 5
    assert REJECT_BAD_INPUT == 1 << 6

    assert reject_reason_name(REJECT_CYCLE_MISMATCH) == "cycle_mismatch"
    assert reject_reason_name(REJECT_STALE) == "stale"
    assert reject_reason_name(REJECT_PAUSED) == "paused"
    assert reject_reason_name(REJECT_NO_LIMITS) == "no_limits"
    assert reject_reason_name(0) == "none"
    assert reject_reason_name(128) == "unknown_128"
    assert reject_reason_name(REJECT_NO_LIMITS | REJECT_BAD_INPUT) == "no_limits|bad_input"
    assert set(REJECT_NAMES.values()) == {
        "none",
        "unknown_agent",
        "cycle_mismatch",
        "stale",
        "no_limits",
        "paused",
        "replay",
        "bad_input",
    }


def test_the_predicted_mask_is_the_byte_the_contract_publishes() -> None:
    # The model asks for 71%, the cap is 60%, the edge is healthy: the contract clamps to
    # 60% and publishes mask 1 (LP_ABOVE_MAX) with no other bit set.
    lp, _, mask = decision(7102, 4000, fee_edge_bps=500, fee_edge_measured=True)
    assert lp == 6000
    assert mask == CLAMP_LP_ABOVE_MAX


def test_the_agent_posts_the_model_number_unchanged() -> None:
    # The agent does not pre-clamp: the chain is the thing that enforces the envelope,
    # and the ledger has to show the contract doing it.
    proposal = decide(
        cycle_id=7,
        model_allocation=0.9,
        forecast_vol_bps=400.0,
        forecast_yield_bps=900.0,
        envelope=ENVELOPE,
        current_lp_share_bps=0,
        lending_rate_bps=300.0,
        chain_vol_bps=0,
        fee_edge_bps=500,
        fee_edge_measured=True,
    )
    assert proposal.lp_share_bps == 9000
    assert proposal.expected_lp_share_bps == 6000
    assert "lp_above_max" in proposal.clamp_mask_name


def test_the_rationale_names_the_rule_that_fired() -> None:
    proposal = decide(
        cycle_id=1,
        model_allocation=0.0,
        forecast_vol_bps=100.0,
        forecast_yield_bps=100.0,
        envelope=ENVELOPE,
        current_lp_share_bps=0,
        lending_rate_bps=300.0,
        chain_vol_bps=0,
        fee_edge_bps=0,
        fee_edge_measured=False,
    )
    assert "economic" in proposal.rationale.lower() or "edge" in proposal.rationale.lower()
    assert "lp_below_min" in clamp_mask_name(proposal.expected_clamp_mask)
