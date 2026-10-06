# SEC-05 Evidence Record - Extension, MIME and Signature Validation

## Test identity

- Test ID: SEC-05
- Category: File-upload validation and persistence safety
- Execution time: 2026-10-06 00:33 Asia/Colombo
- Tester: Individual Student 4 assessor
- Git commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Target: local LearnMate FastAPI instance
- Account: fresh synthetic file-type-testing account

## Controlled inputs

- Valid PDF SHA-256:
  `7d50bd155e43364a6acd9256871264ee3169d38937746113da3e2f6a9250ce5b`
- Valid PNG SHA-256:
  `a28cf898f5be383ec202a5b7056e8475507d72df365e995fbb8c4e43f88832c2`
- Non-PDF signature-mismatch file SHA-256:
  `52455a459acb34accc7f56cd0ec6a9835f05600995017b665f1c54e43c05f594`
- A JPEG byte stream was generated in memory from the controlled PNG.
- Password and bearer token were not recorded.

## Baseline persistence state

- Upload-directory PDF count: 3
- Synthetic user's SQLite document count: 0
- Chroma record count: 55

These counts were captured before the first rejection and compared after every
case.

## Test definition

- Objective: verify that extension, declared MIME type and file signature are
  validated authoritatively before file, SQLite or Chroma state is persisted.
- Rejection cases:
  1. `.pdf` with `image/png`
  2. `.png` with `application/pdf`
  3. `.jpg` with `image/png`
  4. `.pdf` with a non-PDF signature
  5. `.png` containing PDF bytes
  6. `.jpeg` containing PNG bytes
  7. Unsupported `.txt` containing PDF bytes
  8. `.pdf` with `application/octet-stream`
  9. Unsupported `.exe` with executable-like bytes
- Positive control: uppercase `VALID-UPPERCASE.PDF` with PDF MIME and signature.
- Expected: mismatches return controlled 400 or 415 responses with no state
  change; the matching uppercase control succeeds and is then removed.

## Actual rejection results

- Rejection cases executed: 9
- Rejection cases passed: 9
- Rejection cases failed: 0
- Wrong MIME for supported extension: controlled 415
- Wrong signature for declared format: controlled 400
- Unsupported extension: controlled 400
- Upload-directory state unchanged after every rejection: Yes
- Synthetic-user SQLite state unchanged after every rejection: Yes
- Global Chroma record count unchanged after every rejection: Yes

No rejection response exposed a traceback, storage path, database detail or
internal filename.

## Positive control

- Upload status: 201
- Public filename: `VALID-UPPERCASE.PDF`
- Page count: 4
- Chunk count: 4
- Upload-directory count increased: Yes
- SQLite document count increased: Yes
- Chroma record count increased: Yes
- Positive control outcome: Pass

This control shows that the test environment and upload endpoint were working;
the nine earlier results were selective rejections rather than a generally
broken upload endpoint.

## Cleanup verification

- Positive-control deletion: 200
- Final upload-directory PDF count: 3
- Final synthetic-user document count: 0
- Final Chroma record count: 55
- All three stores returned to baseline: Yes
- Cleanup succeeded: Yes
- Overall outcome: Pass

## Evidence

- Raw log: `evidence/raw/sec-type-validation-20261005T190314Z.json`
- MIME mismatch screenshot: `SEC-05-01-mime-mismatches.png`
- Signature mismatch screenshot: `SEC-05-02-signature-mismatches.png`
- Unsupported-type screenshot: `SEC-05-03-unsupported-types.png`
- Baseline screenshot: `SEC-05-04-baseline-state.png`
- Positive-control screenshot: `SEC-05-05-valid-control.png`
- Summary screenshot: `SEC-05-06-summary.png`
- Cleanup screenshot: `SEC-05-07-cleanup.png`
- Validation-code screenshot: `SEC-05-08-validation-code.png`
- Ordering-code screenshot: `SEC-05-09-validation-order.png`
- Screenshot status: Pending; capture from the sanitized log and narrow
  validation/upload-order code sections
- Secret review: no password, bearer token, API key or internal filename appears
  in the evidence

## Analysis and conclusion

The endpoint checks the safe display extension and allowed MIME pairing, then
checks the leading file signature before creating a storage path. This ordering
explains why all three persistence layers remained unchanged during rejection.

No extension, MIME or signature mismatch vulnerability was demonstrated by
these cases. Signature prefixes alone are not complete content validation: a
malicious file can begin with a valid marker but remain malformed. LearnMate
subsequently parses accepted material, and SEC-06 separately tests corrupt,
truncated and password-protected inputs. Malware scanning is outside the
current local application scope.

## Risk and recommendation

- Confirmed vulnerability: No
- Severity: Not applicable
- Control result: Effective for the nine tested mismatch/unsupported cases
- Recommendation: retain server-side extension, MIME and signature checks,
  preserve validation-before-persistence ordering, and automate these cases as
  regression tests.
