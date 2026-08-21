"""Request body size limit middleware.

Rejects requests with bodies exceeding a reasonable limit.
Prevents abuse without breaking legitimate MVP requests.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Maximum request body size: 1 MB
MAX_BODY_BYTES = 1 * 1024 * 1024


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with bodies exceeding MAX_BODY_BYTES."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")

        if content_length is not None:
            try:
                size = int(content_length)
            except ValueError:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Invalid Content-Length header"},
                )

            if size > MAX_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large"},
                )

        return await call_next(request)
