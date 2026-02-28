"""Rate limiting helpers for API request throttling."""

from collections import deque
from threading import Lock
from time import time


class InMemoryRateLimiter:
    """Simple in-memory sliding window rate limiter."""

    def __init__(self) -> None:
        """Initialize limiter state."""
        self._events: dict[str, deque[float]] = {}
        self._lock = Lock()

    def consume(
        self,
        *,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """Consume one request token and return allowance + retry delay."""
        now = time()
        window_start = now - window_seconds
        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and events[0] <= window_start:
                events.popleft()

            if len(events) >= max_requests:
                retry_after = max(1, int(window_seconds - (now - events[0])))
                return False, retry_after

            events.append(now)
            return True, 0

    def reset(self) -> None:
        """Clear limiter state (test helper)."""
        with self._lock:
            self._events.clear()
