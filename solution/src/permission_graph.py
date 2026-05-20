from __future__ import annotations

from typing import Any

from .resource_store import InMemoryResourceStore


class PermissionGraph:
    def __init__(self, store: InMemoryResourceStore) -> None:
        self.store = store

    def build_policy_input(self, user_id: str, tenant_id: str, resource_id: str, action: str) -> dict[str, Any]:
        resource = self.store.get_resource(resource_id)
        assignment = self.store.active_assignment(user_id, tenant_id)
        role = assignment["role"] if assignment else "none"

        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "resource": dict(resource),
            "action": action,
            "role": role,
            "assignment_status": assignment["status"] if assignment else "missing",
            "groups": assignment.get("groups", []) if assignment else [],
        }
