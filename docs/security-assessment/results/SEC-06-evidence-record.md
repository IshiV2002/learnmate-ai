# SEC-06 Evidence Record - Malformed and Protected File Handling

## Test identity

- Test ID: SEC-06
- Category: File-parser failure handling and persistence safety
- Execution time: 2026-10-06 00:40 Asia/Colombo
- Tester: Individual Student 4 assessor
- Git commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Target: local LearnMate FastAPI instance on Windows
- Account: fresh synthetic malformed-file-testing account

## Test definition

- Objective: verify that corrupt, truncated and protected materials return a
  controlled client error, do not leave persistent state, and do not make the
  service unavailable.
- Inputs:
  1. Corrupt PDF with a valid PDF signature
  2. A valid PDF truncated to its first 128 bytes
  3. Password-protected PDF
  4. Corrupt PNG with a valid PNG signature
  5. Corrupt JPEG with a valid JPEG signature
- Positive control: a valid text PDF uploaded after all malformed cases.
- Expected: each malformed input returns a controlled 4xx response, creates no
  upload, SQLite or Chroma residue, exposes no internal detail, and leaves the
  service healthy.

## Baseline persistence state

- Upload-directory PDF count: 3
- Synthetic user's SQLite document count: 0
- Chroma record count: 55

Each case took a fresh state snapshot immediately before its request. This
prevents one failed cleanup from falsely changing the result of later cases.

## Corrected final results

- Cases executed: 5
- Cases passed: 3
- Cases failed: 2
- Overall outcome: Fail

### Failed cases

- Corrupt PDF: returned 500 and left one stored PDF residue.
- Truncated valid PDF: returned 500 and left one stored PDF residue.
- SQLite remained unchanged in both cases.
- Chroma remained unchanged in both cases.
- `GET /health` returned 200 after both cases.
- The client saw only `Internal Server Error`; no traceback, internal path or
  generated server filename was exposed.

### Passed cases

- Password-protected PDF: controlled 400, no persistent state change.
- Corrupt PNG: controlled 400, no persistent state change.
- Corrupt JPEG: controlled 400, no persistent state change.
- The service remained healthy after every case.

### Positive control

- Valid PDF upload after malformed inputs: 201.
- Page count: 4.
- Chunk count: 4.
- The control document was deleted successfully after verification.

This confirms that the endpoint was operational and that the failures were
specific to malformed-PDF cleanup rather than a general service outage.

## Technical root cause

`extract_pdf_pages` catches PyMuPDF parser failures and raises the intended
application-level `PDFExtractionError`. The upload endpoint then tries to
delete the stored file before returning a controlled 400 response.

On Windows, the rejected corrupt/truncated PDF remained locked when
`stored_path.unlink(missing_ok=True)` ran. That cleanup call raised
`PermissionError [WinError 32]`. Because the cleanup exception was not handled,
it replaced the intended 400 with a generic 500 and left the file behind.

The two underlying parser failures were different (`no objects found` and
`truncated object`), but both reached the same cleanup defect.

## Preliminary run exclusion

The earlier log `sec-malformed-files-20261005T190800Z.json` is retained as a
preliminary diagnostic run but excluded from final counts. Its runner compared
later cases with one global baseline, so the first orphan file incorrectly
made otherwise safe later cases look state-changing. The corrected final run
snapshotted state before every case and produced the 3-pass/2-fail result above.

## Cleanup verification

Immediately after the corrected run:

- Upload-directory PDF count: 5
- Expected baseline count: 3
- Orphan test files: 2
- Synthetic user's SQLite document count: 0
- Chroma record count: 55

The two residues were identified using the controlled input SHA-256 hashes.
They were removed only after the backend was stopped so that the Windows locks
were released. This manual evidence cleanup does not change the baseline test
outcome.

## Risk assessment

- Finding: `SEC-F01`
- Confidentiality impact demonstrated: None
- Integrity impact demonstrated: None in SQLite or Chroma
- Availability impact: 3/5 - each malformed PDF causes a 500 and retains file
  data. Repeated authenticated uploads can consume storage, although no service
  outage was demonstrated.
- Likelihood: 4/5 - any authenticated user can submit a small malformed PDF,
  and both controlled malformed forms reproduced the defect.
- Risk score: 12/25.
- Preliminary severity: High.
- Matrix: 1-4 Low, 5-9 Medium, 10-16 High, 17-25 Critical.

The 10 MiB per-request upload limit restricts individual-file size but does not
prevent repeated storage consumption. Rate limiting and per-user quotas were
not present in this baseline assessment.

## Recommended mitigation

1. Prefer validating/extracting PDF content before moving it into persistent
   upload storage, or use a clearly managed temporary-file lifecycle.
2. Ensure every PyMuPDF document/resource is released before file deletion on
   Windows.
3. Handle cleanup `OSError` without replacing the intended safe client error,
   while also recording and retrying failed cleanup rather than silently
   accepting residue.
4. Add Windows regression tests for corrupt, truncated and protected PDFs.
5. Add upload rate limiting and per-user storage quotas to limit repeated
   resource consumption.
6. Re-run SEC-06 after remediation and verify the upload directory, SQLite and
   Chroma all return to their exact baselines.

## Evidence

- Corrected raw log:
  `evidence/raw/sec-malformed-files-20261005T191039Z.json`
- Sanitized server error excerpt:
  `evidence/raw/sec-malformed-files-20261005T191039Z-server-error.txt`
- Preliminary excluded log:
  `evidence/raw/sec-malformed-files-20261005T190800Z.json`
- Finding: `findings/SEC-F01-malformed-pdf-cleanup-failure.md`
- Screenshot status: Pending; capture the corrected raw-log blocks, sanitized
  server excerpt and narrow error-handling code section.
- Secret review: passwords, bearer tokens, signing secrets, personal paths and
  generated server filenames are absent from the formal evidence.

## Conclusion

Protected PDFs and corrupt images were rejected safely, and the service stayed
available. Corrupt and truncated PDFs exposed a repeatable Windows-specific
cleanup weakness that returns 500 and leaves stored-file residue. This is a
confirmed availability/resource-exhaustion risk, recorded as `SEC-F01`. The
application is intentionally not remediated until the remaining baseline tests
are complete.
