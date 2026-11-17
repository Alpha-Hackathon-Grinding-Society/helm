"""The live deployment: where the contracts are, and which key talks to them.

The addresses live in `deployments/base-sepolia.json`, which the deployment script writes.
The keys live outside the repository, in `deploy-keys/addresses.txt` or in the environment.
Nothing here ever prints a key.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEPLOYMENT = REPO_ROOT / "deployments" / "base-sepolia.json"
DEFAULT_KEYS = REPO_ROOT / "deploy-keys" / "addresses.txt"


def _load_keys(path: Path = DEFAULT_KEYS) -> dict[str, str]:
    keys: dict[str, str] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            name, value = line.split("=", 1)
            keys[name.strip()] = value.strip()
    for name in ("DEPLOYER_PRIVATE_KEY", "AGENT_PRIVATE_KEY"):
        env = os.environ.get(name)
        if env:
            keys[name] = env
    return keys


@dataclass
class Deployment:
    """Everything the agent needs to talk to the live Helm deployment."""

    chain_id: int
    base_rpc: str
    base_explorer: str
    lasna_rpc: str
    lasna_explorer: str
    lasna_chain_id: int
    deployer: str
    agent: str
    token: str
    lp_pool: str
    lending_pool: str
    vault: str
    reactive: str
    limits: dict
    deployer_key: str = ""
    agent_key: str = ""

    @classmethod
    def load(cls, path: Path | str = DEFAULT_DEPLOYMENT, keys_path: Path = DEFAULT_KEYS) -> "Deployment":
        record = json.loads(Path(path).read_text())
        keys = _load_keys(keys_path)
        reactive = record.get("reactive", {})
        return cls(
            chain_id=int(record.get("chainId", 84532)),
            base_rpc=record.get("rpc", "https://base-sepolia-rpc.publicnode.com"),
            base_explorer=record.get("explorer", "https://sepolia.basescan.org"),
            lasna_rpc=reactive.get("rpc", "https://lasna-rpc.rnk.dev"),
            lasna_explorer=reactive.get("explorer", "https://lasna.reactscan.net/"),
            lasna_chain_id=int(reactive.get("chainId", 5318007)),
            deployer=record.get("deployer", ""),
            agent=record.get("agent", ""),
            token=record.get("token", ""),
            lp_pool=record.get("lpPool", ""),
            lending_pool=record.get("lendingPool", ""),
            vault=record.get("vault", ""),
            reactive=reactive.get("address", ""),
            limits=record.get("limits", {}),
            deployer_key=keys.get("DEPLOYER_PRIVATE_KEY", ""),
            agent_key=keys.get("AGENT_PRIVATE_KEY", ""),
        )

    def to_json(self) -> dict:
        return {
            "chainId": self.chain_id,
            "baseRpc": self.base_rpc,
            "baseExplorer": self.base_explorer,
            "lasnaRpc": self.lasna_rpc,
            "lasnaExplorer": self.lasna_explorer,
            "lasnaChainId": self.lasna_chain_id,
            "deployer": self.deployer,
            "agent": self.agent,
            "token": self.token,
            "lpPool": self.lp_pool,
            "lendingPool": self.lending_pool,
            "vault": self.vault,
            "reactive": self.reactive,
            "limits": self.limits,
        }
