# Tenant Permission Audit

This is an internal Translucid challenge template, not a generated candidate repo.

The template generates a production-shaped enterprise SaaS authorization challenge. It focuses on tenant-scoped RBAC/ABAC decisions, policy evidence, stale role invalidation, and access-control regression reporting.

The generated candidate repo intentionally contains flawed starter code. Candidates must repair tenant-aware authorization, policy input construction, evidence capture, and stale permission cache behavior.

## Local Simulator

Validation uses local services only:

- Postgres for users, tenants, resources, role assignments, and audit logs.
- OPA for local policy decisions through the same HTTP path candidates must preserve.

No external credentials, live policy service, customer data, or startup source code are required.

## Time Budget

- Expected candidate coding time: 70-95 minutes for senior backend/security candidates.
- Staff variant: up to 120 minutes with relationship-inheritance and stale-cache traps.
- Setup time after cached images: under 10 minutes on a normal laptop.
- Docker image pull cost: Postgres and OPA.

## Validation

```bash
make validate-solution
make validate-candidate-main-expected-failure
make render
make scan-safety
make validate-rendered-smoke
make validate-docker-integration
make validate
```

Expected starter failure markers:

- `cross_tenant_access_allowed`
- `global_admin_shortcut`
- `missing_policy_evidence`
- `stale_role_cache`
