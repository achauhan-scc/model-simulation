from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from src.security.auth import ApiKeyAuthorizer


@pytest.mark.asyncio
async def test_uses_configured_api_key_header() -> None:
    request = Mock()
    request.headers = {"x-custom-simulator-key": "expected"}
    authorizer = ApiKeyAuthorizer("expected", "x-custom-simulator-key")

    await authorizer.authorize(request)


@pytest.mark.asyncio
async def test_rejects_invalid_api_key() -> None:
    request = Mock()
    request.headers = {"x-simulator-key": "wrong"}
    authorizer = ApiKeyAuthorizer("expected", "x-simulator-key")

    with pytest.raises(HTTPException) as error:
        await authorizer.authorize(request)

    assert error.value.status_code == 401
