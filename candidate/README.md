# Tenant Permission Audit

You are inheriting an enterprise SaaS permission layer where cross-tenant records can leak and access can be granted from stale role assumptions.

Repair tenant-aware authorization, policy input construction, policy evidence, stale role invalidation, and access regression reporting.

## Local Services

```txt
Postgres   users, tenants, resources, role assignments, audit log
OPA        local policy decision service
```

No real policy service, cloud credentials, or customer data are needed.

## Time Budget

- Setup: about 5-10 minutes after Docker images are available.
- Coding: about 70-95 minutes for the standard challenge.
- Staff variant: up to 120 minutes with stricter inheritance and cache invalidation cases.

## Commands

```bash
make dev
make seed
make test
make test-integration
make run
make clean
```

Final validation includes harder tenant-collision, role-revocation, group-inheritance, denied-reason, and admin-scope cases. Do not hardcode fixture IDs or bypass Postgres/OPA.
