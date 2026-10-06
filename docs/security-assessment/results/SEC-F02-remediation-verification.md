# SEC-F02 Remediation Verification

## Verification identity

- Finding: SEC-F02 - Unbounded Semantic-Search Requests
- Test: SEC-09
- Original baseline commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Reconfirmed affected commit: `bec9feb60d8dd643ceee8eb6ab54d3db47c563a9`
- Remediation commit: `9fa06dfe18f4af8f55a212f0253c2665d0c3e607`
- Exact-boundary test commit: `679bc2f`
- Verification date: 2026-10-06
- Environment: local single-process Microsoft Windows development instance

## Before remediation

The targeted reassessment on `bec9feb` reproduced the original behavior:

- queries of 128, 1,024, 8,192 and 32,768 characters all returned 200;
- all 12 requests in a four-worker burst returned 200;
- no rate limiting was observed;
- storage state remained unchanged; and
- the service remained healthy.

Raw evidence: `sec-query-abuse-20261006T084914Z.json`.

## Implemented controls

The backend now applies both controls before expensive semantic-search work:

1. Pydantic rejects document-search queries longer than 4,096 characters.
2. A thread-safe sliding-window limiter permits ten requests per authenticated
   user in ten seconds and then returns 429 with `Retry-After`.

The defaults are documented and configurable through:

- `LEARNMATE_MAX_SEARCH_QUERY_CHARACTERS`
- `LEARNMATE_SEARCH_RATE_LIMIT_REQUESTS`
- `LEARNMATE_SEARCH_RATE_LIMIT_WINDOW_SECONDS`

No query text is stored by the limiter; its key is the authenticated user ID.

## Post-remediation SEC-09 result

The controlled assessment runner was repeated against the exact remediation
commit:

- Query-length cases executed: 4
- 128 characters: 200
- 1,024 characters: 200
- 8,192 characters: 422
- 32,768 characters: 422
- Excessive query rejected: Yes
- Maximum accepted length among the runner's tested values: 1,024
- Query median/p95 latency: 25.53/49.37 ms
- Controlled burst: 12 requests with four workers
- Burst status distribution: eight 200 responses and four 429 responses
- Rate limit observed: Yes
- Burst median/p95 latency: 59.75/70.33 ms
- No internal details exposed: Yes
- Storage state preserved: Yes
- Service remained healthy: Yes
- Cleanup succeeded: Yes
- Overall SEC-09 outcome: Pass

Raw evidence: `sec-query-abuse-20261006T091624Z.json`.

The runner does not submit exactly 4,096 characters. Separate automated tests
therefore verify that 4,096 is accepted and 4,097 is rejected.

## Automated regression result

The complete backend suite was executed from the `backend` directory after the
remediation and exact-boundary test commits:

```text
python -m unittest discover -s tests -v
Ran 122 tests in 36.561s
OK
```

Coverage includes query boundaries, per-user isolation, retry calculation,
window recovery, the controlled API burst and all existing application tests.

## Security conclusion

The demonstrated SEC-F02 behavior is mitigated for the assessed local
single-process deployment. Oversized inputs no longer reach embedding, and a
repeatable authenticated burst produces controlled 429 responses without
changing persistent state or making the service unhealthy.

The in-memory limiter is intentionally simple for the current architecture. It
does not coordinate counters across multiple processes or servers. Production
deployment should add a shared Redis/API-gateway limiter, capacity monitoring,
timeouts and justified limits for other expensive endpoints.
