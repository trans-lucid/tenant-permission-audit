from __future__ import annotations

from typing import Any

from .audit import PermissionAuditLog
from .permission_graph import PermissionGraph
from .policy_client import FakePolicyClient
from .resource_store import InMemoryResourceStore


class AccessEvaluator:
    def __init__(
        self,
        store: InMemoryResourceStore,
        policy_client: FakePolicyClient | None = None,
        graph: PermissionGraph | None = None,
        audit_log: PermissionAuditLog | None = None,
    ) -> None:
        self.store = store
        self.policy_client = policy_client or FakePolicyClient()
        self.graph = graph or PermissionGraph(store)
        self.audit_log = audit_log or PermissionAuditLog(store)

    def evaluate(self, case: dict[str, Any]) -> dict[str, Any]:
        resource = case.get("resource_id")
        if not resource:
            match = self.store.find_resource_by_slug(case["tenant_id"], case["resource_slug"])
            if not match:
                raise KeyError(f"resource not found for tenant={case['tenant_id']} slug={case['resource_slug']}")
            resource = match["resource_id"]

        policy_input = self.graph.build_policy_input(case["user_id"], case["tenant_id"], resource, case["action"])
        policy_decision = self.policy_client.decide(policy_input)

        # Starter bug: the service records only the final boolean, not the
        # policy evidence needed to explain allow/deny decisions.
        decision = {
            "request_id": case["request_id"],
            "user_id": case["user_id"],
            "tenant_id": case["tenant_id"],
            "resource_id": resource,
            "action": case["action"],
            "allow": bool(policy_decision["allow"]),
            "reason": policy_decision.get("reason", "unknown"),
            "evidence": {},
        }
        self.audit_log.append_decision(decision)
        return decision
