# IR-03 Evidence Record - Acronym Retrieval

## Test identity

- Test ID: IR-03
- Category: Retrieval accuracy
- Execution time: 2026-10-05 19:18 Asia/Colombo
- Tester: Individual Student 4 assessor
- Git commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`

## Environment

- Operating system: Microsoft Windows NT 10.0.26200.0
- Python: 3.14.7
- FastAPI: 0.141.1
- ChromaDB: 1.5.9
- Sentence Transformers: 5.7.0
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Vector distance: cosine
- Chunk size: 180 words
- Chunk overlap: 30 words
- Search setting: `top_k=3`
- Account: fresh synthetic `IR Baseline Tester` account
- Input: `ir-accuracy.pdf`
- Input SHA-256:
  `7d50bd155e43364a6acd9256871264ee3169d38937746113da3e2f6a9250ce5b`

## Test definition

- Objective: test retrieval when the query uses the source acronym.
- Input: `What three activities are used by LEF?`
- Preconditions: the controlled four-page PDF was uploaded and indexed.
- Request: authenticated `POST /documents/search` with the test document ID,
  acronym query and `top_k=3`.
- Expected: page 2 appears within the first three results.
- Pass criterion: relevant page rank is 1, 2 or 3 and the page reference is
  correct.

## Actual result

- HTTP status: 200
- Ranked pages: 2, 1, 3
- Ranked cosine distances: 0.5271, 0.7715, 0.8518
- Relevant rank: 1
- Returned source: `ir-accuracy.pdf`, page 2, chunk 0
- Relevant text: `The Learning Evidence Framework, abbreviated LEF, uses
  observation, verification, and reflection.`
- Search latency: 28.70 ms
- Hit@1: Yes
- Hit@3: Yes
- Reciprocal rank: 1.0
- Outcome: Pass

## Evidence

- Raw log:
  `evidence/raw/ir-baseline-20261005T134856Z.json` under the `IR-03` block
- Source screenshot required: `IR-03-01-source-page.png`
- Ranked-response screenshot required: `IR-03-02-ranked-response.png`
- Screenshot status: Pending; capture from the source PDF and sanitized raw log
- Secret review: the evidence contains no password, token or authorization
  header

## Analysis and conclusion

The acronym query retrieved the correct page at rank 1. The returned text and
page reference matched the controlled source. This test passed and did not
demonstrate a vulnerability.

The result covers one known acronym only. Other abbreviations and ambiguous
acronyms should not be assumed to behave identically.

## Finding and risk classification

- Confirmed vulnerability: No
- Finding ID: Not applicable
- Severity: Not applicable
- Mitigation: No mitigation is assigned to a passing test
- Regression use: retain the query as an acronym-retrieval smoke test
