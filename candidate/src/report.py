from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .audit import PermissionAuditLog
from .evaluator import AccessEvaluator
from .policy_client import OpaPolicyClient
from .resource_store import PostgresResourceStore


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def build_report(events: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "tenant-permission-audit/v1",
        "summary": {
            "total": len(events),
            "allowed": sum(1 for event in events if event["allow"]),
            "denied": sum(1 for event in events if not event["allow"]),
        },
        "events": events,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="fixtures/public/access_cases.jsonl")
    parser.add_argument("--out", default="results/access_audit_report.json")
    args = parser.parse_args()

    store = PostgresResourceStore()
    try:
      evaluator = AccessEvaluator(store, policy_client=OpaPolicyClient(), audit_log=PermissionAuditLog(store))
      for case in load_cases(Path(args.cases)):
          evaluator.evaluate(case)
      report = build_report(store.list_audit())
    finally:
      store.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str) + "\n")
    (out.parent / "summary.md").write_text(
        f"# Tenant Permission Audit Summary\n\nTotal decisions: {report['summary']['total']}\n"
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
