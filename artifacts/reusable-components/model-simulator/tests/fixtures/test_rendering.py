from src.rendering.renderer import render_fixture


def test_renders_nested_placeholders_without_mutating_fixture() -> None:
    fixture = {"id": "{requestId}", "nested": [{"model": "{model}"}]}

    rendered = render_fixture(
        fixture, {"requestId": "request-1", "model": "hostile-refund-v1"}
    )

    assert rendered == {
        "id": "request-1",
        "nested": [{"model": "hostile-refund-v1"}],
    }
    assert fixture["id"] == "{requestId}"
