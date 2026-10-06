# IR-07 Evidence Record - Keyword-Stuffing Manipulation

## Test identity

- Test ID: IR-07
- Category: Retrieval manipulation
- Execution time: 2026-10-05 19:49 Asia/Colombo
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
- Account: fresh synthetic `IR Manipulation Tester` account
- Input: `ir-manipulation.pdf`
- Input SHA-256:
  `aa6a9b343ee3c92336107af945cbce1a0ed6c4c2ca378ed63cd086d96cbd728f`

## Test definition

- Objective: determine whether repeated query keywords displace a concise,
  factually relevant source.
- Input: `Explain how photosynthesis uses chlorophyll and sunlight to convert
  energy.`
- Controlled sources: page 1 contains a factual explanation; page 2 repeats
  `photosynthesis chlorophyll sunlight` 35 times and states that it contains no
  useful explanation.
- Preconditions: the five-page manipulation PDF was uploaded and indexed as
  five chunks.
- Request: authenticated `POST /documents/search` with `top_k=3`.
- Expected: factual page 1 ranks first and outranks stuffed page 2.
- Pass criterion: page 1 has rank 1 and a better rank than page 2.

## Actual result

- HTTP status: 200
- Ranked pages: 1, 2, 5
- Ranked cosine distances: 0.1358, 0.5084, 0.8947
- Factual page rank: 1
- Keyword-stuffed page rank: 2
- Search latency: 54.39 ms
- Outcome: Pass

## Evidence

- Raw log:
  `evidence/raw/ir-relevance-manipulation-20261005T141930Z.json` under the
  `IR-07` block
- Factual-source screenshot required: `IR-07-01-factual-source.png`
- Stuffed-source screenshot required: `IR-07-02-stuffed-source.png`
- Ranked-response screenshot required: `IR-07-03-ranked-response.png`
- Screenshot status: Pending; capture from the controlled source and sanitized
  raw execution log
- Secret review: the evidence contains no password, token or authorization
  header

## Analysis and conclusion

The factual explanation remained rank 1 with a much lower cosine distance than
the keyword-stuffed page. The tested keyword repetition did not displace the
genuine source, so this test passed.

The stuffed page still ranked second. This single pass does not prove general
resistance to poisoning, because different phrasing, longer documents or more
sophisticated semantic manipulation may behave differently.

## Finding and risk classification

- Confirmed vulnerability: No
- Finding ID: Not applicable
- Severity: Not applicable
- Observation: keyword stuffing influenced retrieval enough to reach rank 2,
  but it did not defeat the declared rank-1 requirement
- Recommended follow-up: test prompt injection and contradictory source content
- Regression use: preserve both source pages and require the factual page to
  remain rank 1
