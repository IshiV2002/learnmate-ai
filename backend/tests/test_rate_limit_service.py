import unittest

from app.services.rate_limit_service import (
    RateLimitExceededError,
    SlidingWindowRateLimiter,
)


class FakeClock:
    """Provide predictable time without making rate-limit tests sleep."""

    def __init__(self) -> None:
        self.current_time = 0.0

    def __call__(self) -> float:
        return self.current_time

    def advance(self, seconds: float) -> None:
        self.current_time += seconds


class SlidingWindowRateLimiterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.rate_limiter = SlidingWindowRateLimiter(
            max_requests=2,
            window_seconds=10,
            clock=self.clock,
        )

    def test_request_over_limit_reports_retry_time(self) -> None:
        self.rate_limiter.check_request("user-1")
        self.rate_limiter.check_request("user-1")

        with self.assertRaises(RateLimitExceededError) as raised_error:
            self.rate_limiter.check_request("user-1")

        self.assertEqual(raised_error.exception.retry_after_seconds, 10)

    def test_users_have_independent_allowances(self) -> None:
        self.rate_limiter.check_request("user-1")
        self.rate_limiter.check_request("user-1")

        self.rate_limiter.check_request("user-2")

    def test_allowance_recovers_after_window(self) -> None:
        self.rate_limiter.check_request("user-1")
        self.rate_limiter.check_request("user-1")
        self.clock.advance(10)

        self.rate_limiter.check_request("user-1")


if __name__ == "__main__":
    unittest.main()
