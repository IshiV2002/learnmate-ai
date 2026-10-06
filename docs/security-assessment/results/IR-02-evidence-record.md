# IR-02 Evidence Record - Paraphrased Semantic Retrieval

## Test identity

- Test ID: IR-02
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

- Objective: test meaning-based retrieval when the query does not copy the
  source wording.
- Input: `When did the evidence-organizing initiative begin?`
- Preconditions: the controlled four-page PDF was uploaded and indexed.
- Request: authenticated `POST /documents/search` with the test document ID,
  paraphrased query and `top_k=3`.
- Expected: page 1 appears within the first three results.
- Pass criterion: relevant page rank is 1, 2 or 3 and its page reference is
  correct.

## Actual result

- HTTP status: 200
- Ranked pages: 2, 1, 3
- Ranked cosine distances: 0.5830, 0.6760, 0.8831
- Relevant rank: 2
- Returned relevant source: `ir-accuracy.pdf`, page 1, chunk 0
- Relevant text: `The Orion Protocol was launched in 2019.`
- Search latency: 35.78 ms
- Hit@1: No
- Hit@3: Yes
- Reciprocal rank: 0.5
- Outcome: Pass

## Evidence

- Raw log:
  `evidence/raw/ir-baseline-20261005T134856Z.json` under the `IR-02` block
- Source screenshot: reuse `IR-01-01-source-page.png`
- Ranked-response screenshot required: `IR-02-01-ranked-response.png`
- Screenshot status: Pending; capture the result order and both leading
  distances from the sanitized raw log
- Secret review: the evidence contains no password, token or authorization
  header

## Analysis and conclusion

The relevant page appeared at rank 2 and met the predefined Hit@3 criterion.
However, the unrelated LEF page ranked first. This demonstrates reduced ranking
precision for the deliberately vague paraphrase.

This is currently an observation rather than a vulnerability. More paraphrase
queries and a larger controlled corpus are required to determine whether the
behaviour is consistent and whether it can cause unsupported downstream
answers.

## Finding and risk classification

- Confirmed vulnerability: No
- Candidate observation: reduced precision for a vague paraphrased query
- Severity: Not assigned without repeatable impact
- Recommended follow-up: repeat with several paraphrases and test Tutor use of
  the incorrectly top-ranked chunk
- Regression use: preserve the query and monitor rank changes
