from __future__ import annotations

from src.audit import PermissionAuditLog
from src.app_api import ProtectedResourceAPI
from src.evaluator import AccessEvaluator
from src.policy_client import FakePolicyClient
from src.resource_store import InMemoryResourceStore


def seeded_store() -> InMemoryResourceStore:
    store = InMemoryResourceStore()
    store.seed_public()
    return store


def test_reference_solution_handles_tenant_boundary_evidence_and_revocation():
    store = seeded_store()
    api = ProtectedResourceAPI(AccessEvaluator(store, policy_client=FakePolicyClient(), audit_log=PermissionAuditLog(store)))

    allowed = api.access_resource(
        {
            "request_id": "ref-allow",
            "user_id": "user_alpha_admin",
            "tenant_id": "tenant_alpha",
            "resource_slug": "billing-summary",
            "action": "read",
        }
    )
    assert allowed["status"] == 200
    assert allowed["decision"]["evidence"]["policy"] == "tenant_rbac_v1"

    cross = api.access_resource(
        {
            "request_id": "ref-cross",
            "user_id": "user_alpha_admin",
            "tenant_id": "tenant_beta",
            "resource_id": "res_beta_admin",
            "action": "write",
        }
    )
    assert cross["status"] == 403
    assert cross["decision"]["reason"] == "role_not_allowed"

    store.update_assignment_status("user_alpha_admin", "tenant_alpha", "admin", "revoked")
    revoked = api.access_resource(
        {
            "request_id": "ref-revoked",
            "user_id": "user_alpha_admin",
            "tenant_id": "tenant_alpha",
            "resource_slug": "billing-summary",
            "action": "write",
        }
    )
    assert revoked["status"] == 403
