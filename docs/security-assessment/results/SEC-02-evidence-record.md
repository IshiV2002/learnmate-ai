# SEC-02 Evidence Record - Cross-User Search Authorization

## Test identity

- Test ID: SEC-02
- Category: Broken Object Level Authorization and semantic-search isolation
- Execution time: 2026-10-06 00:17 Asia/Colombo
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
- User B knew the exact document ID but did not own the document.
- Passwords and bearer tokens were not recorded.

## Test definition

- Objective: determine whether an authenticated User B can search a known
  document ID belonging to User A.
- Positive control: User A searches the document and retrieves the unique
  phrase.
- Isolation check: User B lists their documents and must not see User A's
  document.
- Attack: User B searches User A's exact document ID five times.
- Non-disclosure control: User B searches a random nonexistent document ID five
  times using the same query.
- Expected: User B receives the same generic 404 response for both IDs, no
  private text or metadata is returned, and User A retains access afterward.

## Actual result

- User A upload: 201
- User A positive-control search: 200
- Unique phrase retrieved for User A: Yes
- User B list: 200 with no User A document
- User B attempts against User A's ID: 5/5 returned 404
- Nonexistent-ID control attempts: 5/5 returned 404
- Response body in every denial: `{"detail":"Document not found."}`
- Known-ID and nonexistent-ID status/body identical: Yes
- Cross-document leakage count: 0
- User A search after User B attempts: 200
- User A unique phrase still retrievable: Yes
- Cleanup deletion: 200
- Outcome: Pass

## Timing observation

- Median denial latency for User A's known ID: 19.45 ms
- Median denial latency for the nonexistent ID: 19.70 ms
- Difference between medians: 0.25 ms

The five-repetition sample did not show an obvious timing distinction. This is
not sufficient to prove that no timing side channel exists; the primary SEC-02
criterion is the identical status/body and zero content leakage.

## Evidence

- Raw log: `evidence/raw/sec-cross-user-search-20261005T184703Z.json`
- Controlled-source screenshot: `SEC-02-01-private-source.png`
- Owner positive-control screenshot: `SEC-02-02-owner-search.png`
- User B list screenshot: `SEC-02-03-user-b-list.png`
- Cross-user denial screenshot: `SEC-02-04-cross-user-denial.png`
- Nonexistent-ID control screenshot: `SEC-02-05-nonexistent-control.png`
- Summary and cleanup screenshot: `SEC-02-06-summary-cleanup.png`
- Ownership-code screenshot: `SEC-02-07-ownership-code.png`
- Screenshot status: Pending; capture from the controlled source, sanitized raw
  log and narrow ownership-check code section
- Secret review: no passwords, JWT values or API keys appear in the evidence

## Analysis and conclusion

The API looked up the requested document using both `document_id` and the
authenticated `current_user.user_id` before semantic retrieval. User B's request
therefore stopped with a generic 404 and never returned Chroma results. Using
the same response for a known foreign ID and a nonexistent ID also avoided
directly disclosing whether the resource existed.

No cross-user semantic-search vulnerability was demonstrated through the
public API. This result evaluates the HTTP endpoint only. It does not prove that
every future internal agent call is safely scoped, so internal Retrieval Agent
consumers should continue to receive authorized document IDs from an ownership-
checked orchestration layer.

## Risk and recommendation

- Confirmed vulnerability: No
- Severity: Not applicable
- Control result: Effective for tested cross-user semantic search
- Recommendation: retain the ownership-filtered lookup before retrieval, keep
  foreign and nonexistent responses indistinguishable, and add this two-user
  scenario as an automated regression test.
