# RET-01 - Missing Semantic Relevance Threshold

## Status

- Evidence status: Confirmed at the Retrieval API boundary
- Downstream status: no-evidence Tutor/Quiz behavior covered by automated tests;
  final end-to-end reassessment pending
- Related test: IR-06
- Affected commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Reconfirmed commit: `bec9feb60d8dd643ceee8eb6ab54d3db47c563a9`
- Mitigation status: Implemented and verified on the controlled validation set
- Remediation commit: `80179977f04fff279d7dbf828ca243a0eb73b0f1`

The Medium 8/25 rating is retained as the original pre-fix risk assessment.
The threshold reduces the demonstrated failure mode but does not guarantee
that every future relevant and irrelevant query will be perfectly separated.

## Description

The semantic search pipeline always returns the nearest available chunks up to
`top_k`, even when every chunk is unrelated to the query. The API provides no
minimum similarity requirement and no low-confidence indicator.

## Reproduction summary

The controlled PDF contained only facts about the Orion Protocol, LEF and two
meanings of Mercury. A query asking how to bake sourdough bread returned three
chunks from that PDF with cosine distances between 1.0090 and 1.0403.

No chunk contained cooking information, but the response was `200 OK` and did
not indicate that the evidence was irrelevant.

## Technical root cause

`VectorStoreService.search_documents` calls the ChromaDB collection with
`n_results=top_k`, then converts every returned document, metadata item and
distance into a public result. There is no calibrated distance threshold or
empty-on-low-confidence decision before the results reach API consumers.

Document-ID filtering correctly limits the search scope, but it does not solve
semantic irrelevance within that scope.

## Impact

- Unrelated content can be presented to Tutor or Quiz as grounding evidence.
- Page references can make irrelevant evidence appear trustworthy.
- Students may receive unsupported explanations if downstream agents do not
  reject the weak context.
- No confidentiality or availability impact was demonstrated by IR-06.

## Risk assessment

- Impact: 2/5 - incorrect evidence retrieval is confirmed, but downstream
  misinformation is not yet demonstrated.
- Likelihood: 4/5 - any authenticated user can enter an unrelated query, and
  the controlled test reproduced the behaviour.
- Risk score: 8/25.
- Preliminary severity: Medium.
- Reassessment trigger: test whether Tutor or Quiz uses these unrelated chunks
  to make unsupported claims.

## Recommended mitigation

1. Build a labelled validation set containing relevant and irrelevant queries.
2. Calibrate a maximum cosine-distance threshold for the selected embedding
   model and content domain.
3. Discard candidates exceeding the threshold.
4. Return an explicit empty/no-evidence state to callers.
5. Require Tutor and Quiz to respond safely when no evidence is available.
6. Log threshold decisions without recording sensitive query content.
7. Re-run IR-06 and downstream hallucination tests after implementation.

## Implemented mitigation and verification

The Chroma collection uses cosine distance, where lower values are closer. The
controlled labelled evidence showed a highest required relevant distance of
approximately 0.704 and a closest clearly irrelevant IR-06 distance of
approximately 1.009. A configurable maximum distance of 0.80 was selected
between those observed groups.

Search results above the threshold are now discarded before reaching the
document API, Tutor, Quiz or Recommendation consumers. The setting is exposed
as `LEARNMATE_MAX_RETRIEVAL_COSINE_DISTANCE` and validated to remain within the
cosine-distance range.

Automated tests cover an unrelated result above the threshold, retention at
the exact threshold, and safe Tutor/Quiz behavior when no evidence remains. A
post-fix run passed IR-01 through IR-07: IR-06 returned zero results, IR-07 kept
the factual page above the stuffed page, and the original baseline retained a
Hit@3 rate of 1.0 and MRR of 0.8333. The complete backend suite passed 124
tests.

See `results/RET-01-remediation-verification.md` for the full evidence record.

## Residual risk

No single threshold perfectly separates relevant and irrelevant text. The
threshold must be evaluated for false positives and false negatives, monitored
after model changes, and combined with transparent citations and downstream
uncertainty handling.

The current calibration set is intentionally small and synthetic. More varied
course subjects, short queries, multilingual material and OCR noise should be
added before claiming that 0.80 generalizes to production use.
