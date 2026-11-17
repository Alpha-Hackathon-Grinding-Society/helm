"""The explanation layer.

Helm's allocation decision is made by a trained network, but a number on its own is not a
product: the user has to be able to read *why* the model wants to move money and what the
contract is going to do about it. This module writes that sentence.

The sentence is produced by Claude through the Kite Passport paid endpoint (an x402 call
to `blockrun.ai`, about two thousandths of a dollar per call), and every call is paid on
Base, so the explanation itself has a transaction hash.

The rule that matters: the explanation is never allowed to break the agent. If the paid
endpoint is down, if the allowance is empty, if the call takes too long, the agent still
answers the cycle, with a deterministic explanation built from the same numbers. A demo
that dies because a paid API had a bad minute is not a demo.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass

DEFAULT_ENDPOINT = "https://blockrun.ai/api/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are the analyst inside Helm, an on-chain fund manager.

Helm has three parts:
1. A neural network proposes a stablecoin allocation each cycle (what share of the vault
   goes into a liquidity position, the rest stays in a lending market).
2. A smart contract on another chain clamps that proposal to limits the user approved,
   exits the position by itself when volatility is too high, and vetoes the trade when the
   fee edge it measured on chain does not beat lending.
3. The user reads your explanation and decides whether to trust the setup.

Rules for your answer:
- Two sentences at most. Plain English, no bullet points, no emoji, no markdown.
- Name the numbers that matter: the proposed allocation, the expected fee yield, the
  lending rate, and what the contract will do to the proposal.
- If the contract will clamp or veto the proposal, say so plainly and say why.
- Never claim the model guarantees a profit. It is a forecast, and the contract can refuse it.
- Do not invent numbers. Use only the numbers given to you.
"""


@dataclass
class Explanation:
    """One explanation, and where it came from."""

    text: str
    source: str  # "llm" or "template"
    model: str = ""
    cost_usd: float = 0.0
    payment_tx: str = ""
    latency_ms: int = 0
    error: str = ""

    def to_json(self) -> dict:
        return {
            "text": self.text,
            "source": self.source,
            "model": self.model,
            "costUsd": self.cost_usd,
            "paymentTx": self.payment_tx,
            "latencyMs": self.latency_ms,
            "error": self.error,
        }


def _kpass_binary() -> str | None:
    found = shutil.which("kpass")
    if found:
        return found
    for candidate in (
        os.path.expanduser("~/.local/bin/kpass"),
        "/usr/local/bin/kpass",
        "/usr/bin/kpass",
    ):
        if os.path.exists(candidate):
            return candidate
    return None


def _idempotency_key(prefix: str, payload: dict) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
    return f"{prefix}-{digest}"


def _build_prompt(proposal: dict, context: dict) -> str:
    """The user message. It carries the facts and nothing else."""
    facts = {
        "cycle": proposal.get("cycleId"),
        "model_proposed_lp_share_bps": proposal.get("modelAllocationBps"),
        "model_proposed_range_width_bps": proposal.get("rangeWidthBps"),
        "model_forecast_volatility_bps": proposal.get("forecastVolBps"),
        "model_forecast_fee_yield_bps": proposal.get("forecastYieldBps"),
        "user_limit_lp_share_min_bps": (context.get("limits") or {}).get("lpShareMinBps"),
        "user_limit_lp_share_max_bps": (context.get("limits") or {}).get("lpShareMaxBps"),
        "user_limit_volatility_exit_bps": (context.get("limits") or {}).get("volExitLevelBps"),
        "lending_rate_bps": context.get("rateBps"),
        "contract_measured_volatility_bps": context.get("chainVolBps"),
        "contract_measured_fee_edge_bps": context.get("feeEdgeBps"),
        "contract_measured_fee_edge_available": context.get("feeEdgeMeasured"),
        "contract_expected_lp_share_bps": proposal.get("expectedLpShareBps"),
        "contract_expected_clamp_reasons": proposal.get("expectedClampMaskName"),
        "vault_total_value_usd": context.get("totalValueUsd"),
        "vault_current_lp_share_bps": context.get("currentLpShareBps"),
    }
    return (
        "Here is this cycle's decision. Write the two sentences a user would need to "
        "understand it and trust it.\n\n" + json.dumps(facts, indent=2)
    )


def _extract_text(response_body: str) -> str:
    payload = json.loads(response_body)
    content = payload.get("content") or []
    for part in content:
        if part.get("type") == "text" and part.get("text"):
            return part["text"].strip()
    return ""


def explain(
    proposal: dict,
    context: dict,
    fallback_text: str,
    endpoint: str = DEFAULT_ENDPOINT,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 220,
    timeout_sec: float = 10.0,
    enabled: bool = True,
) -> Explanation:
    """Write the explanation for one cycle.

    Returns the language model's answer when it can get one, and the deterministic
    explanation otherwise. It never raises.
    """
    if not enabled:
        return Explanation(text=fallback_text, source="template", error="llm_disabled")

    binary = _kpass_binary()
    if binary is None:
        return Explanation(text=fallback_text, source="template", error="kpass_not_found")

    prompt = _build_prompt(proposal, context)
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
    }
    command = [
        binary,
        "session",
        "execute",
        "--url",
        endpoint,
        "--method",
        "POST",
        "--headers",
        json.dumps({"content-type": "application/json", "anthropic-version": "2023-06-01"}),
        "--body",
        json.dumps(body),
        "--idempotency-key",
        _idempotency_key("helm-explain", {"cycle": proposal.get("cycleId"), "prompt": prompt}),
        "--output",
        "json",
    ]

    started = time.time()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return Explanation(
            text=fallback_text,
            source="template",
            error=f"timeout after {timeout_sec:.0f}s",
            latency_ms=int((time.time() - started) * 1000),
        )

    latency_ms = int((time.time() - started) * 1000)
    if completed.returncode != 0:
        return Explanation(
            text=fallback_text,
            source="template",
            error=completed.stderr.strip()[:300] or f"exit {completed.returncode}",
            latency_ms=latency_ms,
        )

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return Explanation(
            text=fallback_text,
            source="template",
            error="the paid endpoint did not return json",
            latency_ms=latency_ms,
        )

    payment = payload.get("payment") or {}
    response_body = payment.get("response_body") or ""
    try:
        text = _extract_text(response_body)
    except json.JSONDecodeError:
        text = ""

    if not text:
        return Explanation(
            text=fallback_text,
            source="template",
            error=payload.get("hint") or "empty response",
            latency_ms=latency_ms,
        )

    amount = payment.get("amount")
    cost_usd = 0.0
    if amount is not None:
        try:
            cost_usd = float(amount) / 1_000_000
        except (TypeError, ValueError):
            cost_usd = 0.0

    transaction = ""
    payment_response = payment.get("payment_response") or {}
    if isinstance(payment_response, dict):
        transaction = payment_response.get("transaction", "") or ""

    return Explanation(
        text=text,
        source="llm",
        model=model,
        cost_usd=cost_usd,
        payment_tx=transaction,
        latency_ms=latency_ms,
    )
