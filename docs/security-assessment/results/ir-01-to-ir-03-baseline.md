# IR-01 to IR-03 Retrieval Baseline Results

## Execution record

- Execution time: 2026-10-05 19:18 Asia/Colombo
- Tested commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- API: `http://127.0.0.1:8000`
- Input: `ir-accuracy.pdf`
- Input SHA-256:
  `7d50bd155e43364a6acd9256871264ee3169d38937746113da3e2f6a9250ce5b`
- Uploaded pages: 4
- Indexed chunks: 4
- Search setting: `top_k=3`
- Distance metric: cosine distance; lower values indicate closer matches
- Authentication: fresh synthetic account and bearer token
- Secret handling: the temporary password and bearer token were not recorded

The upload returned `201 Created`. Cleanup returned `200 OK` after the three
tests, confirming that the test document deletion request completed.

## IR-01 - Exact-fact retrieval

- Query: `In what year was the Orion Protocol launched?`
- Expected: page 1 at rank 1
- Ranked pages: 1, 3, 2
- First-result distance: 0.1911
- Relevant rank: 1
- Latency: 31.14 ms
- Hit@1: Yes
- Hit@3: Yes
- Reciprocal rank: 1.0
- Outcome: Pass

The exact factual query returned the correct page first with a substantially
lower distance than the other returned pages.

## IR-02 - Paraphrased semantic retrieval

- Query: `When did the evidence-organizing initiative begin?`
- Expected: page 1 within the first three results
- Ranked pages: 2, 1, 3
- Ranked distances: 0.5830, 0.6760, 0.8831
- Relevant rank: 2
- Latency: 35.78 ms
- Hit@1: No
- Hit@3: Yes
- Reciprocal rank: 0.5
- Outcome: Pass

The relevant page was retrieved at rank 2 and therefore met the predefined
Hit@3 requirement. The unrelated page 2 result ranked first, showing that vague
paraphrasing can reduce ranking precision. This is an observation for further
testing, not a confirmed vulnerability.

## IR-03 - Acronym retrieval

- Query: `What three activities are used by LEF?`
- Expected: page 2 within the first three results
- Ranked pages: 2, 1, 3
- First-result distance: 0.5271
- Relevant rank: 1
- Latency: 28.70 ms
- Hit@1: Yes
- Hit@3: Yes
- Reciprocal rank: 1.0
- Outcome: Pass

The acronym and activity wording retrieved the correct Learning Evidence
Framework page at rank 1.

## Aggregate results

- Tests executed: 3
- Tests passed: 3
- Hit@1 rate: 66.67%
- Hit@3 rate: 100%
- Mean Reciprocal Rank: 0.8333
- Cross-document leakage observed: 0 (only one document was in scope)

## Current conclusion

The controlled baseline demonstrates successful exact-fact, paraphrased and
acronym retrieval under the declared Hit@1/Hit@3 criteria. IR-02 indicates a
ranking-quality limitation that should be retested with more paraphrases and a
larger corpus before it is treated as a finding.

This run is a small controlled experiment. It does not by itself establish
production retrieval accuracy, resistance to manipulation, or the absence of
security vulnerabilities.

## Raw evidence

The sanitized raw JSON log is stored locally at:

`docs/security-assessment/evidence/raw/ir-baseline-20261005T134856Z.json`

The raw evidence directory is intentionally ignored by Git. It contains no
password or bearer token.
