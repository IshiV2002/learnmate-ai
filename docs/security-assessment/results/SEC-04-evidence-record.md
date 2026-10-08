# SEC-04 Evidence Record - Filename and Path Traversal

## Test identity

- Test ID: SEC-04
- Category: File-upload security and path traversal
- Execution time: 2026-10-06 00:26 Asia/Colombo
- Tester: Individual Student 4 assessor
- Git commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Target: local LearnMate FastAPI instance
- Account: fresh synthetic path-testing account

## Environment and controlled input

- File content: valid controlled `ir-accuracy.pdf`
- Input SHA-256:
  `7d50bd155e43364a6acd9256871264ee3169d38937746113da3e2f6a9250ce5b`
- Baseline upload-directory PDF count: 3 unrelated existing files
- Password, bearer token and generated internal filenames were not recorded.

## Test definition

- Objective: determine whether a client-controlled multipart filename can
  escape the upload directory or expose the server's internal filename.
- Filename forms:
  1. POSIX parent segments: `../../escape-posix.pdf`
  2. Windows parent segments: `..\..\escape-windows.pdf`
  3. Windows drive path: `C:\temp\escape-drive.pdf`
  4. POSIX absolute path: `/var/tmp/escape-absolute.pdf`
  5. Mixed separators and dot segments:
     `folder\sub/../../escape-mixed.pdf`
  6. Unicode path: `../课程/lecture-安全.pdf`
- Expected for every case:
  1. Directory components are removed from the public display name.
  2. Storage uses a server-generated 32-character hexadecimal UUID plus
     `.pdf`.
  3. The resolved file remains directly inside `backend/uploads`.
  4. The stored bytes match the controlled input SHA-256.
  5. The internal stored filename is absent from the public response.

## Actual result

- Cases executed: 6
- Cases passed: 6
- Cases failed: 0
- All uploads returned: 201
- All display filenames matched their safe basenames: Yes
- All internal names matched the UUID-only pattern: Yes
- All resolved paths remained inside the upload directory: Yes
- All stored file hashes matched the controlled input: Yes
- Internal stored filename exposed publicly: No
- Library contained only the six expected sanitized display names: Yes
- Outcome: Pass

Accepting these uploads after securely removing path components is valid
behavior; rejection is not required when the server never uses the client name
as its storage path.

## Cleanup verification

- All six test documents returned 200 on authenticated deletion.
- All six generated test files were removed.
- Upload-directory PDF count after cleanup: 3
- Upload-directory contents returned exactly to the pre-test baseline: Yes
- Unrelated existing uploads were preserved: Yes
- Cleanup succeeded: Yes

## Evidence

- Raw log: `evidence/raw/sec-path-traversal-20261005T185613Z.json`
- Filename-cases screenshot: `SEC-04-01-filename-cases.png`
- Unicode-case screenshot: `SEC-04-02-unicode-case.png`
- Library screenshot: `SEC-04-03-sanitized-library.png`
- Summary screenshot: `SEC-04-04-summary.png`
- Cleanup screenshot: `SEC-04-05-cleanup.png`
- Filename-sanitization code screenshot: `SEC-04-06-sanitization-code.png`
- Safe-storage code screenshot: `SEC-04-07-storage-code.png`
- Public-response code screenshot: `SEC-04-08-public-response-code.png`
- Screenshot status: Pending; capture from the sanitized raw log and narrow
  code sections
- Secret review: no password, bearer token, generated internal filename or API
  key appears in the evidence

## Analysis and conclusion

The server normalizes backslashes, extracts only the final POSIX-style name,
and uses that value for display metadata. Storage is independent: a new UUID
filename is generated, resolved beneath the upload directory and checked for
containment. Public serialization explicitly removes `stored_filename`.

No path-traversal or internal-filename disclosure vulnerability was
demonstrated by these six cases. The test does not evaluate operating-system
symlink attacks or hostile server deployment permissions; those require a
separate infrastructure-level assessment.

## Risk and recommendation

- Confirmed vulnerability: No
- Severity: Not applicable
- Control result: Effective for tested slash, backslash, drive, absolute,
  mixed-separator and Unicode path forms
- Recommendation: retain UUID storage names, path resolution and containment
  checks, continue hiding internal filenames, and add these cases as automated
  upload-security regression tests.
