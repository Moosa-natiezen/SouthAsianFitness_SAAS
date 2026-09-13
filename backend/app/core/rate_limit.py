from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock


class InMemoryRateLimiter:
    def __init__(self, window_seconds: int, max_requests: int) -> None:
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self._locks: dict[str, Lock] = defaultdict(Lock)
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        """Record a request for `key` and return whether it is within the limit."""
        now = time.monotonic()
        window_start = now - self.window_seconds
        with self._locks[key]:
            bucket = self._requests[key]
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                return False
            bucket.append(now)
            return True

    def peek(self, key: str) -> bool:
        """Check whether a request for `key` would be allowed WITHOUT recording it.

        Used when the expensive operation itself records the quota only on
        success (e.g. a generation that takes minutes to complete): the route
        pre-checks with peek(), runs the generation, then calls allow() to
        consume quota. Failed attempts are never counted.
        """
        now = time.monotonic()
        window_start = now - self.window_seconds
        with self._locks[key]:
            bucket = self._requests[key]
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            return len(bucket) < self.max_requests

    def clear(self, key: str | None = None) -> None:
        if key is None:
            self._requests.clear()
            return
        self._requests.pop(key, None)


login_rate_limiter = InMemoryRateLimiter(window_seconds=300, max_requests=10)

# ── AI generation abuse prevention ───────────────────────────────────────────
# LLM generation endpoints cost real API tokens. The IP-level cap stops one
# client from rotating throwaway free accounts to farm free generations —
# the per-user quota cannot see across accounts, this can.
generation_ip_limiter = InMemoryRateLimiter(
    window_seconds=60 * 60 * 24,  # 24 hours
    max_requests=10,
)
