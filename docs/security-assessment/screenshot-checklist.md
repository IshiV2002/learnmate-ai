# Screenshot Checklist

Capture evidence during each test whenever possible. Raw logs preserve exact
data, but screenshots help the examiner understand the result quickly.

## Shared screenshots captured once per testing session

1. `ENV-01-tested-commit-and-versions.png`
   - Show the Git commit, Python, FastAPI, ChromaDB and Sentence Transformers
     versions.
   - Do not show unrelated terminal history or personal directories.
2. `ENV-02-backend-health.png`
   - Show `GET /health`, its `200` status and the response body.
3. `IR-BASELINE-01-upload-result.png`
   - Show the `201` upload response, original filename, page count and chunk
     count.
   - Do not show an authorization token.

## IR-01

1. `IR-01-01-source-page.png`
   - Show page 1 of `ir-accuracy.pdf` containing the 2019 answer.
2. `IR-01-02-ranked-response.png`
   - Show the query, `200` status, page 1 at rank 1 and its distance.

## IR-02

1. Reuse `IR-01-01-source-page.png` and cite it clearly.
2. `IR-02-01-ranked-response.png`
   - Show the paraphrased query and the result order: page 2 first, relevant
     page 1 second.
   - Include both distances because they support the ranking observation.

## IR-03

1. `IR-03-01-source-page.png`
   - Show page 2 with the LEF acronym and its three activities.
2. `IR-03-02-ranked-response.png`
   - Show the acronym query, `200` status and page 2 at rank 1.

## IR-04

1. `IR-04-01-source-boundary.png`
   - Show the section of `ir-boundary.pdf` containing `amber telescope` and
     `silver compass`.
2. `IR-04-02-upload-chunks.png`
   - Show that the one-page source was indexed as two chunks.
3. `IR-04-03-ranked-chunks.png`
   - Show returned chunks 0 and 1, their page 1 references, both phrases and
     distances.

## IR-05

1. `IR-05-01-source-pages.png`
   - Show page 3's project-codename meaning and page 4's chemical-element
     meaning. Two clearly labelled screenshots are acceptable if one image is
     unreadable.
2. `IR-05-02-codename-response.png`
   - Show the codename query with page 3 ranked first.
3. `IR-05-03-element-response.png`
   - Show the chemical-element query with page 4 ranked first.

## IR-06

1. `IR-06-01-unrelated-source.png`
   - Show the controlled PDF contents or page thumbnails demonstrating that it
     contains no cooking or bread information.
2. `IR-06-02-irrelevant-results.png`
   - Show the cooking query, `200` status, three unrelated returned chunks and
     their distances above 1.0.
3. `IR-06-03-no-threshold-code.png`
   - Show the narrow `collection.query` and result-building section in
     `vector_store_service.py` where results are returned without a relevance
     threshold. Include line numbers but no unrelated code.

## IR-07

1. `IR-07-01-factual-source.png`
   - Show page 1's concise photosynthesis explanation.
2. `IR-07-02-stuffed-source.png`
   - Show page 2's repeated keywords and statement that it has no useful
     explanation.
3. `IR-07-03-ranked-response.png`
   - Show page 1 at rank 1, page 2 at rank 2 and both distances.

## IR-08

1. `IR-08-01-malicious-source.png`
   - Show page 3's embedded instruction and synthetic verification token.
2. `IR-08-02-retrieved-citation.png`
   - Show page 3 retrieved with its source, chunk and distance.
3. `IR-08-03-tutor-reply.png`
   - Show the fallback Tutor presenting the instruction as a `Core Definition`
     and the absence of an explicit safety rejection.
4. `IR-08-04-fallback-code.png`
   - Show the narrow fallback section that inserts the first retrieved chunk
     into the reply. Include line numbers.

## IR-09

1. `IR-09-01-conflicting-pages.png`
   - Show pages 4 and 5 with the 30-credit and 45-credit claims.
2. `IR-09-02-both-citations.png`
   - Show that both pages were present in the retrieved citations.
3. `IR-09-03-incomplete-reply.png`
   - Show that the reply stated only 30 credits and did not compare it with the
     45-credit claim.
