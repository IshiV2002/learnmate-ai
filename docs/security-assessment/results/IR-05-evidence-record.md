# IR-05 Evidence Record - Page-Reference Integrity

## Test identity

- Test ID: IR-05
- Category: Retrieval provenance and source reliability
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
- Input: `ir-accuracy.pdf`
- Input SHA-256:
  `7d50bd155e43364a6acd9256871264ee3169d38937746113da3e2f6a9250ce5b`

## Test definition

- Objective: verify that retrieved metadata reports the page containing the
  returned text when the same key term has different meanings.
- Probe 1: ask where Mercury is described as the project codename; expected
  page 3.
- Probe 2: ask where Mercury is described as the chemical element; expected
  page 4.
- Preconditions: the controlled four-page PDF was uploaded and indexed as four
  chunks.
- Request: two authenticated `POST /documents/search` requests with `top_k=3`.
- Expected: the matching page is rank 1 for each probe and its returned text
  contains the corresponding meaning.
- Pass criterion: both checked page references are correct at rank 1.

## Actual result

### Project-codename probe

- HTTP status: 200
- Ranked pages: 3, 4, 1
- Ranked cosine distances: 0.2022, 0.4412, 0.7476
- Relevant page rank: 1
- Search latency: 49.24 ms
- Page reference correct: Yes

### Chemical-element probe

- HTTP status: 200
- Ranked pages: 4, 3, 1
- Ranked cosine distances: 0.2075, 0.5373, 0.8381
- Relevant page rank: 1
- Search latency: 50.01 ms
- Page reference correct: Yes

### Combined measurement

- Correct references: 2
- References checked: 2
- Page-reference accuracy: 100%
- Outcome: Pass

## Evidence

- Raw log:
  `evidence/raw/ir-chunk-provenance-20261005T140943Z.json` under the `IR-05`
  block
- Source screenshot required: `IR-05-01-source-pages.png`
- Codename-response screenshot required: `IR-05-02-codename-response.png`
- Element-response screenshot required: `IR-05-03-element-response.png`
- Screenshot status: Pending; capture from the controlled source and sanitized
  raw execution log
- Secret review: the evidence contains no password, token or authorization
  header

## Analysis and conclusion

Both queries ranked the correct meaning and source page first. The page numbers
reported in retrieval metadata matched the controlled PDF. The test passed and
did not demonstrate a provenance vulnerability.

The sample checked two short text pages. It does not prove correct provenance
for complex tables, OCR errors, duplicated chunks or content spanning pages.

## Finding and risk classification

- Confirmed vulnerability: No
- Finding ID: Not applicable
- Severity: Not applicable
- Mitigation: No mitigation is assigned to a passing test
- Regression use: retain both Mercury probes and require 100% page-reference
  accuracy after extraction, chunking or vector-store changes
