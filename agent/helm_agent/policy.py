"""The decision layer: what the agent proposes, and what the chain will do about it.

The split matters, so it is worth stating plainly:

* the **model** says "I would put 42% into the liquidity position",
* the **agent** posts that number as-is, with its two forecasts and a short rationale,
* the **contract** checks it against the user's envelope, against the volatility it
  measured itself and against the fee edge it measured itself, and does what is allowed.

The agent deliberately does **not** pre-clamp the allocation to the user's envelope. The
whole point of the on-chain guarantee is that the model cannot widen the user's limits; if
the agent quietly trimmed its proposals before posting them, the guarantee would never be
exercised and the ledger would never show the contract doing its job. What the agent does
do is compute, locally, exactly what the contract is going to decide, so the dashboard can
show "proposed / expected / actually executed" and a human can see the contract and the
off-chain mirror agree.

The local mirror of the contract's rules lives in `expected_chain_decision`, and the
python tests check it against the same cases the Foundry tests check on chain.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# The clamp reasons the contract uses, mirrored here so the dashboard can label a decision
# without waiting for the chain.
#
# These bit positions have to match `HelmTypes.sol` exactly: the contract packs every rule it
# applied into one byte, and the agent's off-chain prediction is only useful if it predicts the
# same byte the chain will publish.
CLAMP_NONE = 0
CLAMP_LP_ABOVE_MAX = 1 << 0
CLAMP_LP_BELOW_MIN = 1 << 1
CLAMP_RANGE_ABOVE_MAX = 1 << 2
CLAMP_RANGE_BELOW_MIN = 1 << 3
CLAMP_VOLATILITY_EXIT = 1 << 4
CLAMP_ECONOMIC_VETO = 1 << 5
CLAMP_NO_TRADE = 1 << 6

# The rejection reasons HelmReactive emits.
#
# These are bit flags in `HelmReject` (HelmReactive.sol), not a sequence, so the values are
# the bit positions and not 1, 2, 3...
REJECT_UNKNOWN_AGENT = 1 << 0
REJECT_CYCLE_MISMATCH = 1 << 1
REJECT_STALE = 1 << 2
REJECT_NO_LIMITS = 1 << 3
REJECT_PAUSED = 1 << 4
REJECT_REPLAY = 1 << 5
REJECT_BAD_INPUT = 1 << 6

REJECT_NAMES = {
    0: "none",
    REJECT_UNKNOWN_AGENT: "unknown_agent",
    REJECT_CYCLE_MISMATCH: "cycle_mismatch",
    REJECT_STALE: "stale",
    REJECT_NO_LIMITS: "no_limits",
    REJECT_PAUSED: "paused",
    REJECT_REPLAY: "replay",
    REJECT_BAD_INPUT: "bad_input",
}


def reject_reason_name(reason: int) -> str:
    """The name of one rejection reason, or the raw value when it is not a known flag."""
    if reason in REJECT_NAMES:
        return REJECT_NAMES[reason]
    names = [name for bit, name in REJECT_NAMES.items() if bit and reason & bit]
    if names:
        return "|".join(names)
    return f"unknown_{reason}"


@dataclass(frozen=True)
class Envelope:
    """The limits the user approved on chain, plus the contract's economic parameters."""

    lp_min_bps: int = 1000
    lp_max_bps: int = 6000
    range_min_bps: int = 500
    range_max_bps: int = 4000
    cooldown_sec: int = 120
    vol_exit_bps: int = 1200
    min_trade_bps: int = 200
    freshness_sec: int = 600
    min_fee_edge_bps: int = 50

    @classmethod
    def from_dict(cls, data: dict) -> "Envelope":
        return cls(
            lp_min_bps=int(data.get("lpShareMinBps", 1000)),
            lp_max_bps=int(data.get("lpShareMaxBps", 6000)),
            range_min_bps=int(data.get("rangeWidthMinBps", 500)),
            range_max_bps=int(data.get("rangeWidthMaxBps", 4000)),
            cooldown_sec=int(data.get("cooldownSec", 120)),
            vol_exit_bps=int(data.get("volExitLevelBps", 1200)),
            min_trade_bps=int(data.get("minTradeBps", 200)),
            freshness_sec=int(data.get("freshnessSec", 600)),
            min_fee_edge_bps=int(data.get("minFeeEdgeBps", 50)),
        )

    def to_dict(self) -> dict:
        return {
            "lpShareMinBps": self.lp_min_bps,
            "lpShareMaxBps": self.lp_max_bps,
            "rangeWidthMinBps": self.range_min_bps,
            "rangeWidthMaxBps": self.range_max_bps,
            "cooldownSec": self.cooldown_sec,
            "volExitLevelBps": self.vol_exit_bps,
            "minTradeBps": self.min_trade_bps,
            "freshnessSec": self.freshness_sec,
            "minFeeEdgeBps": self.min_fee_edge_bps,
        }


