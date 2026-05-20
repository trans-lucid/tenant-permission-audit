#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def public_cases() -> list[dict]:
    return [
        {
            "request_id": "case-own-allow",
            "user_id": "user_alpha_admin",
            "tenant_id": "tenant_alpha",
            "resource_slug": "billing-summary",
            "action": "read",
            "expected_allow": True,
        },
        {
            "request_id": "case-cross-deny",
            "user_id": "user_alpha_admin",
            "tenant_id": "tenant_beta",
            "resource_slug": "admin-console",
            "action": "write",
            "expected_allow": False,
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="candidate/fixtures/public/access_cases.jsonl")
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(case) + "\n" for case in public_cases()))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
