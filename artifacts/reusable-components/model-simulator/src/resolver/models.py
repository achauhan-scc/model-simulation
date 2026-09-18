from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ModelProfile(BaseModel):
    scenario: str = Field(min_length=1)
    mapping_file: str = Field(alias="mappingFile", min_length=1)
    synthetic_usage_profile: str = Field(
        alias="syntheticUsageProfile", default="default"
    )


class ModelProfileRegistry(BaseModel):
    schema_version: int = Field(alias="schemaVersion")
    profiles: dict[str, ModelProfile]


class MatchRule(BaseModel):
    conversation_stage: Literal["initial", "after_tool"] | None = Field(
        alias="conversationStage", default=None
    )
    required_tools: list[str] = Field(alias="requiredTools", default_factory=list)
    input_contains_all: list[str] = Field(
        alias="inputContainsAll", default_factory=list
    )
    tool_result_for: str | None = Field(alias="toolResultFor", default=None)


class ScenarioRule(BaseModel):
    id: str = Field(min_length=1)
    priority: int = 0
    match: MatchRule
    response_fixture: str = Field(alias="responseFixture", min_length=1)


class ScenarioFallback(BaseModel):
    behavior: Literal["reject"]
    status_code: int = Field(alias="statusCode", default=422, ge=400, le=499)


class ScenarioMapping(BaseModel):
    schema_version: int = Field(alias="schemaVersion")
    scenario_id: str = Field(alias="scenarioId", min_length=1)
    title: str = Field(min_length=1)
    model: str = Field(min_length=1)
    rules: list[ScenarioRule] = Field(min_length=1)
    fallback: ScenarioFallback

    @model_validator(mode="after")
    def validate_unique_rule_ids(self) -> "ScenarioMapping":
        rule_ids = [rule.id for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("Scenario rule IDs must be unique.")
        return self
