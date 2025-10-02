import time
import asyncio
from typing import Dict
from starlette.types import ASGIApp, Scope, Receive, Send

class TokenBucket:
    __slots__ = ("capacity","tokens","fill_rate","timestamp","lock")
    def __init__(self, capacity: int, refill_per_minute: int):
        self.capacity = capacity
        self.tokens = capacity
        self.fill_rate = refill_per_minute / 60.0  # tokens per second
        self.timestamp = time.time()
        self.lock = asyncio.Lock()

    async def consume(self, num: int = 1) -> bool:
        async with self.lock:
            now = time.time()
            elapsed = now - self.timestamp
            self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)
            self.timestamp = now
            if self.tokens >= num:
                self.tokens -= num
                return True
            return False

class RateLimitMiddleware:
    """
    ASGI middleware implementing per-IP token bucket.
    In-memory — not suitable for multi-process horizontally scaled systems.
    For production use Redis-based leaky bucket.
    """
    def __init__(self, app: ASGIApp, requests_per_minute: int = 120, capacity: int | None = None):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.capacity = capacity or max(1, requests_per_minute // 2)
        self.buckets: Dict[str, TokenBucket] = {}
        self._cleanup_task = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        ip = client[0] if client else "unknown"
        bucket = self.buckets.get(ip)
        if bucket is None:
            bucket = TokenBucket(capacity=self.capacity, refill_per_minute=self.requests_per_minute)
            self.buckets[ip] = bucket

        allowed = await bucket.consume()
        if not allowed:
            # Too Many Requests
            from starlette.responses import JSONResponse
            response = JSONResponse({"detail": "Too Many Requests"}, status_code=429)
            await response(scope, receive, send)
            return

        # lazy cleanup task
        if self._cleanup_task is None:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(self._cleanup_loop())

        await self.app(scope, receive, send)

    async def _cleanup_loop(self):
        # periodically remove IPs that haven't been used for a while to avoid memory leak
        try:
            while True:
                await asyncio.sleep(60)
                now = time.time()
                to_delete = []
                for ip, bucket in list(self.buckets.items()):
                    # if bucket not refilled for > 5 minutes, drop
                    if (now - bucket.timestamp) > 300:
                        to_delete.append(ip)
                for ip in to_delete:
                    del self.buckets[ip]
        except asyncio.CancelledError:
            return
