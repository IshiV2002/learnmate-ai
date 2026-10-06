# SEC-F02 - Unbounded Semantic-Search Requests

## Status

- Evidence status: Confirmed at the application boundary
- Related test: SEC-09
- Affected commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`

## Description

The authenticated document-search endpoint enforces neither a maximum query
length nor an observable request-rate limit. Every tested query through 32,768
characters and all 12 requests in a four-worker burst reached semantic search
and returned 200.

## Technical root cause

`DocumentSearchRequest.query` is a plain Pydantic string. Its validator rejects
blank values but has no maximum length. Accepted queries trigger embedding and
Chroma search. The FastAPI application contains no rate-limiting middleware or
endpoint-specific throttle.

## Evidence summary

- Accepted query lengths: 128, 1,024, 8,192 and 32,768 characters
- Maximum accepted tested length: 32,768 characters
- Burst: 12 requests, four workers
- Burst statuses: 12 responses with 200; zero with 429
- Burst median/p95: 133.22/208.38 ms
- Storage state preserved: Yes
- Service remained healthy: Yes
- Cleanup succeeded: Yes

## Impact

- Authenticated users can cause unnecessary embedding and vector-search work.
- Repeated requests could reduce availability for legitimate students.
- Future use of billed external models could also create avoidable cost.
- No outage, data corruption or confidentiality impact was demonstrated.

## Risk assessment

- Impact: 2/5 - avoidable resource consumption is confirmed; outage is not.
- Likelihood: 4/5 - the behavior is easy for any authenticated user to repeat.
- Risk score: 8/25.
- Preliminary severity: Medium.
- Matrix: 1-4 Low, 5-9 Medium, 10-16 High, 17-25 Critical.

## Recommended mitigation

1. Enforce a documented query character limit before embedding.
2. Add authenticated per-user/IP rate limits for expensive endpoints.
3. Return controlled 422/413 for excessive input and 429 for throttled requests.
4. Define short-burst and longer-window quotas using expected classroom usage.
5. Monitor request counts and latency without retaining sensitive query text.
6. Add exact-boundary and recovery regression tests.

## Residual risk

Reasonable limits reduce abuse but cannot eliminate all resource pressure.
Capacity monitoring, timeouts, concurrency controls and deployment-layer limits
should complement application validation.
