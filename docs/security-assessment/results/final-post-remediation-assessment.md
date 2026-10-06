# Final Post-Remediation Retrieval and Security Assessment

## Executive result

All 20 planned top-level assessment tests passed on the final assessed
application snapshot. IR-10 was executed as two declared subcases, IR-10A and
IR-10B. The five failures that produced confirmed findings during the baseline
assessment were no longer reproducible with the same controlled inputs.

- Planned top-level tests: 20
- Executed top-level tests: 20
- Passed: 20
- Failed: 0
- Inconclusive: 0
- Confirmed baseline findings reassessed: 5
- Demonstrated baseline failure modes mitigated: 5
- Backend automated regression tests: 129 passed, 0 failed
- Frontend automated tests: 20 passed, 0 failed
- Frontend production build: Pass

This result is evidence for the tested local snapshot and controlled corpus. It
is not a guarantee that the application is free from every vulnerability or
that retrieval and AI-generated answers are always correct.

## Assessment identity

- Branch: `feature/retrieval-agent`
- Assessed commit: `5d14958e8857e1414fe1dc04602938762c0d6aae`
- Assessment date: 2026-10-06
- Environment: local Microsoft Windows development instance
- Python: 3.14.7
- FastAPI: 0.141.1
- ChromaDB: 1.5.9
- Sentence Transformers: 5.7.0
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Tutor mode assessed: deterministic fallback
- Gemini path assessed: No
- Node.js: 22.17.1
- pnpm: 11.21.0

All final raw evidence files identify the same assessed Git commit. Synthetic
passwords and bearer tokens were held only in process memory and were not
written to the evidence files.

## Methodology

The final assessment reused the frozen synthetic corpus and the same declared
pass criteria used for the baseline. Each runner created fresh synthetic users
and resources, recorded sanitized JSON evidence, checked expected state, and
cleaned up its own documents and sessions.

The test groups covered:

- retrieval accuracy, ranking, chunk boundaries and page provenance;
- irrelevant queries, keyword manipulation, prompt injection, contradictory
  evidence and OCR-derived text;
- JWT enforcement and cross-user authorization;
- filename traversal, extension, MIME and signature validation;
- corrupt, truncated, protected and empty-content files;
- byte, decoded-pixel, query-length and request-rate limits; and
- deletion across file storage, SQLite and ChromaDB.

Backend, frontend and build checks were executed separately from the security
runners to detect regressions outside the controlled assessment cases.

## Information-retrieval results

- IR-01 exact-fact retrieval: Pass
- IR-02 paraphrased semantic retrieval: Pass
- IR-03 synonym and acronym retrieval: Pass
- IR-04 chunk-boundary evidence: Pass
- IR-05 page-reference integrity: Pass
- IR-06 irrelevant-query handling: Pass; zero unrelated results returned
- IR-07 keyword-stuffing manipulation: Pass; factual evidence remained rank 1
- IR-08 retrieved prompt-injection handling: Pass
- IR-09 contradictory-source reliability: Pass
- IR-10A clean OCR accuracy and provenance: Pass
- IR-10B adversarial OCR handling: Pass

Retrieval quality metrics for IR-01 to IR-03 were Hit@1 = 0.6667, Hit@3 = 1.0
and mean reciprocal rank = 0.8333. These values show that every expected answer
appeared within the first three results, but not every answer ranked first.

## Security results

- SEC-01 JWT enforcement: Pass; 20 of 20 request cases passed
- SEC-02 cross-user search authorization: Pass; no private phrase leakage
- SEC-03 cross-user metadata and deletion authorization: Pass
- SEC-04 filename and path traversal: Pass; six of six cases passed
- SEC-05 extension, MIME and signature validation: Pass; nine rejection cases
  and the valid uppercase-PDF control passed
- SEC-06 malformed and protected file handling: Pass; five of five cases
  returned controlled errors without storage residue
- SEC-07 no-extractable-text rollback: Pass; two of two cases preserved all
  persistence layers
- SEC-08 resource-limit enforcement: Pass; byte and decoded-pixel boundaries
  behaved as declared
- SEC-09 query and request abuse: Pass; 1,024 characters was accepted, an
  excessive query was rejected, and four of 12 burst requests returned 429
- SEC-10 deletion lifecycle: Pass; file, SQLite metadata and Chroma chunks were
  removed and later operations matched nonexistent-resource controls

For SEC-09, query latency median was 44.77 ms and p95 was 131.99 ms. Burst
latency median was 149.66 ms and p95 was 185.91 ms. These local figures are
environment-specific and are not production performance guarantees.

## Finding reassessment

### RET-01 - Missing semantic relevance threshold

