from collections import deque
from collections.abc import Callable
from math import ceil
from threading import Lock
from time import monotonic


class RateLimitExceededError(Exception):
    """Raised when one client exceeds an in-memory request allowance."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("The request rate limit was exceeded.")
        self.retry_after_seconds = retry_after_seconds


class SlidingWindowRateLimiter:
    """Apply a small per-key request limit within a rolling time window."""

    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if max_requests <= 0:
            raise ValueError("max_requests must be greater than zero.")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be greater than zero.")

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._clock = clock or monotonic
        self._requests_by_key: dict[str, deque[float]] = {}
        self._lock = Lock()

    def check_request(self, key: str) -> None:
        """Record one request or raise with the number of seconds to retry."""
        if not key.strip():
            raise ValueError("The rate-limit key cannot be empty.")

        now = self._clock()
        cutoff = now - self.window_seconds

        with self._lock:
            request_times = self._requests_by_key.setdefault(key, deque())
            while request_times and request_times[0] <= cutoff:
                request_times.popleft()

            if len(request_times) >= self.max_requests:
                retry_after = max(
                    1,
                    ceil(request_times[0] + self.window_seconds - now),
                )
                raise RateLimitExceededError(retry_after)

            request_times.append(now)

    def clear(self) -> None:
        """Remove recorded requests, primarily for controlled test isolation."""
        with self._lock:
            self._requests_by_key.clear()

    def clear_key(self, key: str) -> None:
        """Clear one allowance after a successful authentication attempt."""
        with self._lock:
            self._requests_by_key.pop(key, None)
