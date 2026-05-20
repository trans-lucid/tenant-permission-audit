package translucid.authz

default allow = false

read_roles := {"admin", "viewer", "support"}

allow {
  input.tenant_id == input.resource.tenant_id
  input.action == "read"
  read_roles[input.role]
}

allow {
  input.tenant_id == input.resource.tenant_id
  input.action == "write"
  input.role == "admin"
}

reason = "allowed" {
  allow
}

reason = "cross_tenant" {
  not allow
  input.tenant_id != input.resource.tenant_id
}

reason = "role_not_allowed" {
  not allow
  input.tenant_id == input.resource.tenant_id
}

evidence = {
  "policy": "tenant_rbac_v1",
  "tenant_id": input.tenant_id,
  "resource_tenant_id": input.resource.tenant_id,
  "role": input.role,
  "assignment_status": input.assignment_status,
  "groups": input.groups,
}

decision = {
  "allow": allow,
  "reason": reason,
  "evidence": evidence,
}
