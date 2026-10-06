# IR-01 Evidence Record - Exact-Fact Retrieval

## Test identity

- Test ID: IR-01
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

- Objective: determine whether a uniquely worded exact fact is ranked first.
- Input: `In what year was the Orion Protocol launched?`
- Preconditions: the controlled four-page PDF was uploaded successfully and
  indexed as four chunks.
- Request: authenticated `POST /documents/search` with the test document ID,
  exact query and `top_k=3`.
- Expected: page 1 at rank 1.
- Pass criterion: relevant page has rank 1 and the returned page reference
  matches the source.

## Actual result

- HTTP status: 200
- Ranked pages: 1, 3, 2
- Ranked cosine distances: 0.1911, 0.8736, 0.9273
- Relevant rank: 1
- Returned source: `ir-accuracy.pdf`, page 1, chunk 0
- Relevant text: `The Orion Protocol was launched in 2019.`
- Search latency: 31.14 ms
- Hit@1: Yes
- Hit@3: Yes
- Reciprocal rank: 1.0
- Outcome: Pass

## Evidence

- Raw log:
  `evidence/raw/ir-baseline-20261005T134856Z.json` under the `IR-01` block
- Source screenshot required: `IR-01-01-source-page.png`
- Ranked-response screenshot required: `IR-01-02-ranked-response.png`
- Screenshot status: Pending; capture from the source PDF and sanitized raw log
- Secret review: the evidence contains no password, token or authorization
  header

## Analysis and conclusion

The relevant page ranked first, and its distance was substantially lower than
the other returned results. The page reference and returned text matched the
controlled source. This test passed and did not demonstrate a vulnerability.

One test case with a small corpus cannot establish general retrieval accuracy.
The result should be considered alongside paraphrase, manipulation and larger
corpus tests.

## Finding and risk classification

- Confirmed vulnerability: No
- Finding ID: Not applicable
- Severity: Not applicable
- Mitigation: No mitigation is assigned to a passing test
- Regression use: retain this exact query as a future retrieval smoke test
