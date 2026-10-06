# SEC-07 Evidence Record - No-Extractable-Text Rollback

## Test identity

- Test ID: SEC-07
- Category: Empty-content validation and transactional cleanup
- Execution time: 2026-10-06 01:04 Asia/Colombo
- Tester: Individual Student 4 assessor
- Git commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Target: local LearnMate FastAPI instance
- Account: fresh synthetic empty-content-testing account

## Controlled inputs

- Blank one-page PDF SHA-256:
  `5ef121f272cef73053eb2d1bb2531a543d60e0e583fdeca3fe275063dfc82568`
- Blank PNG SHA-256:
  `a56fe544f0e13aab9d3005b8ed6b6ed3f601a320a69021c51390462257ac481a`
- Password and bearer token were not recorded.

## Test definition

- Objective: verify complete rollback when valid-format material produces no
  searchable text chunks.
- Cases:
  1. Valid blank PDF with no extractable text
  2. Valid blank PNG with no readable OCR text
- Expected: controlled 422, no success message, no internal-detail exposure,
  and no file, SQLite metadata or Chroma record residue.
- Positive control: upload a valid text PDF after both rejected inputs, then
  delete it and confirm exact baseline restoration.

## Baseline persistence state

- Upload-directory PDF count: 3
- Synthetic user's SQLite document count: 0
- Chroma record count: 55
- Health endpoint: 200 and `healthy`

## Actual results

### Blank PDF

- Status: 422
- Detail: `The PDF contains no extractable text. Scanned or image-only PDFs are
  not currently supported.`
- New stored-file residue: 0
- Upload-directory state unchanged: Yes
- SQLite state unchanged: Yes
- Chroma state unchanged: Yes
- Service healthy after rejection: Yes
- Outcome: Pass

### Blank image

- Status: 422
- Detail: `The image contains no readable text. Upload a clear image containing
  course material.`
- New stored-file residue: 0
- Upload-directory state unchanged: Yes
- SQLite state unchanged: Yes
- Chroma state unchanged: Yes
- Service healthy after rejection: Yes
- Outcome: Pass

Both bodies were clear user-facing validation responses. Neither exposed a
traceback, OCR/PDF library name, database detail, internal filename or storage
path.

## Positive control and cleanup

- Valid text PDF status: 201
- Page count: 4
- Chunk count: 4
- Positive-control deletion: 200
- Final upload-directory PDF count: 3
- Final synthetic-user SQLite document count: 0
- Final Chroma record count: 55
- Returned exactly to baseline: Yes
- Service healthy after cleanup: Yes
- Cleanup succeeded: Yes

## Summary

- Cases executed: 2
- Cases passed: 2
- Cases failed: 0
- All responses controlled 422: Yes
- Upload, SQLite and Chroma state preserved: Yes
- Service healthy after every case: Yes
- Valid control succeeded: Yes
- Overall outcome: Pass

## Evidence

- Raw log: `evidence/raw/sec-empty-content-20261005T193414Z.json`
- Blank-PDF screenshot: `SEC-07-01-blank-pdf.png`
- Blank-image screenshot: `SEC-07-02-blank-image.png`
- Baseline screenshot: `SEC-07-03-baseline.png`
- Valid-control screenshot: `SEC-07-04-valid-control.png`
- Summary screenshot: `SEC-07-05-summary.png`
- Cleanup screenshot: `SEC-07-06-cleanup.png`
- Rollback-code screenshot: `SEC-07-07-rollback-code.png`
- Screenshot status: Pending; capture from the sanitized log and narrow
  zero-chunk handler in `documents.py`
- Secret review: no password, bearer token, signing secret, personal path or
  internal filename appears in the evidence record

## Analysis and conclusion

The endpoint correctly distinguishes a structurally valid upload from material
that can contribute searchable knowledge. It performs extraction/OCR and
chunking before reporting success. When chunking returns no usable content, it
removes the stored material and returns a clear 422 response before creating
the document metadata or vector records.

The blank-image result also shows that OCR was available during this test; a
missing OCR installation would have produced a different 503 path.

No vulnerability was demonstrated by SEC-07. The no-extractable-text rollback
control was effective for both tested material types on the assessed commit.

## Risk and recommendation

- Confirmed vulnerability: No
- Severity: Not applicable
- Control result: Effective
- Recommendation: retain the rollback behavior and add automated regression
  tests that assert the 422 bodies and exact three-store baseline restoration
  for both blank PDFs and images.
