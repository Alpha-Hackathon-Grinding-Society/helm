"""Configuration for the Helm agent.

Every setting can come from the environment so that the same code runs in a test, in a
container, and on a laptop without edits. Nothing here has a secret in it: the agent key
lives in `HELM_AGENT_PRIVATE_KEY` and is never written to disk by this package.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "agent" / "data"
MODEL_DIR = REPO_ROOT / "agent" / "models"


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw not in (None, "") else default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    return float(raw) if raw not in (None, "") else default


@dataclass(frozen=True)
class NetworkConfig:
    """Where the agent reads from and writes to."""

    chain_id: int = 84532
    rpc_url: str = "https://base-sepolia-rpc.publicnode.com"
    explorer: str = "https://sepolia.basescan.org"
    vault_address: str = ""
    token_address: str = ""
    lp_pool_address: str = ""
    lending_pool_address: str = ""
    reactive_address: str = ""
    callback_proxy: str = "0x476F44b11F5C942c58f4c8E3d0300E5710743585"
    agent_private_key: str = ""
    agent_address: str = ""

    @classmethod
    def from_env(cls) -> "NetworkConfig":
        return cls(
            chain_id=_env_int("HELM_CHAIN_ID", 84532),
            rpc_url=os.environ.get("HELM_RPC_URL", "https://base-sepolia-rpc.publicnode.com"),
            vault_address=os.environ.get("HELM_VAULT", ""),
            token_address=os.environ.get("HELM_TOKEN", ""),
            lp_pool_address=os.environ.get("HELM_LP_POOL", ""),
            lending_pool_address=os.environ.get("HELM_LENDING_POOL", ""),
            reactive_address=os.environ.get("HELM_REACTIVE", ""),
            agent_private_key=os.environ.get("HELM_AGENT_PRIVATE_KEY", ""),
            agent_address=os.environ.get("HELM_AGENT_ADDRESS", ""),
        )


@dataclass(frozen=True)
class LlmConfig:
    """The Kite Passport backed Anthropic endpoint, used for explanations.

    The agent never *needs* the model to run. If the allowance is empty or the endpoint is
    down, `helm_agent.llm.explain` falls back to a deterministic template so the demo
    always has an explanation.
    """

    enabled: bool = True
    base_url: str = "https://api.kite.ai/v1/blockrun"
    api_key: str = ""
    model: str = "claude-sonnet-4-5"
    max_tokens: int = 320
    timeout_sec: float = 25.0

    @classmethod
    def from_env(cls) -> "LlmConfig":
        return cls(
            enabled=os.environ.get("HELM_LLM", "1") != "0",
            base_url=os.environ.get("HELM_LLM_BASE_URL", "https://api.kite.ai/v1/blockrun"),
            api_key=os.environ.get("HELM_LLM_API_KEY", os.environ.get("KITE_API_KEY", "")),
            model=os.environ.get("HELM_LLM_MODEL", "claude-sonnet-4-5"),
            max_tokens=_env_int("HELM_LLM_MAX_TOKENS", 320),
            timeout_sec=_env_float("HELM_LLM_TIMEOUT", 25.0),
        )


@dataclass(frozen=True)
class PolicyConfig:
    """The shape of the decision.

    `min_trade_bps` mirrors the contract: a move smaller than this is not worth a
    transaction, so the agent does not even post it.
    """

    min_trade_bps: int = 200
    range_width_bps: int = 1500
    max_range_width_bps: int = 4000
    min_range_width_bps: int = 500


@dataclass(frozen=True)
class AgentConfig:
    network: NetworkConfig = field(default_factory=NetworkConfig)
    llm: LlmConfig = field(default_factory=LlmConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    data_dir: Path = DATA_DIR
    model_dir: Path = MODEL_DIR
    poll_interval_sec: float = 4.0

    @classmethod
    def load(cls) -> "AgentConfig":
        return cls(
            network=NetworkConfig.from_env(),
            llm=LlmConfig.from_env(),
            policy=PolicyConfig(),
        )
