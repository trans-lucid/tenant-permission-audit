from __future__ import annotations

from load_target import load


audit_module = load("src.audit")
app_api_module = load("src.app_api")
evaluator_module = load("src.evaluator")
policy_client_module = load("src.policy_client")
resource_store_module = load("src.resource_store")


def test_public_docker_access_path_uses_postgres_and_opa():
    store = resource_store_module.PostgresResourceStore()
    try:
        store.seed_public()
        policy = policy_client_module.OpaPolicyClient()
        evaluator = evaluator_module.AccessEvaluator(store, policy_client=policy, audit_log=audit_module.PermissionAuditLog(store))
        api = app_api_module.ProtectedResourceAPI(evaluator)

        own = api.access_resource(
            {
                "request_id": "int-own-allow",
                "user_id": "user_alpha_admin",
                "tenant_id": "tenant_alpha",
                "resource_slug": "billing-summary",
                "action": "read",
            }
        )
        assert own["status"] == 200

        cross = api.access_resource(
            {
                "request_id": "int-cross-deny",
                "user_id": "user_alpha_admin",
                "tenant_id": "tenant_beta",
                "resource_id": "res_beta_admin",
                "action": "write",
            }
        )
        assert cross["status"] == 403, "cross_tenant_access_allowed: Docker path must deny tenant admin crossing tenants"

        evidence = store.list_audit()[-1]["evidence"]
        assert evidence.get("policy") == "tenant_rbac_v1", "missing_policy_evidence: Docker path must persist OPA evidence"
    finally:
        store.close()
