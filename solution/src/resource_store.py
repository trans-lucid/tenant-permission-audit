from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .config import DATABASE_URL


def find_runtime_root(path: Path) -> Path:
    for parent in path.parents:
        if (parent / "fixtures" / "public").exists():
            return parent
    template_candidate = path.parents[2] / "candidate"
    if (template_candidate / "fixtures" / "public").exists():
        return template_candidate
    return path.parents[1]


ROOT = find_runtime_root(Path(__file__).resolve())


class InMemoryResourceStore:
    def __init__(self) -> None:
        self.tenants: dict[str, dict[str, Any]] = {}
        self.users: dict[str, dict[str, Any]] = {}
        self.resources: dict[str, dict[str, Any]] = {}
        self.assignments: list[dict[str, Any]] = []
        self.audit_events: list[dict[str, Any]] = []

    def seed_public(self) -> None:
        fixture_dir = ROOT / "fixtures" / "public"
        seed_payload = json.loads((fixture_dir / "users.json").read_text())
        for tenant in seed_payload["tenants"]:
            self.tenants[tenant["tenant_id"]] = tenant
        for user in seed_payload["users"]:
            self.users[user["user_id"]] = user
        for resource in json.loads((fixture_dir / "resources.json").read_text())["resources"]:
            self.resources[resource["resource_id"]] = resource
        self.assignments = json.loads((fixture_dir / "assignments.json").read_text())["assignments"]

    def get_resource(self, resource_id: str) -> dict[str, Any]:
        return dict(self.resources[resource_id])

    def find_resource_by_slug(self, tenant_id: str, slug: str) -> dict[str, Any] | None:
        for resource in self.resources.values():
            if resource["tenant_id"] == tenant_id and resource["slug"] == slug:
                return dict(resource)
        return None

    def list_assignments(self, user_id: str) -> list[dict[str, Any]]:
        return [dict(item) for item in self.assignments if item["user_id"] == user_id]

    def active_assignment(self, user_id: str, tenant_id: str) -> dict[str, Any] | None:
        for assignment in self.assignments:
            if assignment["user_id"] == user_id and assignment["tenant_id"] == tenant_id and assignment["status"] == "active":
                return dict(assignment)
        return None

    def update_assignment_status(self, user_id: str, tenant_id: str, role: str, status: str) -> None:
        for assignment in self.assignments:
            if assignment["user_id"] == user_id and assignment["tenant_id"] == tenant_id and assignment["role"] == role:
                assignment["status"] = status

    def append_audit(self, event: dict[str, Any]) -> None:
        self.audit_events.append(dict(event))

    def list_audit(self) -> list[dict[str, Any]]:
        return [dict(event) for event in self.audit_events]