- Original risk: Medium, 8/25
- Final controlled result: IR-06 Pass
- Mitigation evidence: low-relevance candidates are removed using the
  configured cosine-distance threshold
- Residual limitation: threshold quality depends on the model, corpus,
  language and OCR quality

### RET-02 - Unsafe retrieved-instruction handling

- Original risk: Medium, 9/25
- Final controlled results: IR-08 and IR-10B Pass
- Mitigation evidence: instruction-like retrieved text is treated as untrusted
  data, explicitly rejected and not repeated as a core definition
- Residual limitation: pattern matching may miss obfuscated or multilingual
  instructions; Gemini behavior remains untested

### RET-03 - Conflicting retrieved evidence ignored

- Original risk: Medium, 9/25
- Final controlled result: IR-09 Pass
- Mitigation evidence: both 30-credit and 45-credit claims are stated with page
  references and the unresolved conflict is disclosed
- Residual limitation: the deterministic comparison covers explicit numeric
  claims with supported units, not every semantic contradiction

### SEC-F01 - Malformed-PDF cleanup failure

- Original risk: High, 12/25
- Final controlled result: SEC-06 Pass
- Mitigation evidence: malformed PDF content is validated before persistent
  storage; five malformed/protected cases preserved file, SQLite and Chroma
  state
- Residual limitation: hostile parser inputs can still consume CPU or memory,
  so dependency updates, timeouts, quotas and monitoring remain necessary

### SEC-F02 - Unbounded semantic-search requests

- Original risk: Medium, 8/25
- Final controlled result: SEC-09 Pass
- Mitigation evidence: excessive query length is rejected and authenticated
  request bursts receive HTTP 429 responses
- Residual limitation: limits require monitoring and tuning for realistic
  concurrent production use

The original scores remain historical pre-mitigation risk classifications.
This assessment does not assign lower residual scores without a separate,
documented residual-risk scoring exercise.

## Regression and build verification

Backend command and result:

```text
python -m unittest discover -s tests -q
Ran 129 tests in 49.155s
OK
```

Frontend command and result:

```text
pnpm test
20 tests passed, 0 failed

pnpm build
58 modules transformed
Build completed successfully
```

The frontend build produced `dist/index.html`, the compiled CSS bundle and the
compiled JavaScript bundle. `git diff --check` also completed without errors.

## Raw evidence index

- IR-01 to IR-03: `ir-baseline-20261006T175524Z.json`
- IR-04 to IR-05: `ir-chunk-provenance-20261006T175640Z.json`
- IR-06 to IR-07: `ir-relevance-manipulation-20261006T175643Z.json`
- IR-08 to IR-09: `ir-tutor-integrity-20261006T175644Z.json`
- IR-10A to IR-10B: `ir-ocr-20261006T175646Z.json`
- SEC-01: `sec-jwt-20261006T175648Z.json`
- SEC-02: `sec-cross-user-search-20261006T175649Z.json`
- SEC-03: `sec-cross-user-management-20261006T175651Z.json`
- SEC-04: `sec-path-traversal-20261006T175653Z.json`
- SEC-05: `sec-type-validation-20261006T175657Z.json`
- SEC-06: `sec-malformed-files-20261006T175701Z.json`
- SEC-07: `sec-empty-content-20261006T175706Z.json`
- SEC-08: `sec-resource-limits-20261006T175710Z.json`
- SEC-09: `sec-query-abuse-20261006T175714Z.json`
- SEC-10: `sec-deletion-lifecycle-20261006T175718Z.json`

Raw evidence remains intentionally ignored by Git because it records local test
runs. The report-ready summary and remediation records are committed.

## Screenshot checklist

Capture these final screenshots without exposing terminal secrets or local
personal paths:

1. This report's Executive result and Assessment identity sections.
2. The final IR evidence summaries showing IR-01 through IR-10B as passed.
3. The final SEC evidence summaries showing SEC-01 through SEC-10 as passed.
4. IR-08 and IR-09 response fields showing the safety rejection, both numeric
   values, page references and explicit conflict statement.
5. SEC-06 summary showing five controlled rejections and preserved storage.
6. SEC-09 summary showing the 1,024-character boundary and 429 burst responses.
7. The backend `Ran 129 tests` and `OK` terminal lines.
8. The frontend `20 tests passed` and successful Vite build terminal lines.
9. The final clean `git status` and assessed commit hash.

## Final conclusion

The final controlled assessment provides repeatable evidence that all 20
planned retrieval and security tests pass on commit `5d14958`. Each of the five
baseline findings has a scoped mitigation, automated regression coverage and a
post-fix reproduction result. Claims remain limited to the local deterministic
fallback and synthetic corpus; Gemini behavior and broader production-scale
threats require separate evaluation.
