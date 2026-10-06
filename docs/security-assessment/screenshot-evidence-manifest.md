# Screenshot Evidence Manifest

## Purpose and storage

This manifest records the essential baseline screenshots captured for the
Retrieval Agent and security assessment. The image files are stored locally in:

`docs/security-assessment/evidence/raw/screenshots/`

That directory is intentionally ignored by Git because screenshots can contain
local execution details. Selected images will later be inserted into the final
individual report with numbered captions and appropriate cropping/redaction.

## Shared baseline evidence

- `BASELINE-01-identity.png`
  - Proves the assessed branch, full commit hash, Windows environment and 20/20
    execution completion.
- `BASELINE-02-outcome-totals.png`
  - Shows 14 Passed, 6 Failed, 0 Inconclusive, 5 unique findings and the 111-test
    backend regression result.
- `BASELINE-03-retrieval-tests.png`
  - Shows the outcome of IR-01 through IR-10, including the IR-10A/IR-10B split.
- `BASELINE-04-security-tests.png`
  - Shows the outcome of SEC-01 through SEC-10.
- `ENV-01-runtime-versions.png`
  - Records FastAPI 0.141.1, ChromaDB 1.5.9 and Sentence Transformers 5.7.0.
- `ENV-02-backend-health.png`
  - Shows the local `/health` endpoint returning `healthy`.

## RET-01 - Missing semantic relevance threshold

- `RET-01-01-irrelevant-result.png`
  - Shows the unrelated bread query returning an Orion Protocol chunk with a
    distance above 1.0.
- `RET-01-02-ground-truth-and-fail.png`
  - Shows that the source contained no cooking information, three irrelevant
    results were returned, and the outcome was Fail.
- `RET-01-03-no-threshold-code.png`
  - Shows Chroma queried with `n_results=top_k` and every candidate appended
    without a calibrated relevance threshold.
- `RET-01-04-risk-assessment.png`
  - Records impact 2/5, likelihood 4/5, score 8/25 and Medium severity.

## RET-02 - Unsafe retrieved-instruction handling

- `RET-02-01-prompt-injection-failure.png`
  - Shows malicious PDF content retrieved, presented as a core definition,
    explicitly not rejected, and marked Fail.
- `RET-02-02-tutor-reply-and-citation.png`
  - Shows the unsafe fallback reply and its page-3 citation.
- `RET-02-03-ocr-corroboration.png`
  - Shows the same trust-boundary failure through OCR-derived image content.
- `RET-02-04-fallback-code.png`
  - Shows the fallback selecting `lecture_chunks[0]` and building its reply from
    that excerpt.
- `RET-02-05-description-and-risk.png`
  - Records the root cause, PDF/OCR evidence and Medium 9/25 risk.
- `RET-02-06-mitigation.png`
  - Records the proposed PDF/OCR untrusted-content handling and regression tests.

## RET-03 - Conflicting evidence ignored

- `RET-03-01-conflict-failure.png`
  - Shows both claim pages retrieved, only one value stated and the outcome Fail.
- `RET-03-02-both-citations.png`
  - Shows the reply using the 30-credit claim while citations also contain the
    incompatible 45-credit claim.
- `RET-03-03-risk-and-mitigation.png`
  - Records the first-chunk root cause, Medium 9/25 risk and conflict-handling
    mitigation.
- Reused root-cause screenshot: `RET-02-04-fallback-code.png`
  - The same `lecture_chunks[0]` selection explains RET-03.

The raw runner's broad `conflict_acknowledged` heuristic produced a false
positive because quoted source text contained `CONTRADICTORY`. The assessment
conclusion relies on the actual reply and its failure to state/compare both
values, not on that flag alone.

## SEC-F01 - Malformed PDF cleanup failure on Windows

- `SEC-F01-01-corrupt-pdf-failure.png`
  - Shows a corrupt PDF returning 500 and leaving one orphan while SQLite and
    Chroma remain unchanged.
- `SEC-F01-02-truncated-pdf-failure.png`
  - Shows the same failure using a separately truncated valid PDF.
- `SEC-F01-03-summary-and-orphans.png`
  - Shows 3/5 cases passed, two orphan uploads, healthy service and failed
    automatic cleanup.
- `SEC-F01-04-sanitized-server-error.png`
  - Links PyMuPDF parser errors to Windows `PermissionError [WinError 32]`
    without exposing personal paths or generated filenames.
- `SEC-F01-05-unprotected-cleanup-code.png`
  - Shows the unprotected `stored_path.unlink(missing_ok=True)` call masking the
    intended controlled response.
- `SEC-F01-06-risk-and-mitigation.png`
  - Records High 12/25 risk, recommended remediation and residual parser risk.

## SEC-F02 - Unbounded semantic-search requests

- `SEC-F02-01-query-length-progression.png`
  - Shows increasing query lengths accepted with 200 and no bounded rejection.
- `SEC-F02-02-summary-and-burst.png`
  - Shows a maximum accepted tested length of 32,768 characters, 12/12 burst
    responses returning 200, no observed rate limit, healthy service and Fail.
- `SEC-F02-03-no-query-length-limit.png`
  - Shows a blank-only query validator with no maximum length.
- `SEC-F02-04-no-rate-limit-middleware.png`
  - Shows the assessed FastAPI application middleware/router setup with no
    application-level rate limiter.
- `SEC-F02-05-risk-and-mitigation.png`
  - Records Medium 8/25 risk and the proposed length/rate controls.

The middleware screenshot is evidence only for the assessed application code.
It does not claim that a future proxy, gateway or hosted deployment lacks
external throttling.

## Capture status

- Essential environment and outcome screenshots: Complete
- All five confirmed findings: Complete
- Screenshot files present locally: 30
- Screenshot directory ignored by Git: Yes
- Application remediation started: No
