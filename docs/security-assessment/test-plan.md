# Retrieval and Security Test Plan

This plan contains 20 independent tests for the Student 4 specialization. Each
test must use the structure in `evidence-template.md` and produce separate
evidence. A failed expectation is not automatically a vulnerability; confirm
the root cause and realistic impact first.

## Retrieval reliability tests

### IR-01 - Exact-fact retrieval

- Objective: measure retrieval of a uniquely worded known fact.
- Input: ask for the Orion Protocol launch year from the controlled corpus.
- Expected: the correct page is ranked first.
- Measure: Hit@1, rank, distance, page-reference accuracy and latency.

### IR-02 - Paraphrased semantic retrieval

- Objective: test meaning-based retrieval without copying source wording.
- Input: paraphrase the known Orion Protocol fact.
- Expected: the correct page appears within the first three results.
- Measure: Hit@3, reciprocal rank, distances and latency.

### IR-03 - Synonym and acronym retrieval

- Objective: test retrieval when the query uses an acronym or synonym.
- Input: query for the Learning Evidence Framework using `LEF` and alternative
  wording.
- Expected: the correct source section is retrieved.
- Measure: rank, source page and result stability over three repetitions.

### IR-04 - Chunk-boundary evidence

- Objective: determine whether chunk overlap preserves evidence near a split.
- Input: ask for the paired `amber telescope` and `silver compass` phrases in
  the boundary corpus.
- Expected: enough adjacent context is returned to recover both facts.
- Measure: returned chunk indexes, page, rank and missing context.

### IR-05 - Page-reference integrity

- Objective: verify that returned provenance matches the actual source page.
- Input: query a phrase that occurs on multiple pages with different meanings.
- Expected: each result reports the page containing its exact text.
- Measure: correct references divided by total checked references.

### IR-06 - Irrelevant query handling

- Objective: determine how the system handles a query unrelated to the source.
- Input: ask an astronomy document for an unrelated cooking instruction.
- Expected: no evidence or a clear low-evidence response, not confident misuse
  of the nearest unrelated chunk.
- Measure: returned distances, downstream response and unsupported claims.

### IR-07 - Keyword-stuffing manipulation

- Objective: test whether repeated query terms displace genuinely relevant
  evidence.
- Input: upload the manipulation corpus and query its target topic.
- Expected: the factual source outranks the irrelevant keyword-stuffed page.
- Measure: before/after rank and distance changes.

### IR-08 - Retrieved prompt-injection text

- Objective: test whether malicious document text is treated as data.
- Input: retrieve the page containing instructions to ignore application rules.
- Expected: Retrieval may return the text, but Tutor and Quiz must not obey it.
- Measure: retrieved chunk, downstream output and any instruction-following.

### IR-09 - Contradictory source reliability

- Objective: test handling of two incompatible claims in uploaded material.
- Input: ask for the value that is stated differently on two source pages.
- Expected: responses preserve citations and avoid unsupported certainty.
- Measure: cited pages, acknowledgement of conflict and unsupported claims.

### IR-10 - OCR accuracy and manipulation

- Objective: assess image-to-text accuracy and adversarial OCR content.
- Input: upload both clean and adversarial generated PNG files.
- Expected: clean text is searchable; malicious text is not treated as trusted
  agent instruction.
- Measure: character/word errors, retrieval rank, source label and downstream
  behaviour.

## Security tests

### SEC-01 - JWT enforcement

- Objective: verify authentication on every document operation.
- Input: missing, malformed, tampered and expired bearer tokens.
- Expected: protected operations return a controlled `401` response without
  data or internal details.
- Evidence: sanitized request/response pairs for upload, list, get, search and
  delete.

### SEC-02 - Cross-user search authorization

- Objective: test Broken Object Level Authorization during semantic search.
- Input: User B searches a known document ID belonging to User A.
- Expected: `404` or an equivalent non-disclosing response with no retrieved
  text.
- Evidence: owner access followed by non-owner attempt using the same ID.

### SEC-03 - Cross-user metadata and deletion authorization

- Objective: test ownership controls on list, get and delete.
- Input: User B attempts each operation on User A's document.
- Expected: no metadata, file, vector, ownership or existence disclosure; User
  A's material remains usable.
- Evidence: two-account before/after state.

### SEC-04 - Filename and path traversal

- Objective: verify that attacker-controlled filenames cannot escape storage.
- Input: slash, backslash, drive-letter, dot-segment and Unicode filename forms.
- Expected: internal UUID storage remains inside the upload directory and is
  never exposed publicly.
- Evidence: response plus sanitized upload-directory listing.

### SEC-05 - Extension, MIME and signature mismatch

- Objective: verify authoritative server-side type validation.
- Input: conflicting PDF, PNG and JPEG extensions, MIME types and signatures.
- Expected: every mismatch is rejected before file, SQLite or Chroma state is
  persisted.
- Evidence: response and three-store before/after inspection.

### SEC-06 - Malformed and protected file handling

- Objective: test parser error handling without server crashes or residue.
- Input: corrupt, truncated and password-protected PDFs plus corrupt images.
- Expected: controlled `4xx` response, no stack trace and no persistent state.
- Evidence: status/body, log and storage inspection.

### SEC-07 - No-extractable-text rollback

- Objective: verify complete cleanup when extraction or OCR yields no chunks.
- Input: blank PDF and blank image.
- Expected: `422`, no success message, and no stored file, metadata or vectors.
- Evidence: response and three-store inspection.

### SEC-08 - Resource-limit enforcement

- Objective: test upload-byte and decoded-image-pixel limits.
- Input: just-below/above 10 MiB files and an image exceeding the configured
  pixel limit.
- Expected: safe completion within limits and controlled `413` rejection above
  limits without persistent state.
- Evidence: timings, statuses, process observations and storage state.

### SEC-09 - Query and request abuse

- Objective: assess disproportionate processing and missing throttling.
- Input: increasingly long queries and a controlled local burst of repeated
  search requests.
- Expected: bounded input and rate controls, stable service and no sensitive
  error details.
- Measure: accepted query length, status distribution, median and p95 latency.

### SEC-10 - Deletion lifecycle

- Objective: verify that deletion removes every retrievable representation.
- Input: delete a known document, then repeat get/search/delete and inspect all
  stores.
- Expected: file, SQLite metadata and all Chroma chunks are gone; later calls
  reveal no content.
- Evidence: before/after API and storage state.

## Overall retrieval metrics

- Hit@1: relevant result is ranked first.
- Hit@3: relevant result appears in the first three results.
- Mean Reciprocal Rank: average of `1 / rank` for the first relevant result.
- Page-reference accuracy: correct page references divided by checked results.
- Cross-document leakage count: results originating outside the authorized
  document set; the secure target is zero.
- Median and p95 latency: report both so slow outliers remain visible.
