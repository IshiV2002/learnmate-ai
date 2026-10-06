# IR-06 Evidence Record - Irrelevant Query Handling

## Test identity

- Test ID: IR-06
- Category: Retrieval reliability and hallucination risk
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
- Input: `ir-accuracy.pdf`
- Input SHA-256:
  `7d50bd155e43364a6acd9256871264ee3169d38937746113da3e2f6a9250ce5b`

## Test definition

- Objective: determine whether the Retrieval Agent returns unrelated evidence
  when no source chunk answers the query.
- Input: `At what temperature and for how long should sourdough bread bake?`
- Ground truth: the four-page controlled PDF contains no cooking, bread,
  temperature or baking information.
- Preconditions: the controlled PDF was uploaded and indexed as four chunks.
- Request: authenticated `POST /documents/search` with `top_k=3`.
- Expected secure behaviour: return no retrieval results or an explicit
  low-evidence result that cannot be mistaken for supporting context.
- Pass criterion: no chunks are returned.

## Actual result

- HTTP status: 200
- Unrelated chunks returned: 3
- Ranked pages: 1, 3, 2
- Ranked cosine distances: 1.0090, 1.0176, 1.0403
- Search latency: 56.96 ms
- Low-relevance warning: None
- Empty/no-evidence signal: None
- Outcome: Fail

The API returned the nearest three chunks even though none contained relevant
evidence. The first result concerned the Orion Protocol, the second concerned a
Mercury project codename, and the third concerned the Learning Evidence
Framework.

## Evidence

- Raw log:
  `evidence/raw/ir-relevance-manipulation-20261005T141930Z.json` under the
  `IR-06` block
- Source screenshot required: `IR-06-01-unrelated-source.png`
- Result screenshot required: `IR-06-02-irrelevant-results.png`
- Root-cause code screenshot required: `IR-06-03-no-threshold-code.png`
- Screenshot status: Pending; capture from the controlled source, sanitized log
  and the narrow vector-store code section
- Secret review: the evidence contains no password, token or authorization
  header

## Analysis and conclusion

The test demonstrates that document-scoped nearest-neighbour search does not
apply a semantic relevance threshold. ChromaDB is asked for `top_k` results and
the service returns those results without rejecting high-distance matches.

This creates a retrieval-integrity weakness: unrelated chunks can be presented
to downstream agents as grounding material. It does not yet prove that Tutor or
Quiz will make a false claim, so downstream impact must be tested separately.

## Finding and risk classification

- Confirmed finding: RET-01 - Missing semantic relevance threshold
- Confidentiality impact: none demonstrated
- Integrity impact: unrelated evidence can be treated as relevant context
- Availability impact: none demonstrated
- Impact score: 2/5; retrieval is incorrect, but downstream misinformation has
  not yet been demonstrated
- Likelihood score: 4/5; any authenticated user can submit an unrelated query,
  and the behaviour reproduced in the controlled test
- Risk score: 8/25
- Preliminary severity: Medium
- Final severity status: pending downstream Tutor/Quiz impact testing

## Recommended mitigation

- Calibrate a maximum acceptable cosine distance using a labelled validation
  corpus.
- Return an empty result when every candidate exceeds the threshold.
- Require downstream agents to produce a no-evidence response when retrieval is
  empty.
- Preserve page/source transparency and avoid claiming retrieval guarantees
  correctness.
- Re-run IR-06 as the regression test after mitigation.
