import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory sliding-window rate limiter.

    Keyed by client IP (or X-Forwarded-For first hop when behind a proxy).
    Process-local — fine for single-instance Koyeb free tier; swap for Redis
    when scaling horizontally.
    """

    def __init__(self, app: ASGIApp, *, requests_per_minute: int = 60, exempt_paths: tuple[str, ...] = ("/health",)):
        super().__init__(app)
        self._limit = requests_per_minute
        self._window = 60.0
        self._exempt = exempt_paths
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request, call_next):
        if any(request.url.path.startswith(p) for p in self._exempt):
            return await call_next(request)

        key = self._client_key(request)
        now = time.monotonic()
        bucket = self._buckets[key]
        cutoff = now - self._window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) >= self._limit:
            retry_after = max(1, int(self._window - (now - bucket[0])))
            return JSONResponse(
                {"data": None, "error": "rate_limit_exceeded", "meta": {"retry_after": retry_after}},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self._limit)
        response.headers["X-RateLimit-Remaining"] = str(self._limit - len(bucket))
        return response

    @staticmethod
    def _client_key(request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
