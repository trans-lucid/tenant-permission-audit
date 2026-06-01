#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cleanup_generated_transients() {
  find "$ROOT/generated" -type d \( -name __pycache__ -o -name .pytest_cache -o -name "*.egg-info" \) -prune -exec rm -rf {} +
}
trap cleanup_generated_transients EXIT

cd "$ROOT/generated/main"
python3 -m pip install -e ".[test]" >/tmp/tenant-render-main-install.txt
set +e
python3 -m pytest tests/public/test_policy_contract.py 2>&1 | tee /tmp/tenant-render-main-unit-output.txt
status=${PIPESTATUS[0]}
set -e
if [ "$status" -eq 0 ]; then
  echo "rendered candidate main unexpectedly passed public unit tests"
  exit 1
fi
for expected in cross_tenant_access_allowed global_admin_shortcut missing_policy_evidence stale_role_cache; do
  if ! grep -q "$expected" /tmp/tenant-render-main-unit-output.txt; then
    echo "rendered candidate main did not fail for expected reason: $expected"
    exit 1
  fi
done

cd "$ROOT/generated/solution"
python3 -m pip install -e ".[test]" >/tmp/tenant-render-solution-install.txt
EVAL_TARGET="$PWD/solution" python3 -m pytest tests/public/test_policy_contract.py solution/tests evaluator/tests_hidden

echo "rendered repo smoke validation passed"
