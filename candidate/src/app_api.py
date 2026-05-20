from __future__ import annotations

from .evaluator import AccessEvaluator


class ProtectedResourceAPI:
    def __init__(self, evaluator: AccessEvaluator) -> None:
        self.evaluator = evaluator

    def access_resource(self, request: dict) -> dict:
        decision = self.evaluator.evaluate(request)
        if not decision["allow"]:
            return {"status": 403, "decision": decision}
        return {"status": 200, "decision": decision, "data": {"resource_id": decision["resource_id"]}}
