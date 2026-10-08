# Test Evidence Template

Copy this section once for every test case. Complete the expected result before
running the test so the conclusion is not influenced by the observed result.

## Test ID and title

- Test ID:
- Test title:
- Category:
- Date and time (with timezone):
- Tester:
- Git commit:

## Environment

- Operating system:
- Python version:
- FastAPI version:
- ChromaDB version:
- Sentence Transformer model:
- Gemini model, if involved:
- Chunk size and overlap:
- `top_k` value:
- Test account labels (never record real passwords):
- Input filename and SHA-256 from `manifest.json`:

## Test definition

- Objective:
- Input or attack scenario:
- Preconditions:
- Exact steps or sanitized request:
- Expected secure behaviour:
- Pass/fail criteria:

## Actual result

- HTTP status:
- Sanitized response or retrieval result:
- Returned source page(s):
- Returned rank(s) and distance(s):
- Duration in milliseconds:
- Storage state after the test (file, SQLite, ChromaDB):
- Actual behaviour:

## Evidence

- Screenshot or log filenames:
- What each item proves:
- Tokens, secrets and personal paths redacted: Yes / No

## Analysis

- Observation:
- Outcome: Pass / Fail / Inconclusive
- Technical explanation:
- Root cause, if demonstrated:
- Security or educational impact:
- Limitations or possible confounding factors:
- Conclusion:

## Finding and risk classification

Complete this section only when the evidence demonstrates a vulnerability.

- Finding ID:
- Impact score (1-5) and justification:
- Likelihood score (1-5) and justification:
- Risk score (impact multiplied by likelihood):
- Severity: Critical / High / Medium / Low / Informational
- Recommended mitigation:
- Residual risk:
- Regression test needed after mitigation:
