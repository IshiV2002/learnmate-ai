# SEC-09 Evidence Record - Query and Request Abuse

## Test identity

- Test ID: SEC-09
- Category: Semantic-search resource abuse
- Execution time: 2026-10-06 01:22 Asia/Colombo
- Tester: Individual Student 4 assessor
- Git commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Target: local LearnMate FastAPI instance only
- Account: fresh synthetic query-testing account

## Ethical safety boundary

- Query lengths: 128, 1,024, 8,192 and 32,768 characters
- Burst size: 12 authenticated requests
- Maximum concurrent workers: 4
- Public or external target: No
- Sustained denial-of-service attempt: No
- Full long-query values, password and bearer token were not recorded

## Test definition

- Objective: determine whether semantic-search input length and request rate are
  bounded before expensive embedding and vector-search work.
- Expected secure behavior: reject excessive queries with a controlled 4xx,
  apply an observable request-rate control, preserve storage, expose no internal
  details and remain healthy.
- Setup: upload one four-page controlled PDF to the synthetic account.

## Query-length results

All four queries returned 200 and three retrieval results:

- 128 characters: 54.14 ms
- 1,024 characters: 99.34 ms
- 8,192 characters: 123.33 ms
- 32,768 characters: 129.99 ms

Maximum accepted tested length: 32,768 characters.

- Excessive-query rejection observed: No
- Median query latency: 111.34 ms
- p95 query latency: 129.99 ms
- Internal-detail exposure: None observed

The test deliberately stopped at 32 KiB. It does not claim that this is the
maximum the server will accept.

## Controlled burst results

- Requests: 12
- Concurrent workers: 4
- Status distribution: 12 returned 200
- 429 responses: 0
- Rate-limit behavior observed: No
- Median latency: 133.22 ms
- p95 latency: 208.38 ms
- Service healthy after burst: Yes

The small burst demonstrated the absence of an observable throttle at this
level. It did not cause or attempt to cause a service outage.

## Persistence and cleanup

- Upload, SQLite and Chroma state unchanged during query operations: Yes
- Test document deletion: 200
- Final upload-directory count: 3
- Final synthetic-user document count: 0
- Final Chroma count: 55
- Exact initial state restored: Yes
- Cleanup succeeded: Yes

## Outcome

- Overall outcome: Fail
- Finding: `SEC-F02`
- Confirmed behavior: no query-length maximum was enforced through 32,768
  characters, and no rate-limit response appeared during the bounded burst.
- Not demonstrated: service outage, data corruption, cross-user access or
  sensitive error disclosure.

## Technical explanation

`DocumentSearchRequest.query` is a plain string. The validator rejects blank
values but specifies no maximum length. Accepted input proceeds to embedding
generation and Chroma search. The FastAPI application configures CORS and
routers but has no visible rate-limiting middleware or endpoint throttle.

## Risk assessment

- Impact: 2/5 - requests can trigger avoidable embedding/vector work, but this
  bounded test caused no outage or state damage.
- Likelihood: 4/5 - any authenticated user can repeatedly send long queries;
  the behavior was reproduced for every tested request.
- Risk score: 8/25.
- Preliminary severity: Medium.
- Matrix: 1-4 Low, 5-9 Medium, 10-16 High, 17-25 Critical.

## Recommended mitigation

1. Add a documented maximum query length at the Pydantic/API boundary.
2. Return a controlled 422 or 413 before embedding excessive input.
3. Apply authenticated per-user/IP rate controls to expensive endpoints.
4. Add short burst limits and longer-window quotas appropriate to expected use.
5. Return 429 with a retry indication when a limit is reached.
6. Monitor request counts and latency without logging sensitive query text.
7. Add regression tests for exact length boundaries and rate-limit recovery.

## Evidence

- Raw log: `evidence/raw/sec-query-abuse-20261005T195246Z.json`
- Length progression screenshot: `SEC-09-01-query-lengths.png`
- Long-query screenshot: `SEC-09-02-maximum-accepted.png`
- Burst screenshot: `SEC-09-03-burst-statuses.png`
- Summary screenshot: `SEC-09-04-summary.png`
- Cleanup screenshot: `SEC-09-05-cleanup.png`
- Schema screenshot: `SEC-09-06-query-schema.png`
- App-middleware screenshot: `SEC-09-07-middleware.png`
- Screenshot status: Pending
- Secret review: no password, token, full long query, personal path or internal
  filename was recorded

## Limitations

This local test used one process, one machine and a small safe burst. Proxy,
gateway or production infrastructure controls were not present and therefore
were not evaluated. A larger load test would require explicit authorization,
resource monitoring and stop conditions; it is unnecessary to establish the
missing application controls observed here.
