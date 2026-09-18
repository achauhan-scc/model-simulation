import copy
from typing import Any


def render_fixture(fixture: dict, values: dict[str, str | int]) -> dict:
    return _render(copy.deepcopy(fixture), values)


def _render(value: Any, values: dict[str, str | int]) -> Any:
    if isinstance(value, dict):
        return {key: _render(item, values) for key, item in value.items()}
    if isinstance(value, list):
        return [_render(item, values) for item in value]
    if isinstance(value, str):
        for key, replacement in values.items():
            if value == f"{{{key}}}":
                return replacement
        rendered = value
        for key, replacement in values.items():
            rendered = rendered.replace(f"{{{key}}}", str(replacement))
        return rendered
    return value