4. `IR-09-04-first-chunk-code.png`
   - Show the fallback code selecting `lecture_chunks[0]` rather than analysing
     all retrieved evidence.

## IR-10

1. `IR-10-01-clean-source.png`
   - Show the complete controlled image containing `sapphire compass`.
2. `IR-10-02-clean-result.png`
   - Show rank 1, source page 1, character error rate 0 and word error rate 0.
3. `IR-10-03-adversarial-source.png`
   - Show the visible instruction-like text in the controlled image.
4. `IR-10-04-adversarial-retrieval.png`
   - Show the instruction-like text retrieved at rank 1 with correct source and
     page provenance.
5. `IR-10-05-tutor-reply.png`
   - Show the fallback presenting the OCR text as a `Core Definition`.
6. `IR-10-06-fallback-code.png`
   - Show the narrow fallback code that copies the first retrieved chunk into
     the response template.

## SEC-01

1. `SEC-01-01-missing-token.png`
   - Show representative missing-token cases returning the generic 401 and
     Bearer challenge.
2. `SEC-01-02-malformed-token.png`
   - Show representative malformed-token cases returning the same response.
3. `SEC-01-03-tampered-token.png`
   - Show the sanitized tampered-signature cases. Never show the JWT value.
4. `SEC-01-04-expired-token.png`
   - Show the sanitized expired-token cases. Never show the signing secret.
5. `SEC-01-05-state-preserved.png`
   - Show `owner_document_still_present`, `owner_search_still_works`, cleanup
     success and the overall Pass result.
6. `SEC-01-06-authentication-code.png`
   - Show the narrow shared dependency, generic 401 response, Bearer challenge,
     signature verification and required `sub`, `iat` and `exp` claims.

## SEC-02

1. `SEC-02-01-private-source.png`
   - Show the controlled User A PDF containing `violet lighthouse 731`.
2. `SEC-02-02-owner-search.png`
   - Show User A's successful 200 search and the unique phrase in the result.
3. `SEC-02-03-user-b-list.png`
   - Show User B's 200 document list without User A's document.
4. `SEC-02-04-cross-user-denial.png`
   - Show the five User B attempts against User A's known ID returning the
     generic 404 with no private phrase.
5. `SEC-02-05-nonexistent-control.png`
   - Show the nonexistent-ID control returning the same status and body.
6. `SEC-02-06-summary-cleanup.png`
   - Show zero leakage, preserved owner access, overall Pass and successful
     cleanup.
7. `SEC-02-07-ownership-code.png`
   - Show the narrow search endpoint section that passes both document ID and
     authenticated user ID to the metadata lookup before retrieval.

## SEC-03

1. `SEC-03-01-private-source.png`
   - Reuse or recapture the controlled User A PDF containing the unique phrase.
2. `SEC-03-02-owner-before.png`
   - Show User A's metadata 200 and the three positive storage checks.
3. `SEC-03-03-user-b-list.png`
   - Show User B's list without User A's document.
4. `SEC-03-04-get-denial-control.png`
   - Show User B's get request and the nonexistent-ID control returning the
     identical generic 404.
5. `SEC-03-05-delete-denial-control.png`
   - Show User B's delete request and the nonexistent-ID control returning the
     identical generic 404.
6. `SEC-03-06-owner-state-preserved.png`
   - Show User A's metadata and semantic search still working, with metadata,
     stored file and file-hash checks all true.
7. `SEC-03-07-summary-cleanup.png`
   - Show zero leakage, overall Pass, metadata/file removal after authorized
     cleanup and cleanup success.
8. `SEC-03-08-ownership-code.png`
   - Show the narrow get/delete sections that query using both document ID and
     authenticated user ID before returning metadata or deleting state.

## SEC-04

1. `SEC-04-01-filename-cases.png`
   - Show the POSIX, Windows, drive, absolute and mixed-separator cases with
     sanitized display names, containment checks and Pass outcomes.
2. `SEC-04-02-unicode-case.png`
   - Show the Unicode path input becoming `lecture-安全.pdf` while storage stays
     contained and UUID-named.
