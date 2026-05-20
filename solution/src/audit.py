from __future__ import annotations

from typing import Any

from .resource_store import InMemoryResourceStore


class PermissionAuditLog:
    def __init__(self, store: InMemoryResourceStore) -> None:
        self.store = store

    def append_decision(self, decision: dict[str, Any]) -> None:
        self.store.append_audit(
            {
                "request_id": decision["request_id"],
                "user_id": decision["user_id"],
                "tenant_id": decision.get("tenant_id"),
                "resource_id": decision.get("resource_id"),
                "action": decision["action"],
                "allow": decision["allow"],
                "reason": decision["reason"],
                "evidence": decision.get("evidence", {}),
            }
        )

    def list_events(self) -> list[dict[str, Any]]:
        return self.store.list_audit()
