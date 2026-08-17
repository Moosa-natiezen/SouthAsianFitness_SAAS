from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
import time


class InMemoryRateLimiter:
    def __init__(self, window_seconds: int, max_requests: int) -> None:
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self._locks: dict[str, Lock] = defaultdict(Lock)
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
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

    def clear(self, key: str | None = None) -> None:
        if key is None:
            self._requests.clear()
            return
        self._requests.pop(key, None)


login_rate_limiter = InMemoryRateLimiter(window_seconds=300, max_requests=10)