3. `SEC-04-03-sanitized-library.png`
   - Show the six expected safe display names in the synthetic user's library.
4. `SEC-04-04-summary.png`
   - Show 6/6 passed, all containment/name/hash checks true and no internal
     filename exposure.
5. `SEC-04-05-cleanup.png`
   - Show all test files removed and the upload directory returned to its
     three-file baseline.
6. `SEC-04-06-sanitization-code.png`
   - Show backslash normalization and final-name extraction.
7. `SEC-04-07-storage-code.png`
   - Show UUID filename generation, path resolution and parent containment.
8. `SEC-04-08-public-response-code.png`
   - Show `stored_filename` and `user_id` removed from public serialization.

## SEC-05

1. `SEC-05-01-mime-mismatches.png`
   - Show PDF, PNG and JPEG extensions rejected with incorrect MIME types and
     all three persistence-state checks remaining true.
2. `SEC-05-02-signature-mismatches.png`
   - Show the PDF, PNG and JPEG signature mismatch cases returning controlled
     400 responses with no state changes.
3. `SEC-05-03-unsupported-types.png`
   - Show `.txt`, `.exe` and generic binary MIME cases being rejected.
4. `SEC-05-04-baseline-state.png`
   - Show upload count 3, user document count 0 and Chroma count 55.
5. `SEC-05-05-valid-control.png`
   - Show the uppercase PDF accepted with 201 and all three persistence counts
     increasing.
6. `SEC-05-06-summary.png`
   - Show 9/9 rejection cases passed, three stores preserved and valid control
     passed.
7. `SEC-05-07-cleanup.png`
   - Show all three stores returned exactly to baseline.
8. `SEC-05-08-validation-code.png`
   - Show extension/MIME mapping and signature checks.
9. `SEC-05-09-validation-order.png`
   - Show validation calls occurring before safe storage-path creation.

## SEC-06

1. `SEC-06-01-corrupt-pdf-failure.png`
   - Show the corrected raw-log corrupt-PDF block: 500 response, one new orphan,
     unchanged SQLite/Chroma state and healthy service.
2. `SEC-06-02-truncated-pdf-failure.png`
   - Show the truncated-PDF block with the same controlled state fields and
     distinct input hash.
3. `SEC-06-03-protected-and-image-rejections.png`
   - Show the protected PDF, corrupt PNG and corrupt JPEG returning controlled
     400 responses with no new orphan or persistence change.
4. `SEC-06-04-valid-control.png`
   - Show the valid post-malformed PDF returning 201 with four pages and four
     chunks.
5. `SEC-06-05-summary.png`
   - Show 5 cases, 3 passed, 2 failed, no client-side internal-detail exposure,
     service health preserved and valid-control success.
6. `SEC-06-06-orphan-state.png`
   - Show the post-cleanup block recording two orphan PDFs, upload count 5,
     SQLite count 0 and Chroma count 55.
7. `SEC-06-07-sanitized-server-error.png`
   - Show the sanitized server excerpt linking PyMuPDF rejection to Windows
     `PermissionError [WinError 32]`. Do not show personal paths or internal
     generated filenames.
8. `SEC-06-08-cleanup-handler-code.png`
   - Show the narrow `PDFExtractionError` handler and unprotected `unlink` call
     in `documents.py`, with line numbers.
9. `SEC-06-09-pdf-resource-code.png`
   - Show the narrow `with pymupdf.open(...)` and exception-conversion section
     in `pdf_service.py`.

## SEC-07

1. `SEC-07-01-blank-pdf.png`
   - Show the blank-PDF block returning 422, zero new orphan files, unchanged
     SQLite/Chroma state, healthy service and Pass.
2. `SEC-07-02-blank-image.png`
   - Show the blank-image block returning 422 with the clear no-readable-text
     message and all three persistence checks unchanged.
3. `SEC-07-03-baseline.png`
   - Show upload count 3, synthetic-user document count 0 and Chroma count 55.
4. `SEC-07-04-valid-control.png`
   - Show the post-rejection valid PDF returning 201 with four pages and four
     chunks.
