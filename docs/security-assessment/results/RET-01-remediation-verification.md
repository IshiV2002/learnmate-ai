# RET-01 Remediation Verification

## Verification identity

- Finding: RET-01 - Missing Semantic Relevance Threshold
- Primary test: IR-06
- Regression tests: IR-01 through IR-07
- Original baseline commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Reconfirmed affected commit: `bec9feb60d8dd643ceee8eb6ab54d3db47c563a9`
- Remediation commit: `80179977f04fff279d7dbf828ca243a0eb73b0f1`
- Verification date: 2026-10-06
- Environment: local Microsoft Windows development instance
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Chroma distance space: cosine

## Before remediation

The unrelated sourdough query returned three chunks from a document containing
no cooking information. Their cosine distances were approximately 1.009,
1.018 and 1.040. The response did not indicate that the available evidence was
irrelevant.

Raw evidence: `ir-relevance-manipulation-20261006T084653Z.json`.

## Threshold calibration rationale

The threshold was selected from the controlled labelled retrieval evidence,
not from the failing query alone.

- Highest observed distance required for a passing labelled result: about
  0.704, for the second chunk in the chunk-boundary test.
- Closest clearly irrelevant IR-06 result: about 1.009.
- Selected maximum cosine distance: 0.80.

This preserves a margin above the observed relevant group while remaining
below the clearly irrelevant group. It is a project calibration for the
current model and synthetic validation corpus, not a universal semantic rule.

## Implemented control

`VectorStoreService` now converts each returned Chroma distance to a number and
discards the candidate when its cosine distance is greater than the configured
maximum. A result exactly equal to the threshold is retained.

The backend validates and documents the environment setting:

```text
LEARNMATE_MAX_RETRIEVAL_COSINE_DISTANCE=0.8
```

The filter applies in the shared vector-store search path, so document search
and every agent using semantic retrieval receive the same relevance decision.

## Post-remediation retrieval results

IR-01 through IR-07 were repeated against the exact remediation commit.

- IR-01 exact-fact retrieval: Pass
- IR-02 paraphrased semantic retrieval: Pass
- IR-03 acronym retrieval: Pass
- IR-04 chunk-boundary evidence: Pass
- IR-05 page-reference integrity: Pass
- IR-06 irrelevant-query handling: Pass; zero results returned
- IR-07 keyword-stuffing manipulation: Pass; factual page rank 1 and stuffed
  page rank 2
- Hit@1 rate for IR-01 to IR-03: 0.6667
- Hit@3 rate for IR-01 to IR-03: 1.0
- Mean reciprocal rank for IR-01 to IR-03: 0.8333
- All runner uploads cleaned up: Yes

Raw evidence:

- `ir-baseline-20261006T100930Z.json`
- `ir-chunk-provenance-20261006T101002Z.json`
- `ir-relevance-manipulation-20261006T101005Z.json`

## Automated regression result

The complete backend suite was executed from the `backend` directory on the
committed remediation snapshot:

```text
python -m unittest discover -s tests -v
Ran 124 tests in 38.686s
OK
```

The added tests confirm that unrelated evidence above the threshold is removed
and a result exactly at the threshold is retained. Existing Tutor and Quiz
tests also confirm safe behavior when retrieval supplies no evidence.

## Security and reliability conclusion

The demonstrated RET-01 case is mitigated on commit `8017997`: the controlled
irrelevant query now returns an honest empty result set without reducing the
seven-test retrieval pass rate.

Residual relevance risk remains because embedding distances vary by model,
language, document style and OCR quality. The threshold should be monitored and
recalibrated with a larger representative labelled set after model or corpus
changes. Downstream agents must still avoid claiming that retrieved evidence
guarantees correctness.