@dataclass
class Proposal:
    """What the agent is about to post, and what it expects the chain to do."""

    cycle_id: int
    lp_share_bps: int  # posted: the model's raw allocation
    range_width_bps: int  # posted: the model's raw band width
    forecast_vol_bps: int
    forecast_yield_bps: int
    model_allocation_bps: int
    rationale: str
    expected_lp_share_bps: int
    expected_range_width_bps: int
    expected_clamp_mask: int
    expected_no_trade: bool = False
    source: str = "model"

    @property
    def clamp_mask_name(self) -> list[str]:
        return clamp_mask_name(self.expected_clamp_mask)

    def to_json(self) -> dict:
        return {
            "cycleId": self.cycle_id,
            "lpShareBps": self.lp_share_bps,
            "rangeWidthBps": self.range_width_bps,
            "forecastVolBps": self.forecast_vol_bps,
            "forecastYieldBps": self.forecast_yield_bps,
            "modelAllocationBps": self.model_allocation_bps,
            "rationale": self.rationale,
            "expectedLpShareBps": self.expected_lp_share_bps,
            "expectedRangeWidthBps": self.expected_range_width_bps,
            "expectedClampMask": self.expected_clamp_mask,
            "expectedClampMaskName": self.clamp_mask_name,
            "expectedNoTrade": self.expected_no_trade,
            "source": self.source,
        }


def clamp_mask_name(mask: int) -> list[str]:
    """Human names for the clamp bits, in the order the contract applies them."""
    names = []
    if mask & CLAMP_LP_ABOVE_MAX:
        names.append("lp_above_max")
    if mask & CLAMP_LP_BELOW_MIN:
        names.append("lp_below_min")
    if mask & CLAMP_RANGE_ABOVE_MAX:
        names.append("range_above_max")
    if mask & CLAMP_RANGE_BELOW_MIN:
        names.append("range_below_min")
    if mask & CLAMP_ECONOMIC_VETO:
        names.append("economic_veto")
    if mask & CLAMP_VOLATILITY_EXIT:
        names.append("volatility_exit")
    if mask & CLAMP_NO_TRADE:
        names.append("no_trade")
    return names


def range_width_from_volatility(forecast_vol_bps: float, envelope: Envelope) -> int:
    """Map a volatility forecast onto a band width.

    Low volatility: a narrow band, which concentrates the position and earns more of the
    flow. High volatility: a wide band, which bleeds less when the market moves against
    the position. The raw width is deliberately not trimmed to the user's range here: the
    contract does that, and the ledger should show it doing so.
    """
    if forecast_vol_bps <= 0:
        return envelope.range_min_bps
    # 500 bps of volatility is the "calm" anchor, 3000 bps is the "violent" anchor.
    scaled = (forecast_vol_bps - 500.0) / 2500.0
    width = envelope.range_min_bps + (envelope.range_max_bps - envelope.range_min_bps) * min(1.0, max(0.0, scaled))
    return int(round(width))


def expected_chain_decision(
    lp_share_bps: int,
    range_width_bps: int,
    envelope: Envelope,
    chain_vol_bps: int,
    fee_edge_bps: int,
    fee_edge_measured: bool,
    current_lp_share_bps: int,
) -> tuple[int, int, int]:
    """What HelmReactive will do with this proposal, computed off chain.

    This mirrors `_onProposal` in `HelmReactive.sol` clause for clause: the envelope
    first, then the volatility exit, then the economic veto. The python test suite checks
    the mirror against the same cases the Foundry tests check on chain, so the dashboard
    can show an expectation that is actually true.

    The returned mask is the contract's `clampMask` byte, and the contract never puts the
    no-trade bit in it: a move that is too small is reported by a separate `NoTrade` event
    that carries the same mask. `expect_no_trade` predicts that event.
    """
    final_lp = lp_share_bps
    final_range = range_width_bps
    mask = CLAMP_NONE

    if final_lp > envelope.lp_max_bps:
        final_lp = envelope.lp_max_bps
        mask |= CLAMP_LP_ABOVE_MAX
    if final_lp < envelope.lp_min_bps:
        final_lp = envelope.lp_min_bps
        mask |= CLAMP_LP_BELOW_MIN
    if final_range > envelope.range_max_bps:
        final_range = envelope.range_max_bps
        mask |= CLAMP_RANGE_ABOVE_MAX
    if final_range < envelope.range_min_bps:
        final_range = envelope.range_min_bps
        mask |= CLAMP_RANGE_BELOW_MIN

    if chain_vol_bps > envelope.vol_exit_bps:
        final_lp = 0
        mask |= CLAMP_VOLATILITY_EXIT

    edge = fee_edge_bps if fee_edge_measured else 0
    if final_lp > 0 and edge < envelope.min_fee_edge_bps:
        final_lp = 0
        mask |= CLAMP_ECONOMIC_VETO

    return final_lp, final_range, mask


