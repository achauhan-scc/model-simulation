import json
from pathlib import Path

from pydantic import ValidationError

from src.resolver.models import (
    ModelProfile,
    ModelProfileRegistry,
    ScenarioMapping,
)


class ConfigurationError(RuntimeError):
    pass


class ConfigurationStore:
    def __init__(
        self,
        mappings_dir: Path,
        responses_dir: Path,
        registry_file: Path,
    ) -> None:
        self._mappings_dir = mappings_dir.resolve()
        self._responses_dir = responses_dir.resolve()
        self._registry_file = registry_file.resolve()
        self._registry: ModelProfileRegistry | None = None
        self._scenarios: dict[str, ScenarioMapping] = {}
        self._fixtures: dict[str, dict] = {}

    @property
    def ready(self) -> bool:
        return self._registry is not None

    def load(self) -> None:
        try:
            registry = ModelProfileRegistry.model_validate(
                self._read_json(self._registry_file)
            )
            scenarios: dict[str, ScenarioMapping] = {}
            fixtures: dict[str, dict] = {}

            for alias, profile in registry.profiles.items():
                mapping_path = self._safe_child(
                    self._mappings_dir, profile.mapping_file
                )
                scenario = ScenarioMapping.model_validate(
                    self._read_json(mapping_path)
                )
                if scenario.model != alias:
                    raise ConfigurationError(
                        f"Scenario {scenario.scenario_id} declares model "
                        f"{scenario.model!r}, expected {alias!r}."
                    )
                for rule in scenario.rules:
                    fixture_path = self._safe_child(
                        self._responses_dir, rule.response_fixture
                    )
                    fixtures[str(fixture_path)] = self._read_json(fixture_path)
                scenarios[alias] = scenario
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise ConfigurationError(f"Invalid simulator configuration: {exc}") from exc

        self._registry = registry
        self._scenarios = scenarios
        self._fixtures = fixtures

    def model_aliases(self) -> list[str]:
        self._require_ready()
        assert self._registry is not None
        return sorted(self._registry.profiles)

    def profile(self, model_alias: str) -> ModelProfile:
        self._require_ready()
        assert self._registry is not None
        try:
            return self._registry.profiles[model_alias]
        except KeyError as exc:
            raise KeyError(f"Unknown simulator model alias: {model_alias}") from exc

    def scenario(self, model_alias: str) -> ScenarioMapping:
        self._require_ready()
        try:
            return self._scenarios[model_alias]
        except KeyError as exc:
            raise KeyError(f"Unknown simulator model alias: {model_alias}") from exc

    def fixture(self, relative_path: str) -> dict:
        self._require_ready()
        fixture_path = self._safe_child(self._responses_dir, relative_path)
        try:
            return self._fixtures[str(fixture_path)]
        except KeyError as exc:
            raise KeyError(f"Unknown response fixture: {relative_path}") from exc

    def scenario_summary(self, model_alias: str) -> dict:
        scenario = self.scenario(model_alias)
        profile = self.profile(model_alias)
        return {
            "model": model_alias,
            "scenarioId": scenario.scenario_id,
            "title": scenario.title,
            "syntheticUsageProfile": profile.synthetic_usage_profile,
            "rules": [rule.id for rule in scenario.rules],
        }

    def _require_ready(self) -> None:
        if not self.ready:
            raise ConfigurationError("Simulator configuration is not loaded.")

    @staticmethod
    def _read_json(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as file:
            value = json.load(file)
        if not isinstance(value, dict):
            raise ConfigurationError(f"Expected a JSON object in {path}.")
        return value

    @staticmethod
    def _safe_child(root: Path, relative_path: str) -> Path:
        candidate = (root / relative_path).resolve()
        if candidate != root and root not in candidate.parents:
            raise ConfigurationError(
                f"Configured path escapes its allowed directory: {relative_path}"
            )
        return candidate
