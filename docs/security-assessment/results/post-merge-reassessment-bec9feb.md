# Post-Merge Retrieval and Security Reassessment

## Reassessment identity

- Assessed branch: `feature/retrieval-agent`
- Assessed commit: `bec9feb60d8dd643ceee8eb6ab54d3db47c563a9`
- Original frozen baseline: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Execution date: 2026-10-06
- Environment: local Microsoft Windows development instance
- Tutor execution mode: deterministic fallback; Gemini was not tested

This is a targeted post-merge reassessment. It does not replace or modify the
20-test frozen baseline. Results from the two commits must remain separate in
the final report.

## Change-impact review

Between the original baseline and this reassessment, the merge added broader
document-chunk loading for offline quiz generation and substantially expanded
quiz fallback generation. It did not add a semantic relevance threshold,
Tutor fallback conflict synthesis, request-length limits, rate limiting, or a
Windows-safe malformed-PDF cleanup path. The affected baseline cases were
therefore rerun against the new commit rather than assumed to be unchanged.

## Targeted results

- IR-06 irrelevant-query handling: **Fail**. The unrelated cooking query still
  returned three chunks from the controlled non-cooking document.
- IR-07 keyword-stuffing manipulation: **Pass**.
- IR-08 retrieved prompt-injection handling: **Fail**. The malicious page was
  retrieved and presented as a core definition without an explicit safety
  rejection.
- IR-09 contradictory-source reliability: **Fail**. Both claim pages were
  retrieved, but the Tutor response did not state both conflicting values.
- IR-10A clean OCR accuracy and retrieval: **Pass**. Character error rate and
  word error rate were both 0%, with correct source/page provenance.
- IR-10B adversarial OCR handling: **Fail**. The malicious OCR text ranked first
  and retained correct provenance, but was still presented as a core
  definition. This continues to corroborate RET-02 rather than constituting a
  separate vulnerability.
- SEC-06 malformed and protected file handling: **Fail overall**. Corrupt and
  truncated PDFs returned 500 and each left one upload residue. The
  password-protected PDF, corrupt PNG and corrupt JPEG were safely rejected
  with 400. SQLite and Chroma state were preserved, no internal details were
  exposed, and the service remained healthy.
- SEC-09 query and request abuse: **Fail**. Queries up to 32,768 characters were
  accepted. All 12 controlled requests returned 200 and no rate limit was
  observed. Query median/p95 latency was 55.68/66.93 ms; controlled-burst
  median/p95 latency was 62.04/70.28 ms. Storage state and service health were
  preserved.

## Finding status

All five original findings remain reproducible on commit `bec9feb`:

1. RET-01 missing semantic relevance threshold - Medium, 8/25.
2. RET-02 unsafe retrieved-instruction handling in deterministic Tutor fallback
   - Medium, 9/25.
3. RET-03 conflicting retrieved evidence ignored by deterministic Tutor
   fallback - Medium, 9/25.
4. SEC-F01 malformed-PDF cleanup failure on Windows - High, 12/25.
5. SEC-F02 unbounded semantic-search requests - Medium, 8/25.

No severity was increased solely because the behavior reproduced. The existing
impact and likelihood rationale remains applicable to this local reassessment.

## Evidence files

The detailed, sanitized JSON evidence is stored locally under the ignored
`docs/security-assessment/evidence/raw/` directory:

- `ir-relevance-manipulation-20261006T084653Z.json`
- `ir-tutor-integrity-20261006T084751Z.json`
- `ir-ocr-20261006T084825Z.json`
- `sec-malformed-files-20261006T084851Z.json`
- `sec-query-abuse-20261006T084914Z.json`

The SEC-06 runner reproduced two locked upload residues. After the backend was
stopped, each residue was matched to its controlled input by SHA-256 and only
those two files were removed. The upload directory then returned to its
three-PDF pre-test baseline.

## Regression result

The complete backend suite was executed from the `backend` directory after the
targeted reassessment:

```text
python -m unittest discover -s tests -v
Ran 114 tests in 39.154s
OK
```

This establishes that the merged application passed its existing automated
backend regression suite. It does not negate the five assessment findings,
because those adversarial acceptance criteria are not currently represented by
passing regression tests.
