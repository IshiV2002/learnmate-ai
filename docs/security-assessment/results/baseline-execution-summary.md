# Retrieval and Security Baseline Execution Summary

## Baseline identity

- Assessed branch: `feature/retrieval-agent`
- Assessed application commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Environment: local Microsoft Windows development instance
- Planned assessment tests: 20
- Executed assessment tests: 20
- Execution completion: 100%

Assessment documentation and runners were created in the working tree while
the application remained at the commit above. No application-code remediation
was performed before or during baseline execution.

## Outcome totals

- Passed: 14
- Failed: 6
- Inconclusive: 0
- Unique confirmed findings: 5
- Full backend regression suite after assessment: 111 tests passed, 0 failed

## Retrieval tests

- IR-01 exact-fact retrieval: Pass
- IR-02 paraphrased semantic retrieval: Pass
- IR-03 synonym and acronym retrieval: Pass
- IR-04 chunk-boundary evidence: Pass
- IR-05 page-reference integrity: Pass
- IR-06 irrelevant-query handling: Fail (`RET-01`)
- IR-07 keyword-stuffing manipulation: Pass
- IR-08 retrieved prompt-injection text: Fail (`RET-02`)
- IR-09 contradictory-source reliability: Fail (`RET-03`)
- IR-10 OCR accuracy and manipulation: Fail overall
  - IR-10A clean OCR accuracy: Pass
  - IR-10B adversarial OCR handling: Fail; corroborates `RET-02`

## Security tests

- SEC-01 JWT enforcement: Pass
- SEC-02 cross-user search authorization: Pass
- SEC-03 cross-user metadata/deletion authorization: Pass
- SEC-04 filename and path traversal: Pass
- SEC-05 extension, MIME and signature validation: Pass
- SEC-06 malformed and protected file handling: Fail (`SEC-F01`)
- SEC-07 no-extractable-text rollback: Pass
- SEC-08 resource-limit enforcement: Pass
- SEC-09 query and request abuse: Fail (`SEC-F02`)
- SEC-10 deletion lifecycle: Pass

## Confirmed findings

1. `RET-01` - Missing semantic relevance threshold
   - Score: 8/25
   - Severity: Medium
2. `RET-02` - Unsafe retrieved-instruction handling in deterministic Tutor
   fallback
   - Score: 9/25
   - Severity: Medium
3. `RET-03` - Conflicting retrieved evidence ignored by deterministic Tutor
   fallback
   - Score: 9/25
   - Severity: Medium
4. `SEC-F01` - Malformed PDF cleanup failure on Windows
   - Score: 12/25
   - Severity: High
5. `SEC-F02` - Unbounded semantic-search requests
   - Score: 8/25
   - Severity: Medium

Risk matrix: 1-4 Low, 5-9 Medium, 10-16 High, 17-25 Critical.

## Effective controls demonstrated

- JWT rejection for missing, malformed, tampered and expired tokens
- Per-user ownership isolation for document metadata, search and deletion
- Safe internal filenames and upload-directory containment
- Extension, MIME and file-signature validation
- Blank-content rollback across upload, SQLite and Chroma
- Exact byte-size and decoded-image-pixel limits
- Complete immediate deletion across file, SQLite and Chroma representations
- Generic non-disclosing 404 behavior for foreign, deleted and nonexistent IDs

## Important scope limitations

- Tutor manipulation/conflict findings apply to the deterministic fallback;
  Gemini was not enabled and was not claimed as tested.
- OCR accuracy used one controlled high-contrast English image and does not
  establish accuracy for handwriting, complex layouts or other languages.
- SEC-09 used a safe local 12-request burst, not a denial-of-service attempt.
- SEC-10 covers immediate local application state, not external backups or
  future hosted storage.
- Tests used synthetic accounts and controlled local documents only.

## Evidence status

- Separate evidence record exists for every test ID.
- Sanitized raw JSON logs are retained locally under ignored `evidence/raw/`.
- Generated test documents are retained locally under ignored `generated/`.
- Passwords, bearer tokens, signing secrets and production credentials were not
  recorded.
- Screenshot checklist is complete; baseline screenshots remain to be captured
  before application remediation changes relevant code lines.

## Next phase

The baseline is complete. The next work phase is evidence presentation and
remediation: capture baseline screenshots, commit the validated assessment
support, synchronize the feature branch with `origin/develop`, prioritize
fixes, and create before/after regression evidence without mixing commit hashes.
