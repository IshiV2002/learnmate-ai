# SEC-F01 - Malformed PDF Cleanup Failure on Windows

## Status

- Evidence status: Confirmed and repeatable
- Related test: SEC-06
- Affected commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Reconfirmed commit: `bec9feb60d8dd643ceee8eb6ab54d3db47c563a9`
- Remediation status: Fixed and verified
- Fixed commit: `2415416437482c97ece7c3c268e0fb0c1cf7191c`
- Environment: Windows local FastAPI service

The High 12/25 rating documents the demonstrated pre-fix risk. It is retained
for the assignment's original risk assessment and is not a claim that the same
exposure remains after the verified remediation.

## Description

When PyMuPDF rejects a corrupt or truncated PDF, the upload endpoint attempts
to delete the stored file. On Windows the rejected file can still be locked,
causing the deletion to raise `PermissionError [WinError 32]`.

That secondary cleanup exception replaces the intended controlled 400 response
with a generic 500 and leaves the uploaded PDF on disk without corresponding
SQLite metadata or Chroma records.

## Reproduction summary

- A 39-byte corrupt PDF returned 500 and left one stored-file residue.
- A valid PDF truncated to 128 bytes returned 500 and left one stored-file
  residue.
- Both test inputs reproduced the same Windows cleanup failure.
- SQLite and Chroma counts remained unchanged.
- `GET /health` stayed 200, and a later valid upload returned 201.
- No stack trace, internal path or generated server filename reached the client.

## Technical root cause

`extract_pdf_pages` converts PyMuPDF parser exceptions to
`PDFExtractionError`. In the corresponding endpoint exception handler,
`stored_path.unlink(missing_ok=True)` is not protected against `OSError`.
The Windows file lock makes this unlink fail, so the cleanup exception masks
the intended API error and leaves residue.

## Impact

- Repeated authenticated malformed uploads can consume server disk space.
- Clients receive an unexpected 500 instead of a controlled validation error.
- Operational cleanup is required for files that have no metadata record.
- No confidentiality breach, SQLite corruption, Chroma corruption or sustained
  outage was demonstrated.

## Risk assessment

- Impact: 3/5 - repeatable disk residue and server errors, with no outage shown.
- Likelihood: 4/5 - simple authenticated malformed PDFs reproduce the issue.
- Risk score: 12/25.
- Preliminary severity: High.
- Matrix: 1-4 Low, 5-9 Medium, 10-16 High, 17-25 Critical.

## Recommended mitigation

1. Parse/validate from memory or a managed temporary file before persistent
   storage.
2. Ensure PyMuPDF resources are closed before cleanup on Windows.
3. Catch cleanup `OSError` without replacing the controlled client response,
   and reliably retry or reconcile failed cleanup.
4. Add Windows regression tests for corrupt and truncated PDF paths.
5. Add per-user upload quotas and request-rate controls.
6. Verify exact upload, SQLite and Chroma baseline restoration after the fix.

## Implemented mitigation and verification

The upload endpoint now parses and validates untrusted PDF bytes in memory
before creating a persistent upload file. The path-based PDF helper also reads
the file into memory before invoking PyMuPDF, so PyMuPDF no longer holds the
stored path open during parser-error handling.

Two automated regression tests cover the corrupt and truncated PDF paths. A
post-fix rerun of SEC-06 passed all five malformed/protected-file cases:

- corrupt and truncated PDFs returned controlled 400 responses;
- no upload, SQLite or Chroma state changed after rejected inputs;
- zero orphan upload files remained;
- the service stayed healthy and accepted a later valid upload; and
- the complete backend regression suite passed 116 tests.

See `results/SEC-F01-remediation-verification.md` for the full verification
record and evidence identity.

## Residual risk

Even after this file-lock defect is fixed, hostile parsers inputs may consume
CPU, memory or temporary storage. File-size limits, timeouts, quotas, monitoring
and dependency patching should accompany parser-error handling.
