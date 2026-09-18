from dataclasses import dataclass

from src.protocol.models import ChatCompletionRequest, ChatMessage
from src.resolver.models import ScenarioMapping, ScenarioRule


@dataclass(frozen=True)
class MatchResult:
    rule: ScenarioRule
    conversation_stage: str


def match_request(
    request: ChatCompletionRequest, scenario: ScenarioMapping
) -> MatchResult | None:
    stage = _conversation_stage(request.messages)
    tool_names = {tool.function.name for tool in request.tools}
    searchable_text = "\n".join(_message_text(message) for message in request.messages)
    tool_result_ids = {
        message.name
        for message in request.messages
        if message.role == "tool" and message.name
    }

    for rule in sorted(scenario.rules, key=lambda value: value.priority, reverse=True):
        criteria = rule.match
        if criteria.conversation_stage and criteria.conversation_stage != stage:
            continue
        if not set(criteria.required_tools).issubset(tool_names):
            continue
        if any(value not in searchable_text for value in criteria.input_contains_all):
            continue
        if criteria.tool_result_for and criteria.tool_result_for not in tool_result_ids:
            continue
        return MatchResult(rule=rule, conversation_stage=stage)
    return None


def _conversation_stage(messages: list[ChatMessage]) -> str:
    return "after_tool" if any(message.role == "tool" for message in messages) else "initial"


def _message_text(message: ChatMessage) -> str:
    if isinstance(message.content, str):
        return message.content
    if isinstance(message.content, list):
        return " ".join(
            str(part.get("text", ""))
            for part in message.content
            if isinstance(part, dict)
        )
    return ""
