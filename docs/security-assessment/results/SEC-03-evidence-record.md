# SEC-03 Evidence Record - Cross-User Metadata and Deletion Authorization

## Test identity

- Test ID: SEC-03
- Category: Broken Object Level Authorization and document management
- Execution time: 2026-10-06 00:22 Asia/Colombo
- Tester: Individual Student 4 assessor
- Git commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Target: local LearnMate FastAPI instance
- Accounts: fresh synthetic User A and User B

## Environment and controlled input

- Input: `user-a-private.pdf`
- Input SHA-256:
  `0706c6cca401e4a49f11f1094521b1e724297a318323df8d18a618c64d6227d1`
- Unique phrase: `violet lighthouse 731`
- User A owned the uploaded document.
- User B knew the exact document ID but did not own it.
- Passwords, bearer tokens and internal UUID storage filenames were not
  recorded.

## Test definition

- Objective: determine whether authenticated User B can discover metadata or
  delete a document owned by User A.
- Positive control: User A retrieves the document metadata before testing.
- Isolation checks:
  1. User B lists documents.
  2. User B gets User A's exact document ID.
  3. User B deletes User A's exact document ID.
- Non-disclosure controls: repeat get and delete with a random nonexistent ID.
- Integrity postconditions:
  1. User A can still retrieve metadata.
  2. User A can still semantically retrieve the unique phrase.
  3. SQLite metadata remains present.
  4. The safely stored file remains present and matches the input SHA-256.
- Expected: User B receives a generic 404 equivalent to the nonexistent-ID
  control and User A's complete document state remains unchanged.

## Actual result

- User A metadata before attack: 200
- Initial SQLite metadata present: Yes
- Initial stored file present: Yes
- Initial stored file hash matched input: Yes
- User B list: 200; User A document absent
- User B get User A document: 404
- Nonexistent-ID get control: 404
- Get response status/body identical: Yes
- User B delete User A document: 404
- Nonexistent-ID delete control: 404
- Delete response status/body identical: Yes
- Private metadata or phrase leakage count: 0
- Outcome: Pass

## Integrity verification after User B attempts

- User A metadata request: 200
- User A semantic search: 200
- Unique phrase still retrieved: Yes
- SQLite metadata still present: Yes
- Stored file still present: Yes
- Stored file SHA-256 still matched input: Yes
- Owner vector search preserved: Yes
- Owner database and file preserved: Yes

## Cleanup verification

- Authenticated User A deletion: 200
- SQLite metadata removed afterward: Yes
- Stored file removed afterward: Yes
- Cleanup succeeded: Yes

The later SEC-10 test will examine the full deletion lifecycle, including
post-deletion vector behavior, in more depth.

## Evidence

- Raw log: `evidence/raw/sec-cross-user-management-20261005T185203Z.json`
- Controlled-source screenshot: `SEC-03-01-private-source.png`
- Owner-before screenshot: `SEC-03-02-owner-before.png`
- User B list screenshot: `SEC-03-03-user-b-list.png`
- User B get/control screenshot: `SEC-03-04-get-denial-control.png`
- User B delete/control screenshot: `SEC-03-05-delete-denial-control.png`
- Owner-after screenshot: `SEC-03-06-owner-state-preserved.png`
- Summary/cleanup screenshot: `SEC-03-07-summary-cleanup.png`
- Ownership-code screenshot: `SEC-03-08-ownership-code.png`
- Screenshot status: Pending; capture from the controlled source, sanitized raw
  log, and narrow metadata/deletion ownership checks
- Secret review: no password, bearer token, internal stored filename or API key
  appears in the evidence

## Analysis and conclusion

Both metadata retrieval and deletion first queried SQLite using the requested
document ID together with the authenticated user's ID. Because this combined
ownership lookup returned no record for User B, both operations stopped with a
generic 404 before exposing metadata or deleting file/vector state.

No cross-user metadata or deletion vulnerability was demonstrated through the
public API. The result is stronger than checking the status code alone because
the test also confirmed that User A's database record, file bytes and vector
search remained usable after the unauthorized delete attempt.

## Risk and recommendation

- Confirmed vulnerability: No
- Severity: Not applicable
- Control result: Effective for tested list, metadata and deletion operations
- Recommendation: retain ownership-filtered database lookups, keep foreign and
  nonexistent responses identical, and add this two-user state-integrity test
  as automated regression coverage.
