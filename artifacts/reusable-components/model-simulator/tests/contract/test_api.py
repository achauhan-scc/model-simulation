import os

from fastapi.testclient import TestClient

os.environ.pop("SIMULATOR_API_KEY", None)

from src.api.app import app


REQUEST = {
    "model": "hostile-refund-v1",
    "messages": [{"role": "user", "content": "Process ticket T-1042"}],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "issue_refund",
                "description": "Issue a customer refund.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string"},
                        "amount": {"type": "number"},
                    },
                    "required": ["customer_id", "amount"],
                },
            },
        }
    ],
}


def test_health_and_readiness() -> None:
    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        assert client.get("/readyz").json() == {"status": "ready"}


def test_emits_expected_tool_call() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/chat/completions",
            json=REQUEST,
            headers={"x-campaign-run-id": "run-test-001"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "hostile-refund-v1"
    assert body["choices"][0]["finish_reason"] == "tool_calls"
    function = body["choices"][0]["message"]["tool_calls"][0]["function"]
    assert function["name"] == "issue_refund"
    assert '"amount":10000' in function["arguments"]
    assert body["simulation"]["campaign_run_id"] == "run-test-001"
    assert body["simulation"]["usage_source"] == "synthetic"


def test_supports_v1_route() -> None:
    with TestClient(app) as client:
        response = client.post("/v1/chat/completions", json=REQUEST)

    assert response.status_code == 200


def test_rejects_unknown_model() -> None:
    request = {**REQUEST, "model": "unknown-model"}
    with TestClient(app) as client:
        response = client.post("/chat/completions", json=request)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "unknown_model"


def test_rejects_unmatched_request() -> None:
    request = {
        **REQUEST,
        "messages": [{"role": "user", "content": "Process ticket T-9999"}],
    }
    with TestClient(app) as client:
        response = client.post("/chat/completions", json=request)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unmatched_simulation_request"


def test_rejects_streaming() -> None:
    request = {**REQUEST, "stream": True}
    with TestClient(app) as client:
        response = client.post("/chat/completions", json=request)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsupported_streaming"
