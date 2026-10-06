# SEC-08 Evidence Record - Resource-Limit Enforcement

## Test identity

- Test ID: SEC-08
- Category: Upload resource controls
- Execution time: 2026-10-06 01:19 Asia/Colombo
- Tester: Individual Student 4 assessor
- Git commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Target: local LearnMate FastAPI instance
- Account: fresh synthetic resource-limit-testing account

## Configured limits

- Maximum upload size: 10,485,760 bytes (10 MiB)
- Maximum decoded image pixels: 25,000,000

## Test definition

Three controlled boundary cases were used:

1. A signature-valid PDF payload of 10,485,761 bytes, one byte above the limit.
2. A compressed 5,001 by 5,000 PNG that expands to 25,005,000 pixels.
3. A valid four-page PDF padded after its final EOF marker to 10,485,759
   bytes, one byte below the upload limit.

The two excessive cases were expected to return controlled 413 responses with
no file, SQLite or Chroma state change. The valid below-limit case was expected
to upload and index successfully.

## Baseline persistence state

- Upload-directory PDF count: 3
- Synthetic user's SQLite document count: 0
- Chroma record count: 55
- Service health: 200 and `healthy`

## Actual results

### One byte above upload limit

- Input size: 10,485,761 bytes
- Status: 413
- Latency: 121.73 ms
- Clear maximum-size message: Yes
- Upload state unchanged: Yes
- SQLite state unchanged: Yes
- Chroma state unchanged: Yes
- Service healthy: Yes
- Outcome: Pass

### Decoded image pixel limit

- Compressed file size: 32,605 bytes
- Decoded dimensions: 5,001 by 5,000
- Decoded pixels: 25,005,000
- Status: 413
- Latency: 89.01 ms
- Upload state unchanged: Yes
- SQLite state unchanged: Yes
- Chroma state unchanged: Yes
- Service healthy: Yes
- Outcome: Pass

This case is important because a small compressed image can require much more
memory after decoding. The application evaluated decoded dimensions rather than
trusting compressed file size alone.

### One byte below upload limit

- Input size: 10,485,759 bytes
- Status: 201
- Latency: 546.74 ms
- Reported file size matched input: Yes
- Upload count increased by one: Yes
- SQLite count increased by one: Yes
- Chroma count increased: Yes
- Service healthy: Yes
- Outcome: Pass

## Cleanup and summary

- Cases executed: 3
- Cases passed: 3
- Cases failed: 0
- Boundary document deletion: 200
- Final upload-directory count: 3
- Final synthetic-user document count: 0
- Final Chroma count: 55
- Exact baseline restored: Yes
- Overall outcome: Pass

## Evidence

- Raw log: `evidence/raw/sec-resource-limits-20261005T194926Z.json`
- Above-byte-limit screenshot: `SEC-08-01-byte-limit-rejection.png`
- Pixel-limit screenshot: `SEC-08-02-pixel-limit-rejection.png`
- Accepted-boundary screenshot: `SEC-08-03-below-limit-accepted.png`
- Summary screenshot: `SEC-08-04-summary.png`
- Cleanup screenshot: `SEC-08-05-cleanup.png`
- Limit-code screenshot: `SEC-08-06-limit-code.png`
- Screenshot status: Pending; capture from the sanitized raw log and narrow
  validation sections
- Secret review: no password, token, personal path or internal filename was
  recorded

## Analysis and conclusion

Both configured resource controls operated at their exact tested boundaries.
The API read only one byte beyond the configured upload limit to detect an
oversized request, and it rejected the image based on decoded pixel count before
OCR. The valid below-limit PDF proves that the oversized rejection was
selective rather than a broken upload service.

No vulnerability was demonstrated by SEC-08. Network/proxy request limits,
concurrent upload exhaustion and total per-user storage quotas are separate
controls and were not claimed as tested here.

## Risk and recommendation

- Confirmed vulnerability: No
- Severity: Not applicable
- Control result: Effective at the tested byte and decoded-pixel boundaries
- Recommendation: retain both limits, add these cases as regression tests, and
  complement per-request limits with rate limiting and per-user storage quotas.
