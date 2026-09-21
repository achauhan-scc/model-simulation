import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Iterator

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError

from src.matching.engine import match_request
from src.protocol.models import ChatCompletionRequest
from src.rendering.renderer import render_fixture
from src.resolver.store import ConfigurationError, ConfigurationStore
from src.security.auth import ApiKeyAuthorizer
from src.telemetry.events import configure_logging, content_hash, emit_event


BASE_DIR = Path(__file__).resolve().parents[2]
MAPPINGS_DIR = Path(os.getenv("SIMULATOR_MAPPINGS_DIR", BASE_DIR / "mappings"))
RESPONSES_DIR = Path(os.getenv("SIMULATOR_RESPONSES_DIR", BASE_DIR / "responses"))
REGISTRY_FILE = Path(
    os.getenv("SIMULATOR_REGISTRY_FILE", MAPPINGS_DIR / "model-profiles.json")
)
API_KEY_HEADER = os.getenv("SIMULATOR_API_KEY_HEADER", "x-simulator-key")

store = ConfigurationStore(MAPPINGS_DIR, RESPONSES_DIR, REGISTRY_FILE)
authorizer = ApiKeyAuthorizer(os.getenv("SIMULATOR_API_KEY"), API_KEY_HEADER)


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    store.load()
    emit_event("simulation.configuration_loaded", models=store.model_aliases())
    yield


app = FastAPI(
    title="Agent Model Simulator",
    version="0.1.0",
    description="Deterministic OpenAI-compatible model simulator.",
    lifespan=lifespan,
)


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(
    _: Request, exc: ConfigurationError
) -> JSONResponse:
    return _error_response(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        str(exc),
        "configuration_error",
        "simulator_not_ready",
    )


@app.exception_handler(HTTPException)
async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return _error_response(
            exc.status_code,
            str(exc.detail.get("message", "Request failed.")),
            str(exc.detail.get("type", "invalid_request_error")),
            str(exc.detail.get("code", "request_failed")),
        )
    return _error_response(
        exc.status_code,
        str(exc.detail),
        "invalid_request_error",
        "request_failed",
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(_: Request, exc: ValidationError) -> JSONResponse:
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        str(exc),
        "invalid_request_error",
        "invalid_request",
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        str(exc),
        "invalid_request_error",
        "invalid_request",
    )


@app.get("/healthz", include_in_schema=False)
async def health() -> dict:
    return {"status": "ok"}


@app.get("/readyz", include_in_schema=False)
async def readiness() -> JSONResponse:
    if not store.ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready"},
        )
    return JSONResponse(content={"status": "ready"})


@app.get("/admin/scenarios", dependencies=[Depends(authorizer.authorize)])
async def list_scenarios() -> dict:
    return {
        "data": [
            store.scenario_summary(model_alias)
            for model_alias in store.model_aliases()
        ]
    }


@app.get(
    "/admin/scenarios/{model_alias}",
    dependencies=[Depends(authorizer.authorize)],
)
async def get_scenario(model_alias: str) -> dict:
    try:
        return store.scenario_summary(model_alias)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": str(exc),
                "type": "invalid_request_error",
                "code": "unknown_model",
            },
        ) from exc


