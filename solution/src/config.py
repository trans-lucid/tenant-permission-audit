from __future__ import annotations

import os


DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/permissions")
OPA_URL = os.environ.get("OPA_URL", "http://localhost:8181")
