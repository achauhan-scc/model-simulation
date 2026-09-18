import hmac

from fastapi import HTTPException, Request, status


class ApiKeyAuthorizer:
    def __init__(self, expected_key: str | None, header_name: str) -> None:
        self._expected_key = expected_key
        self.header_name = header_name

    async def authorize(self, request: Request) -> None:
        if self._expected_key is None:
            return
        api_key = request.headers.get(self.header_name)
        if api_key is None or not hmac.compare_digest(api_key, self._expected_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": "Invalid simulator API key.",
                    "type": "authentication_error",
                    "code": "invalid_api_key",
                },
            )
