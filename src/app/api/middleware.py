import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests_per_minute: int) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.max_requests_per_minute = max_requests_per_minute
        self._events: dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        if request.url.path != "/api/orders":
            return await call_next(request)

        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window_start = now - 60
        bucket = self._events[key]

        while bucket and bucket[0] < window_start:
            bucket.popleft()

        if len(bucket) >= self.max_requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again in a minute."},
            )

        bucket.append(now)
        return await call_next(request)

