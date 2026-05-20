from __future__ import annotations

import time
from typing import Any

import requests

from .config import OPA_URL


class OpaPolicyClient:
    def __init__(self, base_url: str = OPA_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def wait_until_ready(self, attempts: int = 50) -> None:
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                response = requests.get(f"{self.base_url}/health", timeout=2)
                if response.ok:
                    return
            except Exception as exc:  # noqa: BLE001
                last_error = exc
            time.sleep(0.25)
        raise RuntimeError(f"opa not ready: {last_error}")

    def decide(self, policy_input: dict[str, Any]) -> dict[str, Any]:
        self.wait_until_ready()
        response = requests.post(
            f"{self.base_url}/v1/data/translucid/authz/decision",
            json={"input": policy_input},
            timeout=5,
        )
        response.raise_for_status()
        result = response.json().get("result")
        if not isinstance(result, dict):
            raise RuntimeError(f"OPA response missing decision: {response.text}")
        return result


class FakePolicyClient:
    def decide(self, policy_input: dict[str, Any]) -> dict[str, Any]:
        tenant_match = policy_input["tenant_id"] == policy_input["resource"]["tenant_id"]
        role = policy_input.get("role")
        action = policy_input["action"]
        allow = tenant_match and ((action == "read" and role in {"admin", "viewer", "support"}) or (action == "write" and role == "admin"))
        reason = "allowed" if allow else ("cross_tenant" if not tenant_match else "role_not_allowed")
        return {
            "allow": allow,
            "reason": reason,
            "evidence": {
                "policy": "tenant_rbac_v1",
                "tenant_id": policy_input["tenant_id"],
                "resource_tenant_id": policy_input["resource"]["tenant_id"],
                "role": role,
                "assignment_status": policy_input.get("assignment_status"),
                "groups": policy_input.get("groups", []),
            },
        }
