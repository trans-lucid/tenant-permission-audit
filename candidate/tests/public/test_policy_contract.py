from __future__ import annotations

from load_target import load


audit_module = load("src.audit")
app_api_module = load("src.app_api")
evaluator_module = load("src.evaluator")
policy_client_module = load("src.policy_client")
resource_store_module = load("src.resource_store")


def seeded_store():
    store = resource_store_module.InMemoryResourceStore()
    store.seed_public()
    return store


def evaluator_for(store):
    return evaluator_module.AccessEvaluator(
        store,
        policy_client=policy_client_module.FakePolicyClient(),
        audit_log=audit_module.PermissionAuditLog(store),
    )


def test_tenant_admin_can_access_own_tenant_resource():
    store = seeded_store()
    api = app_api_module.ProtectedResourceAPI(evaluator_for(store))

    response = api.access_resource(
        {
            "request_id": "unit-own-allow",
            "user_id": "user_alpha_admin",
            "tenant_id": "tenant_alpha",
            "resource_slug": "billing-summary",
            "action": "read",
        }
    )

    assert response["status"] == 200
    assert response["decision"]["allow"] is True


def test_tenant_admin_cannot_access_other_tenant_resource():
    store = seeded_store()
    api = app_api_module.ProtectedResourceAPI(evaluator_for(store))

    response = api.access_resource(
        {
            "request_id": "unit-cross-tenant",
            "user_id": "user_alpha_admin",
            "tenant_id": "tenant_beta",
            "resource_id": "res_beta_admin",
            "action": "write",
        }
    )

    assert response["status"] == 403, "cross_tenant_access_allowed: tenant_alpha admin must not write tenant_beta resource"


def test_tenant_admin_is_not_global_admin_for_write():
    store = seeded_store()
    api = app_api_module.ProtectedResourceAPI(evaluator_for(store))

    response = api.access_resource(
        {
            "request_id": "unit-global-admin",
            "user_id": "user_alpha_admin",
            "tenant_id": "tenant_beta",
            "resource_slug": "admin-console",
            "action": "write",
        }
    )

    assert response["decision"]["allow"] is False, "global_admin_shortcut: admin in one tenant is not admin everywhere"


def test_audit_result_includes_policy_evidence():
    store = seeded_store()
    api = app_api_module.ProtectedResourceAPI(evaluator_for(store))

    response = api.access_resource(
        {
            "request_id": "unit-evidence",
            "user_id": "user_beta_viewer",
            "tenant_id": "tenant_beta",
            "resource_slug": "billing-summary",
            "action": "read",
        }
    )

    evidence = response["decision"].get("evidence", {})
    assert evidence.get("policy") == "tenant_rbac_v1", "missing_policy_evidence: decision must include policy evidence"
    assert store.list_audit()[0]["evidence"].get("policy") == "tenant_rbac_v1", (
        "missing_policy_evidence: audit log must persist policy evidence"
    )


def test_role_revocation_invalidates_permission_cache():
    store = seeded_store()
    evaluator = evaluator_for(store)
    api = app_api_module.ProtectedResourceAPI(evaluator)

    first = api.access_resource(
        {
            "request_id": "unit-cache-warm",
            "user_id": "user_alpha_admin",
            "tenant_id": "tenant_alpha",
            "resource_slug": "billing-summary",
            "action": "write",
        }
    )
    assert first["status"] == 200

    store.update_assignment_status("user_alpha_admin", "tenant_alpha", "admin", "revoked")
    second = api.access_resource(
        {
            "request_id": "unit-cache-revoked",
            "user_id": "user_alpha_admin",
            "tenant_id": "tenant_alpha",
            "resource_slug": "billing-summary",
            "action": "write",
        }
    )

    assert second["status"] == 403, "stale_role_cache: role revocation must be visible to later decisions"
