# SEC-F02 - Unbounded Semantic-Search Requests

## Status

- Evidence status: Confirmed at the application boundary
- Related test: SEC-09
- Affected commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Reconfirmed commit: `bec9feb60d8dd643ceee8eb6ab54d3db47c563a9`
- Mitigation status: Implemented and verified for the current single-process deployment
- Remediation commit: `9fa06dfe18f4af8f55a212f0253c2665d0c3e607`
- Boundary-test commit: `679bc2f`

The Medium 8/25 rating documents the demonstrated pre-fix risk. It is retained
as the original assessment result rather than presented as an unmitigated risk
on the remediated commit.

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

## Implemented mitigation and verification

The document-search request schema now rejects queries longer than 4,096
characters before embedding. A thread-safe sliding-window limiter allows ten
semantic-search requests per authenticated user in ten seconds, then returns a
controlled 429 response with a `Retry-After` header. All three limits can be
configured through environment variables while retaining safe defaults.

Automated tests cover the accepted 4,096-character boundary, the rejected
4,097-character boundary, per-user isolation, a controlled burst, retry timing
and recovery after the window. A post-fix SEC-09 run rejected both 8,192- and
32,768-character inputs with 422 and returned four 429 responses during the
controlled 12-request burst. Storage state and service health were preserved,
and the complete backend suite passed 122 tests.

See `results/SEC-F02-remediation-verification.md` for the evidence record.

## Residual risk

Reasonable limits reduce abuse but cannot eliminate all resource pressure.
Capacity monitoring, timeouts, concurrency controls and deployment-layer limits
should complement application validation.

The current limiter stores counters in one application process. A multi-worker
or multi-server production deployment needs a shared limiter, such as Redis or
an API-gateway control, to enforce one allowance across every instance. Other
expensive endpoints should receive separately justified limits before public
deployment.
