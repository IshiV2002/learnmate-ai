# IR-04 Evidence Record - Chunk-Boundary Preservation

## Test identity

- Test ID: IR-04
- Category: Chunking and retrieval reliability
- Execution time: 2026-10-05 19:39 Asia/Colombo
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
- Account: fresh synthetic `IR Provenance Tester` account
- Input: `ir-boundary.pdf`
- Input SHA-256:
  `d7211cfd582a16116302e9b831d3405cf45e6a025ff0d705c122bb0a5da527e6`

## Test definition

- Objective: determine whether the configured overlap preserves evidence near
  a chunk boundary.
- Input: `What are the two paired verification phrases near the chunk boundary?`
- Controlled facts: `amber telescope` and `silver compass`.
- Preconditions: the one-page controlled PDF was uploaded successfully and
  indexed as two chunks.
- Request: authenticated `POST /documents/search` with `top_k=3`.
- Expected: returned adjacent chunks preserve both phrases and report page 1.
- Pass criterion: chunks 0 and 1 are returned, their combined text contains
  both phrases, and every returned page reference equals page 1.

## Actual result

- HTTP status: 200
- Returned chunks: 0 and 1
- Returned pages: 1 and 1
- Ranked cosine distances: 0.6254 and 0.7043
- `amber telescope` present: Yes
- `silver compass` present: Yes
- Adjacent chunks returned: Yes
- Correct page references: Yes
- Search latency: 49.56 ms
- Outcome: Pass

Chunk 0 ended after `amber telescope`. Chunk 1 began within the overlap and
contained both `amber telescope` and `silver compass`, demonstrating that the
30-word overlap retained the boundary context in this controlled case.

## Evidence

- Raw log:
  `evidence/raw/ir-chunk-provenance-20261005T140943Z.json` under the `IR-04`
  block
- Source screenshot required: `IR-04-01-source-boundary.png`
- Upload screenshot required: `IR-04-02-upload-chunks.png`
- Ranked-chunk screenshot required: `IR-04-03-ranked-chunks.png`
- Screenshot status: Pending; capture from the controlled source and sanitized
  raw execution log
- Secret review: the evidence contains no password, token or authorization
  header

## Analysis and conclusion

The overlap preserved the paired evidence across the actual chunk split. Both
chunks retained page 1 provenance, and the query returned them in the first two
positions. The test passed and did not demonstrate a vulnerability.

This result applies to one boundary position and one page. Longer documents,
tables, headings and evidence split across separate pages require additional
testing before making a general reliability claim.

## Finding and risk classification

- Confirmed vulnerability: No
- Finding ID: Not applicable
- Severity: Not applicable
- Mitigation: No mitigation is assigned to a passing test
- Regression use: preserve the corpus and verify both chunk indexes and phrases
  after any chunking change
