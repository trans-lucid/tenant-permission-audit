#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


COUNT_BY_ENTITY = {
    "low": 4,
    "medium": 12,
    "high": 36,
}

USERS = [
    "user_alpha_admin",
    "user_beta_viewer",
    "user_support",
    "user_gamma_admin",
    "user_delta_auditor",
]

TENANTS = ["tenant_alpha", "tenant_beta", "tenant_gamma", "tenant_delta"]

RESOURCES = [
    ("billing-summary", "dashboard"),
    ("admin-console", "admin_tool"),
    ("support-cases", "ticket_queue"),
    ("usage-export", "report"),
    ("customer-ledger", "ledger"),
]


def load_profile(path: str | None) -> dict:
    if not path:
        return {}
    profile_path = Path(path)
    if not profile_path.exists():
        return {}
    return json.loads(profile_path.read_text())


def profile_seed(profile: dict, fallback: int) -> int:
    try:
        return int(profile.get("generator_seed") or fallback)
    except (TypeError, ValueError):
        return fallback


def scenario_profile(profile: dict) -> dict:
    value = profile.get("scenario_profile")
    return value if isinstance(value, dict) else {}


def profile_count(profile: dict, fallback: int) -> int:
    entity_count = str(scenario_profile(profile).get("entity_count") or "").lower()
    if entity_count in COUNT_BY_ENTITY:
        return COUNT_BY_ENTITY[entity_count]
    difficulty = str(profile.get("difficulty") or profile.get("difficulty_profile") or "").lower()
    if difficulty == "junior":
        return COUNT_BY_ENTITY["low"]
    if difficulty == "staff":
        return COUNT_BY_ENTITY["high"]
    return fallback


def failure_mode_for(profile: dict, index: int) -> str:
    mode = str(scenario_profile(profile).get("failure_modes") or "multi_step")
    if mode == "basic":
        return "cross_tenant_access" if index % 3 == 1 else "normal"
    if mode == "ambiguous":
        if index % 11 == 0:
            return "same_slug_two_tenants"
        if index % 7 == 0:
            return "revoked_after_cache_warmup"
        if index % 5 == 0:
            return "group_inheritance_required"
        if index % 4 == 0:
            return "global_admin_shortcut"
        if index % 3 == 0:
            return "denied_reason_required"
    if index % 6 == 0:
        return "stale_role_cache"
    if index % 4 == 0:
        return "missing_policy_evidence"
    if index % 3 == 0:
        return "cross_tenant_access"
    return "normal"


def access_case(seed: int, rng: random.Random, index: int, failure_mode: str) -> dict:
    requested_tenant = rng.choice(TENANTS)
    resource_tenant = requested_tenant
    user_id = rng.choice(USERS)
    slug, kind = rng.choice(RESOURCES)
    action = rng.choice(["read", "write"])
    expected_allow = action == "read"
    role_hint = "viewer"

    if failure_mode in {"cross_tenant_access", "global_admin_shortcut", "same_slug_two_tenants"}:
        requested_tenant = "tenant_alpha"
        resource_tenant = "tenant_beta"
        user_id = "user_alpha_admin"
        slug = "billing-summary" if failure_mode == "same_slug_two_tenants" else "admin-console"
        action = "write"
        expected_allow = False
        role_hint = "admin"
    elif failure_mode == "stale_role_cache":
        requested_tenant = resource_tenant = "tenant_alpha"
        user_id = "user_alpha_admin"
        action = "write"
        expected_allow = False
        role_hint = "revoked_admin"
    elif failure_mode == "revoked_after_cache_warmup":
        requested_tenant = resource_tenant = "tenant_gamma"
        user_id = "user_gamma_admin"
        action = "write"
        expected_allow = False
        role_hint = "revoked_after_warmup"
    elif failure_mode == "group_inheritance_required":
        requested_tenant = resource_tenant = "tenant_alpha"
        user_id = "user_support"
        slug = "support-cases"
        action = "read"
        expected_allow = True
        role_hint = "support_group"
    elif failure_mode in {"missing_policy_evidence", "denied_reason_required"}:
        requested_tenant = resource_tenant = "tenant_beta"
        user_id = "user_beta_viewer"
        slug = "admin-console"
        action = "write"
        expected_allow = False
        role_hint = "viewer"

    return {
        "request_id": f"generated-{seed}-{index}",
        "user_id": user_id,
        "tenant_id": requested_tenant,
        "resource_tenant_id": resource_tenant,
        "resource_slug": slug,
        "resource_kind": kind,
        "action": action,
        "expected_allow": expected_allow,
        "expected_reason_required": not expected_allow,
        "expected_policy_evidence": True,
        "role_hint": role_hint,
        "failure_mode": failure_mode,
    }


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
    parser.add_argument("--seed", type=int, default=20260520)
    parser.add_argument("--count", type=int, default=4)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--out", default="candidate/fixtures/public/access_cases.jsonl")
    args = parser.parse_args()

    profile = load_profile(args.profile)
    seed = profile_seed(profile, args.seed)
    count = profile_count(profile, args.count)
    rng = random.Random(seed)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if not profile:
        out.write_text("".join(json.dumps(case, sort_keys=True) + "\n" for case in public_cases()))
        print(f"wrote {len(public_cases())} public access cases to {out}")
        return

    with out.open("w") as handle:
        for index in range(count):
            failure_mode = failure_mode_for(profile, index)
            handle.write(json.dumps(access_case(seed, rng, index, failure_mode), sort_keys=True) + "\n")
    print(f"wrote {count} generated access cases to {out}")


if __name__ == "__main__":
    main()