5. `SEC-07-05-summary.png`
   - Show 2/2 cases passed, controlled 422 responses, state preservation,
     healthy service and overall Pass.
6. `SEC-07-06-cleanup.png`
   - Show all three final counts matching the baseline and cleanup success.
7. `SEC-07-07-rollback-code.png`
   - Show the narrow zero-chunk handler in `documents.py`: stored-file cleanup,
     422 status and separate PDF/image messages.

## SEC-08

1. `SEC-08-01-byte-limit-rejection.png`
   - Show the 10,485,761-byte case returning 413 with all persistence checks
     unchanged and the service healthy.
2. `SEC-08-02-pixel-limit-rejection.png`
   - Show the 25,005,000-pixel image returning 413 despite its small compressed
     file size.
3. `SEC-08-03-below-limit-accepted.png`
   - Show the 10,485,759-byte PDF returning 201 with upload, SQLite and Chroma
     state increasing as expected.
4. `SEC-08-04-summary.png`
   - Show 3/3 cases passed and the overall Pass outcome.
5. `SEC-08-05-cleanup.png`
   - Show upload count 3, user document count 0, Chroma count 55 and exact
     baseline restoration.
6. `SEC-08-06-limit-code.png`
   - Show the one-byte-beyond upload read, byte-size rejection and decoded-pixel
     comparison with line numbers.

## SEC-09

1. `SEC-09-01-query-lengths.png`
   - Show all four tested lengths returning 200 and their recorded latencies.
2. `SEC-09-02-maximum-accepted.png`
   - Show the 32,768-character case accepted with 200. Do not expose the full
     long query; show only its length and SHA-256.
3. `SEC-09-03-burst-statuses.png`
   - Show the bounded 12-request/four-worker setup and representative 200
     statuses.
4. `SEC-09-04-summary.png`
   - Show maximum accepted length, 12/12 status distribution, no observed rate
     limit, median/p95 latency, healthy service and Fail outcome.
5. `SEC-09-05-cleanup.png`
   - Show storage returned to upload count 3, user documents 0 and Chroma 55.
6. `SEC-09-06-query-schema.png`
   - Show `query: str` and the blank-only validator without a maximum length.
7. `SEC-09-07-middleware.png`
   - Show the narrow FastAPI middleware setup without a rate-limit control.

## SEC-10

1. `SEC-10-01-representations-before.png`
   - Show metadata/search success, matching stored-file hash and four Chroma
     chunks before deletion.
2. `SEC-10-02-authorized-delete.png`
   - Show the authorized 200 deletion response.
3. `SEC-10-03-post-delete-responses.png`
   - Show get, search and repeated delete returning the same generic 404 as
     nonexistent-ID controls.
4. `SEC-10-04-storage-removal.png`
   - Show SQLite metadata absent, stored file absent, Chroma chunk count zero
     and deleted document absent from the library.
5. `SEC-10-05-summary.png`
   - Show all lifecycle conditions true and overall Pass.
6. `SEC-10-06-cleanup.png`
   - Show upload count 3, user documents 0, Chroma 55 and exact baseline
     restoration.
7. `SEC-10-07-delete-order-code.png`
   - Show the narrow delete endpoint removing Chroma, file and then SQLite, with
     line numbers.

## How to capture the tests already completed

The live test document was correctly deleted after execution, so do not pretend
that a later API response came from the original run. Open the sanitized raw
JSON log and capture the relevant test block instead. Caption it as
"sanitized execution log" rather than "live Swagger response".

For later tests, capture the API response before cleanup and retain the raw log.
Both are useful: the screenshot is readable evidence and the JSON is the exact
machine-readable record.

## Screenshot safety

- Hide or crop bearer tokens, passwords, API keys and JWT secrets.
- Avoid real email addresses and personal data; use synthetic account labels.
- Keep the endpoint, query, HTTP status, important response fields and test ID
  visible.
- Give every image a numbered caption explaining what it proves.
- Do not edit response values. Cropping and secret redaction are acceptable,
  but state that the screenshot was redacted.
