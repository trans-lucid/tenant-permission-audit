CREATE TABLE IF NOT EXISTS tenants (
  tenant_id TEXT PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  email TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resources (
  resource_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
  slug TEXT NOT NULL,
  kind TEXT NOT NULL,
  classification TEXT NOT NULL DEFAULT 'internal',
  owner_user_id TEXT,
  UNIQUE (tenant_id, slug)
);

CREATE TABLE IF NOT EXISTS role_assignments (
  user_id TEXT NOT NULL REFERENCES users(user_id),
  tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
  role TEXT NOT NULL,
  status TEXT NOT NULL,
  groups JSONB NOT NULL DEFAULT '[]'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, tenant_id, role)
);

CREATE TABLE IF NOT EXISTS audit_events (
  id BIGSERIAL PRIMARY KEY,
  request_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  tenant_id TEXT,
  resource_id TEXT,
  action TEXT NOT NULL,
  allow BOOLEAN NOT NULL,
  reason TEXT NOT NULL,
  evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_resources_slug ON resources(slug);
CREATE INDEX IF NOT EXISTS idx_assignments_user_tenant ON role_assignments(user_id, tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_audit_request ON audit_events(request_id);
