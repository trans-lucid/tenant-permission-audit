from __future__ import annotations

from typing import Any

from .resource_store import InMemoryResourceStore


class PermissionGraph:
    def __init__(self, store: InMemoryResourceStore) -> None:
        self.store = store
        self._role_cache: dict[str, dict[str, Any]] = {}

    def build_policy_input(self, user_id: str, tenant_id: str, resource_id: str, action: str) -> dict[str, Any]:
        resource = self.store.get_resource(resource_id)
        assignment = self._cached_assignment(user_id)

        # Starter bug: this rewrites the resource tenant to match the requested
        # tenant and treats admin as global. OPA gets a misleading input.
        role = assignment["role"] if assignment else "none"
        input_resource = dict(resource)
        input_resource["tenant_id"] = tenant_id

        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "resource": input_resource,
            "action": action,
            "role": role,
            "assignment_status": assignment["status"] if assignment else "missing",
            "groups": assignment.get("groups", []) if assignment else [],
        }

    def _cached_assignment(self, user_id: str) -> dict[str, Any] | None:
        # Starter bug: cache is keyed only by user_id, so tenant changes and
        # role revocations are invisible after the first decision.
        if user_id not in self._role_cache:
            assignments = self.store.list_assignments(user_id)
            active = [item for item in assignments if item["status"] == "active"]
            admin = next((item for item in active if item["role"] == "admin"), None)
            self._role_cache[user_id] = admin or (active[0] if active else {})
        return self._role_cache[user_id] or None
