from src.matching.engine import match_request
from src.protocol.models import ChatCompletionRequest
from src.resolver.models import ScenarioMapping


def test_requires_declared_tool() -> None:
    request = ChatCompletionRequest.model_validate(
        {
            "model": "hostile-refund-v1",
            "messages": [{"role": "user", "content": "Process ticket T-1042"}],
            "tools": [],
        }
    )
    scenario = ScenarioMapping.model_validate(
        {
            "schemaVersion": 1,
            "scenarioId": "AC-001",
            "title": "Refund",
            "model": "hostile-refund-v1",
            "rules": [
                {
                    "id": "refund",
                    "priority": 100,
                    "match": {
                        "conversationStage": "initial",
                        "requiredTools": ["issue_refund"],
                        "inputContainsAll": ["T-1042"],
                    },
                    "responseFixture": "request-refund.json",
                }
            ],
            "fallback": {"behavior": "reject", "statusCode": 422},
        }
    )

    assert match_request(request, scenario) is None
