# SEC-F01 Remediation Verification

## Verification identity

- Finding: SEC-F01 - Malformed PDF Cleanup Failure on Windows
- Test: SEC-06
- Original baseline commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Reconfirmed affected commit: `bec9feb60d8dd643ceee8eb6ab54d3db47c563a9`
- Remediation commit: `2415416437482c97ece7c3c268e0fb0c1cf7191c`
- Verification date: 2026-10-06
- Environment: local Microsoft Windows development instance

## Before remediation

The targeted reassessment on `bec9feb` reproduced the original defect:

- the corrupt PDF returned 500 and left one orphan file;
- the truncated valid PDF returned 500 and left one orphan file;
- SQLite and Chroma remained unchanged;
- the service remained healthy; and
- manual hash-verified cleanup was required after stopping the backend.

Raw evidence: `sec-malformed-files-20261006T084851Z.json`.

## Implemented control

The upload flow now parses and validates PDF bytes in memory before writing a
persistent upload file. Invalid PDF inputs therefore cannot create stored-file
residue. The PDF service keeps its path-based interface for other callers, but
reads that path into bytes before PyMuPDF parsing to avoid holding a Windows
file lock on the path.

Regression tests were added for both controlled inputs:

- a 39-byte PDF-signature file with intentionally invalid content; and
- a valid generated PDF truncated to 128 bytes.

Both tests require a controlled 400 response, no Retrieval Agent indexing, no
SQLite metadata and no persistent PDF.

## Post-remediation SEC-06 result

The assessment runner was repeated against the exact remediation commit.

- Cases executed: 5
- Cases passed: 5
- Cases failed: 0
- Corrupt PDF: 400, Pass, zero new orphan uploads
- Truncated valid PDF: 400, Pass, zero new orphan uploads
- Password-protected PDF: 400, Pass
- Corrupt PNG: 400, Pass
- Corrupt JPEG: 400, Pass
- No internal details exposed: Yes
- Upload state preserved: Yes
- SQLite state preserved: Yes
- Chroma state preserved: Yes
- Service healthy after every case: Yes
- Valid upload after malformed cases: Yes
- Final upload PDF count: 3, equal to the pre-test baseline
- Final test-user document count: 0
- Final Chroma record count: 55, equal to the pre-test baseline
- Orphan upload PDF count: 0

Raw evidence: `sec-malformed-files-20261006T090552Z.json`.

## Automated regression result

The complete backend test suite was rerun from the `backend` directory on the
committed remediation snapshot:

```text
python -m unittest discover -s tests -v
Ran 116 tests in 38.104s
OK
```

The suite includes the two new malformed-PDF regression tests as well as the
existing upload, retrieval, Tutor, Quiz, Recommendation, authentication,
database, OCR and document-lifecycle tests.

## Security conclusion

The demonstrated SEC-F01 failure mode is remediated on commit `2415416`:
malformed PDFs are rejected before persistent storage, so the tested Windows
file-lock path can no longer replace the controlled client response or leave
orphan uploads.

Residual parser risk remains. Authenticated users can still submit inputs that
consume parsing CPU and memory within the configured byte limit. Upload quotas,
timeouts, monitoring and dependency patching remain recommended defense-in-
depth controls; they are separate from this verified cleanup fix.
