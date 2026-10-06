# SEC-01 Evidence Record - JWT Enforcement

## Test identity

- Test ID: SEC-01
- Category: Authentication and API security
- Execution time: 2026-10-06 00:11 Asia/Colombo
- Tester: Individual Student 4 assessor
- Git commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Target: local LearnMate FastAPI instance
- Test account: fresh synthetic `SEC JWT Tester` account

## Environment and safety boundary

- The backend and runner used the same disposable local assessment signing
  secret so the runner could create a correctly signed but expired token.
- No password, bearer token, invalid token value or signing secret was written
  to the evidence file.
- The test used only a synthetic account and the controlled
  `ir-accuracy.pdf` document.
- Input SHA-256:
  `7d50bd155e43364a6acd9256871264ee3169d38937746113da3e2f6a9250ce5b`

## Test definition

- Objective: verify that every document operation enforces JWT authentication
  and returns a controlled response without exposing data or internal details.
- Token conditions:
  1. Missing authorization header
  2. Malformed bearer value
  3. Valid token with a deterministically modified signature byte
  4. Correctly signed token whose `exp` time was already in the past
- Protected operations:
  1. Upload: `POST /documents/upload`
  2. List: `GET /documents`
  3. Get metadata: `GET /documents/{document_id}`
  4. Semantic search: `POST /documents/search`
  5. Delete: `DELETE /documents/{document_id}`
- Total request cases: 4 token conditions x 5 operations = 20
- Expected: every request returns 401, the same generic message, a Bearer
  authentication challenge, no internal details, and no protected state
  change.

## Actual result

- Requests executed: 20
- Requests passed: 20
- Requests failed: 0
- Missing token: 5/5 returned 401
- Malformed token: 5/5 returned 401
- Tampered signature: 5/5 returned 401
- Expired token: 5/5 returned 401
- Response message in every case:
  `The login session is invalid or has expired.`
- `WWW-Authenticate` in every case: `Bearer`
- Internal stack trace, SQLite, Chroma or signature details exposed: No
- Median unauthorized-response latency: 10.91 ms
- p95 unauthorized-response latency: 28.33 ms
- Maximum unauthorized-response latency: 29.13 ms
- Outcome: Pass

## Protected-state postcondition

After all 20 invalid requests:

- Valid owner list status: 200
- Original owner document still listed: Yes
- Valid owner search status: 200
- Original owner document still searchable: Yes
- Final authenticated document deletion: 200
- Cleanup succeeded: Yes

This confirms that the rejected delete and upload requests did not modify the
protected document state.

## Methodological correction

An earlier preliminary run was excluded from the result because the harness
changed only the final Base64URL signature character. JWT signatures can have
unused padding bits in that final character, so a visually changed character
can decode to the same signature bytes. The application therefore correctly
accepted that equivalent token representation.

The harness was corrected to alter the first signature character, which
guarantees a change to significant decoded signature bits. The one extra
synthetic document created during the invalid preliminary run was identified
by its exact synthetic account and document ID and deleted through the
authenticated API. The preliminary raw file remains local as an audit trail but
is not used as vulnerability evidence.

## Evidence

- Valid raw log: `evidence/raw/sec-jwt-20261005T184109Z.json`
- Excluded preliminary raw log:
  `evidence/raw/sec-jwt-20261005T183451Z.json`
- Missing-token screenshot: `SEC-01-01-missing-token.png`
- Malformed-token screenshot: `SEC-01-02-malformed-token.png`
- Tampered-signature screenshot: `SEC-01-03-tampered-token.png`
- Expired-token screenshot: `SEC-01-04-expired-token.png`
- Preserved-state screenshot: `SEC-01-05-state-preserved.png`
- Authentication-code screenshot: `SEC-01-06-authentication-code.png`
- Screenshot status: Pending; capture from the valid sanitized log and narrow
  authentication code sections

## Analysis and conclusion

The tested document endpoints consistently use the shared authentication
dependency. The token decoder verifies the HS256 signature and requires the
`sub`, `iat` and `exp` claims. Invalid conditions are mapped to one generic 401
response, which reduces information disclosure. The owner-state postcondition
shows that authentication failure occurred before document operations changed
state.

No JWT-enforcement vulnerability was demonstrated by SEC-01. This is a
positive security control result, not proof that the whole authentication
system is secure. Token theft, logout/revocation, production-secret management,
brute-force protection and authorization between different authenticated users
are outside this test. Cross-user authorization is tested separately in SEC-02
and SEC-03.

## Risk and recommendation

- Confirmed vulnerability: No
- Severity: Not applicable
- Control result: Effective for the four tested invalid-token conditions
- Recommendation: retain the shared dependency and generic error response; add
  these 20 cases as automated regression coverage and separately assess token
  revocation, login throttling and production secret rotation.
