# Source Dossier: Tenant Permission Audit

This template uses public sources only as architecture references. The candidate code, fixtures, tests, hidden evaluator, and rubrics are original Translucid-owned material.

## Sources Studied

- Open Policy Agent: policy-as-code service shape, REST decision API, and Rego-style policy evidence.
- Casbin: RBAC/ABAC/ACL model vocabulary and policy-rule fixture concepts.
- SpiceDB: Zanzibar-inspired relationship authorization terminology and fine-grained permission graph concepts.
- OpenFGA: readable authorization models and relationship tuple ideas for future hard-mode variants.

## Allowed Reuse

- Architecture concepts such as policy decision services, role assignments, tenant-scoped resources, permission graphs, evidence trails, and regression case files.
- Generic RBAC/ABAC/ACL terminology.
- Local service patterns for Postgres and OPA.

## Forbidden

- Copying source code from OPA, Casbin, SpiceDB, OpenFGA, or customer repositories.
- Copying real authorization models, production roles, customer schemas, policy files, or access logs.
- Requiring live policy engines, cloud services, or credentials.
- Turning a connected startup repo into the generated challenge repo unless source-slice mode is explicitly approved.
