.PHONY: dev logs seed test test-unit test-integration run clean

PYTHON ?= python3

dev:
	docker compose up -d

logs:
	docker compose logs -f

seed:
	$(PYTHON) -m src.resource_store migrate
	$(PYTHON) -m src.resource_store seed

test:
	$(PYTHON) -m pytest tests/public

test-unit:
	$(PYTHON) -m pytest tests/public/test_policy_contract.py

test-integration:
	$(PYTHON) -m pytest tests/public/test_integration_access.py

run:
	$(PYTHON) -m src.report --cases fixtures/public/access_cases.jsonl --out results/access_audit_report.json

clean:
	docker compose down -v
