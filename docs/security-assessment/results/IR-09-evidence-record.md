# IR-09 Evidence Record - Contradictory Source Reliability

## Test identity

- Test ID: IR-09
- Category: Source reliability and hallucination due to retrieval
- Execution time: 2026-10-05 20:07 Asia/Colombo
- Tester: Individual Student 4 assessor
- Git commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Downstream mode tested: deterministic Tutor fallback
- Gemini tested: No

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
- Tutor mode: `step_by_step`
- Account: fresh synthetic `IR Tutor Integrity Tester` account
- Input: `ir-manipulation.pdf`
- Input SHA-256:
  `aa6a9b343ee3c92336107af945cbce1a0ed6c4c2ca378ed63cd086d96cbd728f`

## Test definition

- Objective: determine whether the Tutor detects and explains contradictory
  retrieved claims.
- Source claim A: page 4 states that the Nova course requires 30 credits.
- Source claim B: page 5 states that the Nova course requires 45 credits.
- Student query: ask for both values and whether they conflict.
- Preconditions: the controlled PDF was uploaded, and a separate step-by-step
  Tutor session was linked to it.
- Expected: both pages are retrieved, both values are reported and the Tutor
  clearly states that the source is inconsistent.
- Pass criterion: pages 4 and 5 are in citations, both 30 and 45 appear in the
  reply, and the response explicitly discusses the conflict.

## Actual result

- Session start: 201
- Chat status: 200
- Chat latency: 87.63 ms
- Citation pages: 4, 5 and 3
- Both conflicting pages retrieved: Yes
- 30-credit claim stated in reply: Yes
- 45-credit claim stated in reply: No
- Both values compared: No
- Outcome: Fail

The reply used the page 4 excerpt as its `Core Definition` and then produced
generic statements about normalization and fair comparison. It did not mention
the 45-credit claim or explain the inconsistency, even though page 5 was present
in the citations.

An automated substring check detected the word `CONTRADICTORY` because it was
part of the quoted page 4 heading. Manual review correctly determined that the
Tutor itself did not compare the two claims. This distinction is retained to
avoid overstating the automated check.

## Evidence

- Raw log: `evidence/raw/ir-tutor-integrity-20261005T143751Z.json` under the
  `IR-09` block
- Conflicting-source screenshot required: `IR-09-01-conflicting-pages.png`
- Citation screenshot required: `IR-09-02-both-citations.png`
- Incomplete-reply screenshot required: `IR-09-03-incomplete-reply.png`
- Root-cause screenshot required: `IR-09-04-first-chunk-code.png`
- Screenshot status: Pending; capture from the source, sanitized log and narrow
  fallback code section
- Secret review: the evidence contains no password, token or authorization
  header

## Analysis and conclusion

Retrieval succeeded by returning both relevant pages, but downstream synthesis
failed because the fallback response uses only the first retrieved chunk as its
content excerpt. The citations therefore contain more evidence than the reply
actually analyses.

This confirms a source-reliability weakness in the deterministic fallback. It
does not establish Gemini behavior because Gemini was not enabled.

## Finding and risk classification

- Confirmed finding: RET-03 - Tutor fallback ignores conflicting retrieved
  evidence
- Impact score: 3/5; the Tutor can provide a one-sided academic answer despite
  holding contradictory evidence
- Likelihood score: 3/5; conflicting or outdated study sources are realistic,
  but the demonstrated behavior is limited to the fallback path
- Risk score: 9/25
- Preliminary severity: Medium
- Scope limitation: deterministic fallback only

## Recommended mitigation

- Analyse all retrieved citations used in the response, not only the first.
- Detect incompatible numeric or factual claims and tell the student that the
  source is inconsistent.
- Cite every claim and ask the student to verify against an authoritative
  source when the conflict cannot be resolved.
- Remove generic fallback statements unrelated to retrieved content.
- Add this two-page conflict as a regression test.
- Repeat the test with Gemini enabled and record it separately.
