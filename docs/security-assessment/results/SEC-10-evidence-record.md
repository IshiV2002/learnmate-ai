# SEC-10 Evidence Record - Deletion Lifecycle

## Test identity

- Test ID: SEC-10
- Category: Data-deletion completeness and post-deletion access
- Execution time: 2026-10-06 01:26 Asia/Colombo
- Tester: Individual Student 4 assessor
- Git commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Target: local LearnMate FastAPI instance
- Account: fresh synthetic deletion-testing account

## Test definition

- Objective: verify that authorized deletion removes the stored file, SQLite
  metadata and every Chroma chunk, and that later API calls reveal no content.
- Setup: upload and index a controlled four-page PDF.
- Before deletion: verify metadata retrieval, semantic search, stored-file hash,
  SQLite record and per-document Chroma count.
- After deletion: repeat get, search and delete; compare each with a random
  nonexistent-ID control; inspect the document library and all storage layers.

## Initial state

- Upload-directory PDF count: 3
- Synthetic user's SQLite document count: 0
- Chroma record count: 55
- Service health: 200 and `healthy`

## Before deletion

- Upload status: 201
- Public metadata get: 200
- Semantic search: 200 with three results
- Expected source fact present: Yes
- SQLite metadata present: Yes
- Stored file present: Yes
- Stored-file hash matched controlled input: Yes
- Document-specific Chroma chunk count: 4
- All representations present: Yes

## Authorized deletion

- Delete status: 200
- Public response: `Document deleted successfully`

## After deletion

- Get deleted document: 404
- Search deleted document: 404
- Delete same document again: 404
- Synthetic user's library: 200 with zero documents
- Each deleted-ID response matched its nonexistent-ID control: Yes
- SQLite metadata absent: Yes
- Stored file absent: Yes
- Document-specific Chroma chunk count: 0
- Deleted source phrase absent from later responses: Yes
- State returned exactly to initial baseline: Yes
- Service healthy: Yes

Using the same generic response for deleted and never-existing identifiers
prevents the API from revealing whether a document previously existed.

## Summary

- All representations present before deletion: Yes
- Authorized deletion succeeded: Yes
- All later protected operations returned 404: Yes
- Deleted and nonexistent responses matched: Yes
- File, SQLite metadata and Chroma chunks removed: Yes
- Private content absent after deletion: Yes
- Exact baseline restored: Yes
- Overall outcome: Pass

## Evidence

- Raw log: `evidence/raw/sec-deletion-lifecycle-20261005T195630Z.json`
- Pre-deletion screenshot: `SEC-10-01-representations-before.png`
- Authorized-delete screenshot: `SEC-10-02-authorized-delete.png`
- Post-delete API screenshot: `SEC-10-03-post-delete-responses.png`
- Storage-removal screenshot: `SEC-10-04-storage-removal.png`
- Summary screenshot: `SEC-10-05-summary.png`
- Cleanup screenshot: `SEC-10-06-cleanup.png`
- Delete-order code screenshot: `SEC-10-07-delete-order-code.png`
- Screenshot status: Pending
- Secret review: no password, token, stored filename or personal path was
  recorded

## Analysis and conclusion

Deletion was complete across all three persistence layers. Chroma records and
the stored file were removed before SQLite metadata, while the metadata still
provided enough information to perform the cleanup. After success, the API
revealed no distinction between the deleted identifier and an identifier that
never existed.

No deletion-lifecycle vulnerability was demonstrated on the assessed commit.
This test covers immediate local deletion, not backup retention, audit-log
retention, distributed caches or external object storage.

## Risk and recommendation

- Confirmed vulnerability: No
- Severity: Not applicable
- Control result: Effective for immediate local application state
- Recommendation: retain the deletion order and generic 404 behavior, automate
  this lifecycle as a regression test, and document backup/retention behavior
  if the application later uses hosted storage.