class PostgresResourceStore:
    def __init__(self, database_url: str = DATABASE_URL) -> None:
        self.connection = wait_for_postgres(database_url)

    def close(self) -> None:
        self.connection.close()

    def reset(self) -> None:
        with self.connection.cursor() as cur:
            cur.execute("TRUNCATE audit_events, role_assignments, resources, users, tenants RESTART IDENTITY CASCADE")
        self.connection.commit()

    def seed_public(self) -> None:
        self.reset()
        fixture_dir = ROOT / "fixtures" / "public"
        seed_payload = json.loads((fixture_dir / "users.json").read_text())
        resources = json.loads((fixture_dir / "resources.json").read_text())["resources"]
        assignments = json.loads((fixture_dir / "assignments.json").read_text())["assignments"]
        with self.connection.cursor() as cur:
            for tenant in seed_payload["tenants"]:
                cur.execute("INSERT INTO tenants (tenant_id, name) VALUES (%s, %s)", (tenant["tenant_id"], tenant["name"]))
            for user in seed_payload["users"]:
                cur.execute("INSERT INTO users (user_id, email) VALUES (%s, %s)", (user["user_id"], user["email"]))
            for resource in resources:
                cur.execute(
                    """
                    INSERT INTO resources (resource_id, tenant_id, slug, kind, classification, owner_user_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        resource["resource_id"],
                        resource["tenant_id"],
                        resource["slug"],
                        resource["kind"],
                        resource["classification"],
                        resource.get("owner_user_id"),
                    ),
                )
            for assignment in assignments:
                cur.execute(
                    """
                    INSERT INTO role_assignments (user_id, tenant_id, role, status, groups)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        assignment["user_id"],
                        assignment["tenant_id"],
                        assignment["role"],
                        assignment["status"],
                        json.dumps(assignment.get("groups", [])),
                    ),
                )
        self.connection.commit()

    def get_resource(self, resource_id: str) -> dict[str, Any]:
        with self.connection.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM resources WHERE resource_id = %s", (resource_id,))
            row = cur.fetchone()
        if not row:
            raise KeyError(resource_id)
        return dict(row)

    def find_resource_by_slug(self, tenant_id: str, slug: str) -> dict[str, Any] | None:
        with self.connection.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM resources WHERE tenant_id = %s AND slug = %s", (tenant_id, slug))
            row = cur.fetchone()
        return dict(row) if row else None

    def list_assignments(self, user_id: str) -> list[dict[str, Any]]:
        with self.connection.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM role_assignments WHERE user_id = %s ORDER BY tenant_id, role", (user_id,))
            rows = cur.fetchall()
        return [normalize_assignment(row) for row in rows]

    def active_assignment(self, user_id: str, tenant_id: str) -> dict[str, Any] | None:
        with self.connection.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT * FROM role_assignments
                WHERE user_id = %s AND tenant_id = %s AND status = 'active'
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (user_id, tenant_id),
            )
            row = cur.fetchone()
        return normalize_assignment(row) if row else None

    def update_assignment_status(self, user_id: str, tenant_id: str, role: str, status: str) -> None:
        with self.connection.cursor() as cur:
            cur.execute(
                """
                UPDATE role_assignments
                SET status = %s, updated_at = now()
                WHERE user_id = %s AND tenant_id = %s AND role = %s
                """,
                (status, user_id, tenant_id, role),
            )
        self.connection.commit()

    def append_audit(self, event: dict[str, Any]) -> None:
        with self.connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit_events (request_id, user_id, tenant_id, resource_id, action, allow, reason, evidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    event["request_id"],
                    event["user_id"],
                    event.get("tenant_id"),
                    event.get("resource_id"),
                    event["action"],
                    event["allow"],
                    event["reason"],
                    json.dumps(event.get("evidence", {})),
                ),
            )
        self.connection.commit()

    def list_audit(self) -> list[dict[str, Any]]:
        with self.connection.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM audit_events ORDER BY id")
            rows = cur.fetchall()
        return [dict(row) for row in rows]


def normalize_assignment(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    groups = normalized.get("groups", [])
    if isinstance(groups, str):
        groups = json.loads(groups)
    normalized["groups"] = groups
    return normalized


def wait_for_postgres(database_url: str = DATABASE_URL, attempts: int = 50) -> psycopg.Connection:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            connection = psycopg.connect(database_url)
            connection.execute("SELECT 1")
            return connection
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"postgres not ready: {last_error}")


def migrate(database_url: str = DATABASE_URL) -> None:
    sql = (ROOT / "migrations" / "001_init.sql").read_text()
    connection = wait_for_postgres(database_url)
    try:
        connection.execute(sql)
        connection.commit()
    finally:
        connection.close()


def main() -> None:
    import sys

    command = sys.argv[1] if len(sys.argv) > 1 else "migrate"
    if command == "migrate":
        migrate()
        print("postgres migration complete")
    elif command == "seed":
        store = PostgresResourceStore()
        try:
            store.seed_public()
            print("permission fixtures seeded")
        finally:
            store.close()
    else:
        raise SystemExit(f"unknown command: {command}")


if __name__ == "__main__":
    main()
