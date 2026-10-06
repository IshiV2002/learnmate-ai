# LearnMate AI Retrieval and Security Assessment

This folder supports the Student 4 individual assignment specialization:
**Information Retrieval and Security Assessment**.

The assessment evaluates the existing system. It does not assume that a
suspected weakness is a confirmed vulnerability until a repeatable test
produces evidence.

## Frozen baseline

- Branch: `feature/retrieval-agent`
- Shared baseline commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Target: 20 independent test cases (the brief requires at least 15)
- Primary components: upload, extraction/OCR, chunking, embeddings, ChromaDB,
  SQLite ownership checks, document APIs, and Retrieval Agent consumers

If the code changes before testing, record the new commit hash in every test
result. Results from different commits must not be presented as one unchanged
experiment.

## Ethical testing boundary

- Test only the local LearnMate AI instance and synthetic accounts/documents.
- Do not attack public services or other users.
- Do not include real API keys, passwords, JWTs, personal data, or full local
  paths in evidence.
- Redact authorization tokens from screenshots and logs.
- Keep failed tests separate from confirmed vulnerabilities.

## Folder contents

- `test-plan.md`: the 20 planned retrieval and security tests.
- `evidence-template.md`: the required recording format for each executed test.
- `tools/generate_test_corpus.py`: creates reproducible synthetic test files.
- `generated/`: local generated corpus; intentionally ignored by Git.
- `evidence/raw/`: local screenshots and raw logs; intentionally ignored by Git.

## Generate the controlled corpus

From the repository root in PowerShell:

```powershell
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\generate_test_corpus.py
```

The generator prints the output directory and writes a `manifest.json` that
records each file's SHA-256 hash, purpose, and expected facts. These hashes make
the assessment reproducible and help prove exactly which input was tested.

## Run the first retrieval baseline

Start the LearnMate backend, then run the first three retrieval tests from the
repository root. Supply a temporary synthetic password through the environment
so it is never stored in Git or the evidence file:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_ir_baseline.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
```

The runner creates a fresh synthetic account, uploads `ir-accuracy.pdf`, runs
`IR-01` to `IR-03`, writes sanitized JSON under `evidence/raw/`, and deletes the
uploaded document. The JWT and password are never written to the evidence.

Run the chunk-boundary and page-reference tests in the same way:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_ir_chunk_provenance.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
```

Run the irrelevant-query and keyword-stuffing tests:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_ir_relevance_manipulation.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
```

Run the retrieved-injection and contradictory-source Tutor tests:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
$env:LEARNMATE_ASSESSMENT_LLM_MODE = "deterministic_fallback"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_ir_tutor_integrity.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
Remove-Item Env:\LEARNMATE_ASSESSMENT_LLM_MODE
```

Set the declared mode to `gemini` only when the running backend—not merely the
test terminal—was started with a working Gemini key. A fallback-only run is
valid evidence for the fallback path, but it must not be described as a Gemini
model security result.

Run the clean and adversarial image OCR test:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
$env:LEARNMATE_ASSESSMENT_LLM_MODE = "deterministic_fallback"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_ir_ocr.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
Remove-Item Env:\LEARNMATE_ASSESSMENT_LLM_MODE
```

This records OCR character and word error rates, retrieval rank, page/source
provenance, and downstream handling of adversarial text. Use `gemini` only when
the backend itself was started with a valid Gemini key.

Run the JWT enforcement test only against a local assessment backend started
with the same disposable test-only signing secret:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
$env:LEARNMATE_ASSESSMENT_JWT_SECRET = "same-local-test-secret-used-by-backend"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_sec_jwt_enforcement.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
Remove-Item Env:\LEARNMATE_ASSESSMENT_JWT_SECRET
```

The JWT secret is needed only to create a correctly signed but expired token.
Never use or record a production secret for this local controlled assessment.

Run the cross-user semantic-search authorization test:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_sec_cross_user_search.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
```

The runner creates two synthetic users, uploads a uniquely identifiable source
as User A, compares User B's denial with a nonexistent-ID control, verifies that
User A retains access, and deletes the document.

Run the cross-user metadata and deletion authorization test:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_sec_cross_user_management.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
```

This verifies User B's list, get and delete behavior, compares foreign-resource
responses with nonexistent-resource controls, and confirms that User A's
metadata, stored file and searchable vector content remain intact.

Run the filename and path-traversal test:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_sec_path_traversal.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
```

The runner submits six path-shaped filenames, verifies sanitized display names,
UUID-only internal names, upload-directory containment and file hashes, then
deletes only its own test documents and checks that pre-existing uploads remain.

Run the extension, MIME type and file-signature validation test:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_sec_type_validation.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
```

The runner tests nine rejected combinations, verifies that upload, SQLite and
Chroma state remain unchanged after each rejection, runs one valid uppercase
PDF control, and restores the original state during cleanup.

Run the malformed and protected file test:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_sec_malformed_files.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
```

The runner tests corrupt PDF, truncated PDF, password-protected PDF, corrupt PNG
and corrupt JPEG inputs. It checks controlled errors, service health and all
three persistence layers, then runs a valid upload control and cleans it up.

Run the no-extractable-text rollback test:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_sec_empty_content.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
```

The runner submits a blank PDF and blank image, expects controlled 422
responses, and verifies that the upload directory, SQLite and Chroma remain
unchanged. It then runs and removes a valid PDF control.

Run the byte-size and decoded-image resource-limit test:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_sec_resource_limits.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
```

The runner checks one-byte-below and one-byte-above upload boundaries plus a
compressed image whose decoded dimensions exceed the configured pixel limit.

Run the controlled query-length and request-burst test:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_sec_query_abuse.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
```

The runner uses only the local API, caps queries at 32 KiB, and limits the burst
to 12 requests with four workers. It records median/p95 latency and restores
the uploaded test document afterward.

Run the deletion-lifecycle test:

```powershell
$env:LEARNMATE_ASSESSMENT_PASSWORD = "choose-a-temporary-test-password"
.\backend\.venv\Scripts\python.exe .\docs\security-assessment\tools\run_sec_deletion_lifecycle.py
Remove-Item Env:\LEARNMATE_ASSESSMENT_PASSWORD
```

The runner proves that file, SQLite metadata and Chroma chunks exist before
deletion, verifies all are removed, and compares later get/search/delete
responses with nonexistent-resource controls.

## Evidence naming

Use predictable names such as:

```text
IR-01-request.json
IR-01-response.json
IR-01-screenshot-01.png
SEC-02-user-b-search-response.json
```

Store raw evidence locally under `evidence/raw/`. Copy only sanitized evidence
into the final individual report.
