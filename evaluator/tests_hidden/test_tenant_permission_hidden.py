from __future__ import annotations

from src.audit import PermissionAuditLog
from src.app_api import ProtectedResourceAPI
from src.evaluator import AccessEvaluator
from src.policy_client import FakePolicyClient
from src.resource_store import InMemoryResourceStore


def seeded_api():
    store = InMemoryResourceStore()
    store.seed_public()
    evaluator = AccessEvaluator(store, policy_client=FakePolicyClient(), audit_log=PermissionAuditLog(store))
    return store, ProtectedResourceAPI(evaluator)


def test_same_slug_resources_do_not_cross_tenant_boundary():
    _store, api = seeded_api()
    response = api.access_resource(
        {
            "request_id": "hidden-same-slug",
            "user_id": "user_alpha_admin",
            "tenant_id": "tenant_alpha",
            "resource_id": "res_beta_invoice",
            "action": "read",
        }
    )
    assert response["status"] == 403
    assert response["decision"]["allow"] is False


def test_tenant_admin_is_not_global_admin_for_other_tenant_write():
    _store, api = seeded_api()
    response = api.access_resource(
        {
            "request_id": "hidden-admin-scope",
            "user_id": "user_alpha_admin",
            "tenant_id": "tenant_beta",
            "resource_slug": "admin-console",
            "action": "write",
        }
    )
    assert response["status"] == 403
    assert response["decision"]["reason"] in {"role_not_allowed", "cross_tenant"}


def test_role_revocation_after_cache_warmup_is_enforced():
    store, api = seeded_api()
    assert (
        api.access_resource(
            {
                "request_id": "hidden-cache-warm",
                "user_id": "user_alpha_admin",
                "tenant_id": "tenant_alpha",
                "resource_slug": "billing-summary",
                "action": "write",
            }
        )["status"]
        == 200
    )
    store.update_assignment_status("user_alpha_admin", "tenant_alpha", "admin", "revoked")
    denied = api.access_resource(
        {
            "request_id": "hidden-cache-revoked",
            "user_id": "user_alpha_admin",
            "tenant_id": "tenant_alpha",
            "resource_slug": "billing-summary",
            "action": "write",
        }
    )
    assert denied["status"] == 403


def test_denied_access_includes_reason_and_policy_evidence():
    _store, api = seeded_api()
    response = api.access_resource(
        {
            "request_id": "hidden-denied-evidence",
            "user_id": "user_beta_viewer",
            "tenant_id": "tenant_beta",
            "resource_slug": "admin-console",
            "action": "write",
        }
    )
    decision = response["decision"]
    assert response["status"] == 403
    assert decision["reason"]
    assert decision["evidence"]["policy"] == "tenant_rbac_v1"
    assert decision["evidence"]["role"] == "viewer"


def test_support_group_read_is_tenant_scoped():
    _store, api = seeded_api()
    allowed = api.access_resource(
        {
            "request_id": "hidden-support-read",
            "user_id": "user_support",
            "tenant_id": "tenant_alpha",
            "resource_slug": "billing-summary",
            "action": "read",
        }
    )
    assert allowed["status"] == 200
    assert allowed["decision"]["evidence"]["groups"] == ["support-basic"]

    denied = api.access_resource(
        {
            "request_id": "hidden-support-cross",
            "user_id": "user_support",
            "tenant_id": "tenant_beta",
            "resource_slug": "billing-summary",
            "action": "read",
        }
    )
    assert denied["status"] == 403