def expect_no_trade(final_lp_bps: int, envelope: Envelope, current_lp_share_bps: int) -> bool:
    """Whether the contract will refuse to move because the trade is too small.

    The contract compares the *enforced* allocation with the one it already holds, and if
    the difference is under the minimum trade it emits `NoTrade` instead of a rebalance.
    """
    delta = abs(final_lp_bps - current_lp_share_bps)
    return delta < envelope.min_trade_bps


def decide(
    cycle_id: int,
    model_allocation: float,
    forecast_vol_bps: float,
    forecast_yield_bps: float,
    envelope: Envelope,
    current_lp_share_bps: int,
    lending_rate_bps: float,
    chain_vol_bps: int = 0,
    fee_edge_bps: int = 0,
    fee_edge_measured: bool = False,
    rationale: str = "",
) -> Proposal:
    """Turn the model's raw output into the proposal the agent posts.

    The proposal carries the model's number unchanged. The chain does the enforcing; the
    agent's job is to make the best case for it and to be able to say in advance what the
    chain is likely to do with it.
    """
    model_bps = int(round(max(0.0, min(1.0, model_allocation)) * 10_000))
    range_width = range_width_from_volatility(forecast_vol_bps, envelope)

    expected_lp, expected_range, mask = expected_chain_decision(
        model_bps,
        range_width,
        envelope,
        chain_vol_bps,
        fee_edge_bps,
        fee_edge_measured,
        current_lp_share_bps,
    )
    no_trade = expect_no_trade(expected_lp, envelope, current_lp_share_bps)

    proposal = Proposal(
        cycle_id=cycle_id,
        lp_share_bps=model_bps,
        range_width_bps=range_width,
        forecast_vol_bps=int(round(forecast_vol_bps)),
        forecast_yield_bps=int(round(forecast_yield_bps)),
        model_allocation_bps=model_bps,
        rationale=rationale or template_rationale(
            model_bps=model_bps,
            range_width=range_width,
            forecast_vol_bps=forecast_vol_bps,
            forecast_yield_bps=forecast_yield_bps,
            envelope=envelope,
            lending_rate_bps=lending_rate_bps,
            chain_vol_bps=chain_vol_bps,
            fee_edge_bps=fee_edge_bps,
            fee_edge_measured=fee_edge_measured,
            expected_lp=expected_lp,
            mask=mask,
            no_trade=no_trade,
        ),
        expected_lp_share_bps=expected_lp,
        expected_range_width_bps=expected_range,
        expected_clamp_mask=mask,
        expected_no_trade=no_trade,
    )
    return proposal


def template_rationale(
    model_bps: int,
    range_width: int,
    forecast_vol_bps: float,
    forecast_yield_bps: float,
    envelope: Envelope,
    lending_rate_bps: float,
    chain_vol_bps: int,
    fee_edge_bps: int,
    fee_edge_measured: bool,
    expected_lp: int,
    mask: int,
    no_trade: bool = False,
) -> str:
    """A deterministic explanation, used whenever the language model is unavailable.

    The dashboard shows this rather than an error, because the explanation is part of the
    product and the product must not depend on a paid endpoint being up.
    """
    names = clamp_mask_name(mask)
    reasons: list[str] = []

    if forecast_yield_bps > 0:
        reasons.append(
            f"the model expects {int(forecast_yield_bps)} bps of fee yield against "
            f"{int(lending_rate_bps)} bps of lending"
        )
    if "lp_above_max" in names:
        reasons.append(f"the model's {model_bps} bps is above the {envelope.lp_max_bps} bps cap")
    if "lp_below_min" in names:
        reasons.append(f"the model's {model_bps} bps is below the {envelope.lp_min_bps} bps floor")
    if "volatility_exit" in names:
        reasons.append(
            f"the contract measured {chain_vol_bps} bps of volatility, above the "
            f"{envelope.vol_exit_bps} bps exit level"
        )
    if "economic_veto" in names:
        edge = fee_edge_bps if fee_edge_measured else 0
        reasons.append(
            f"the contract's measured fee edge is {edge} bps, under the "
            f"{envelope.min_fee_edge_bps} bps it demands"
        )
    if "no_trade" in names or no_trade:
        reasons.append(f"the move is smaller than the {envelope.min_trade_bps} bps minimum trade")
    if not reasons:
        reasons.append(f"the model proposes {model_bps} bps in a {range_width} bps band")
    return "; ".join(reasons)
