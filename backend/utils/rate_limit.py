import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from backend.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window in-memory rate limiter keyed by client identity."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._last_cleanup = time.monotonic()

    def _client_key(self, request: Request) -> str:
        init_data = request.headers.get("X-Telegram-Init-Data")
        if init_data:
            # Cheap stable key without validating here (validation happens in deps).
            return f"initdata:{hash(init_data)}"
        client = request.client
        return f"ip:{client.host if client else 'unknown'}"

    def _cleanup(self, now: float) -> None:
        if now - self._last_cleanup < settings.rate_limit_window_seconds:
            return
        self._last_cleanup = now
        window_start = now - settings.rate_limit_window_seconds
        stale = [key for key, dq in self._hits.items() if not dq or dq[-1] < window_start]
        for key in stale:
            del self._hits[key]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        now = time.monotonic()
        self._cleanup(now)

        key = self._client_key(request)
        window_start = now - settings.rate_limit_window_seconds
        dq = self._hits[key]
        while dq and dq[0] < window_start:
            dq.popleft()

        if len(dq) >= settings.rate_limit_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Слишком много запросов. Попробуйте позже."},
            )

        dq.append(now)
        return await call_next(request)
