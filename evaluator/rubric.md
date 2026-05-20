# Evaluator Rubric

Total: 100 points

- Tenant boundary correctness: 25
- RBAC/ABAC and assignment freshness: 20
- Policy decision service integration: 15
- Audit evidence and denied reason quality: 20
- Regression report quality: 10
- Code quality and simulator discipline: 10

Major deductions:

- Treating `admin` as global instead of tenant-scoped.
- Rewriting resource tenant metadata before policy evaluation.
- Returning allow/deny without policy evidence.
- Caching role data without revocation invalidation.
- Bypassing Postgres or OPA in the integration path.