@app.post(
    "/chat/completions",
    dependencies=[Depends(authorizer.authorize)],
    response_model=None,
)
@app.post(
    "/v1/chat/completions",
    dependencies=[Depends(authorizer.authorize)],
    response_model=None,
)
async def chat_completions(
    request: ChatCompletionRequest,
    raw_request: Request,
    campaign_run_id: Annotated[str | None, Header(alias="x-campaign-run-id")] = None,
) -> dict | StreamingResponse:
    try:
        scenario = store.scenario(request.model)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": str(exc),
                "type": "invalid_request_error",
                "code": "unknown_model",
            },
        ) from exc

    result = match_request(request, scenario)
    if result is None:
        emit_event(
            "simulation.request_unmatched",
            campaignRunId=campaign_run_id,
            modelAlias=request.model,
            scenarioId=scenario.scenario_id,
            requestHash=content_hash(request.model_dump(mode="json")),
        )
        raise HTTPException(
            status_code=scenario.fallback.status_code,
            detail={
                "message": "Request did not match an approved simulation rule.",
                "type": "invalid_request_error",
                "code": "unmatched_simulation_request",
            },
        )

    request_id = f"chatcmpl-sim-{uuid.uuid4().hex}"
    fixture = store.fixture(result.rule.response_fixture)
    response = render_fixture(
        fixture,
        {
            "requestId": request_id,
            "created": int(time.time()),
            "model": request.model,
            "campaignRunId": campaign_run_id or "unavailable",
        },
    )
    response.setdefault("id", request_id)
    response.setdefault("created", int(time.time()))
    response.setdefault("model", request.model)

    emitted_tools = _emitted_tool_names(response)
    emit_event(
        "simulation.response_emitted",
        campaignRunId=campaign_run_id,
        clientHost=raw_request.client.host if raw_request.client else None,
        modelAlias=request.model,
        scenarioId=scenario.scenario_id,
        mappingRuleId=result.rule.id,
        responseFixture=result.rule.response_fixture,
        conversationStage=result.conversation_stage,
        availableTools=sorted(tool.function.name for tool in request.tools),
        emittedToolCalls=emitted_tools,
        usageSource="synthetic",
        streaming=request.stream,
        requestHash=content_hash(request.model_dump(mode="json")),
        responseHash=content_hash(response),
    )
    if request.stream:
        include_usage = bool(
            request.stream_options
            and request.stream_options.get("include_usage") is True
        )
        return StreamingResponse(
            _stream_chat_completion(response, include_usage),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    return response


def _stream_chat_completion(
    response: dict, include_usage: bool
) -> Iterator[str]:
    for chunk in _completion_chunks(response, include_usage):
        yield f"data: {json.dumps(chunk, separators=(',', ':'))}\n\n"
    yield "data: [DONE]\n\n"


def _completion_chunks(response: dict, include_usage: bool) -> list[dict]:
    chunks: list[dict] = []
    base = {
        "id": response["id"],
        "object": "chat.completion.chunk",
        "created": response["created"],
        "model": response["model"],
    }

    for choice in response.get("choices", []):
        index = choice.get("index", 0)
        message = choice.get("message", {})
        chunks.append(
            {
                **base,
                "choices": [
                    {
                        "index": index,
                        "delta": {"role": message.get("role", "assistant")},
                        "finish_reason": None,
                    }
                ],
            }
        )

        delta: dict = {}
        content = message.get("content")
        if isinstance(content, str):
            delta["content"] = content

        tool_calls = message.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            delta["tool_calls"] = [
                {
                    "index": tool_index,
                    "id": tool_call.get("id"),
                    "type": tool_call.get("type", "function"),
                    "function": tool_call.get("function", {}),
                }
                for tool_index, tool_call in enumerate(tool_calls)
            ]

        if delta:
            chunks.append(
                {
                    **base,
                    "choices": [
                        {
                            "index": index,
                            "delta": delta,
                            "finish_reason": None,
                        }
                    ],
                }
            )

        chunks.append(
            {
                **base,
                "choices": [
                    {
                        "index": index,
                        "delta": {},
                        "finish_reason": choice.get("finish_reason", "stop"),
                    }
                ],
            }
        )

    if include_usage:
        chunks.append(
            {
                **base,
                "choices": [],
                "usage": response.get("usage"),
            }
        )
    return chunks


def _emitted_tool_names(response: dict) -> list[str]:
    names: list[str] = []
    for choice in response.get("choices", []):
        message = choice.get("message", {})
        for tool_call in message.get("tool_calls", []):
            function = tool_call.get("function", {})
            name = function.get("name")
            if isinstance(name, str):
                names.append(name)
    return sorted(names)


def _error_response(
    status_code: int, message: str, error_type: str, code: str
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": message,
                "type": error_type,
                "code": code,
            }
        },
    )
