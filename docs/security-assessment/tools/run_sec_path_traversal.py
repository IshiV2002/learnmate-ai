"""Run SEC-04 filename and path-traversal upload checks."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ASSESSMENT_DIRECTORY = Path(__file__).resolve().parent.parent
REPOSITORY_DIRECTORY = ASSESSMENT_DIRECTORY.parent.parent
BACKEND_DIRECTORY = REPOSITORY_DIRECTORY / "backend"
CORPUS_DIRECTORY = ASSESSMENT_DIRECTORY / "generated"
EVIDENCE_DIRECTORY = ASSESSMENT_DIRECTORY / "evidence" / "raw"
BASE_URL = os.getenv("LEARNMATE_ASSESSMENT_API_URL", "http://127.0.0.1:8000")
UUID_STORAGE_PATTERN = re.compile(r"^[0-9a-f]{32}\.pdf$")

sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.core.config import UPLOAD_DIRECTORY  # noqa: E402
from app.database.database import get_application_database  # noqa: E402


TEST_CASES = [
    {
        "case": "posix_parent_segments",
        "submitted_filename": "../../escape-posix.pdf",
        "expected_display_filename": "escape-posix.pdf",
    },
    {
        "case": "windows_parent_segments",
        "submitted_filename": r"..\..\escape-windows.pdf",
        "expected_display_filename": "escape-windows.pdf",
    },
    {
        "case": "windows_drive_path",
        "submitted_filename": r"C:\temp\escape-drive.pdf",
        "expected_display_filename": "escape-drive.pdf",
    },
    {
        "case": "posix_absolute_path",
        "submitted_filename": "/var/tmp/escape-absolute.pdf",
        "expected_display_filename": "escape-absolute.pdf",
    },
    {
        "case": "mixed_separators",
        "submitted_filename": r"folder\sub/../../escape-mixed.pdf",
        "expected_display_filename": "escape-mixed.pdf",
    },
    {
        "case": "unicode_path",
        "submitted_filename": "../课程/lecture-安全.pdf",
        "expected_display_filename": "lecture-安全.pdf",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for block in iter(lambda: input_file.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def current_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_DIRECTORY,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def send_request(
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    timeout: int = 180,
) -> tuple[requests.Response, float]:
    started = time.perf_counter()
    response = requests.request(
        method,
        f"{BASE_URL}{path}",
        headers=headers,
        json=json_body,
        files=files,
        timeout=timeout,
    )
    return response, round((time.perf_counter() - started) * 1000, 2)


def response_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except requests.JSONDecodeError:
        return {"non_json_body": response.text[:1000]}


def main() -> None:
    password = os.getenv("LEARNMATE_ASSESSMENT_PASSWORD")
    if not password:
        raise SystemExit(
            "Set LEARNMATE_ASSESSMENT_PASSWORD to a temporary synthetic password."
        )

    corpus_path = CORPUS_DIRECTORY / "ir-accuracy.pdf"
    if not corpus_path.is_file():
        raise SystemExit("Generate the controlled corpus before running SEC-04.")
    input_hash = sha256(corpus_path)

    upload_directory = UPLOAD_DIRECTORY.resolve()
    baseline_pdf_paths = set(upload_directory.glob("*.pdf"))
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    test_email = f"sec04-path-{run_stamp.lower()}@example.test"
    evidence: dict[str, Any] = {
        "run_id": run_stamp,
        "started_at": utc_now(),
        "base_url": BASE_URL,
        "git_commit": current_commit(),
        "test_id": "SEC-04",
        "synthetic_account": test_email,
        "secret_handling": (
            "Password, bearer token, and generated internal filenames were not recorded."
        ),
        "input_filename": corpus_path.name,
        "input_sha256": input_hash,
        "baseline_upload_pdf_count": len(baseline_pdf_paths),
        "cases": [],
        "cleanup": [],
    }

    authorization: dict[str, str] | None = None
    user_id: str | None = None
    created_documents: list[tuple[str, Path]] = []

    try:
        signup_response, signup_latency = send_request(
            "POST",
            "/auth/signup",
            json_body={
                "full_name": "SEC04 Path Tester",
                "email": test_email,
                "password": password,
            },
        )
        signup_body = response_json(signup_response)
        signup_response.raise_for_status()
        authorization = {"Authorization": f"Bearer {signup_body['access_token']}"}
        user_id = signup_body["user"]["user_id"]
        evidence["setup_signup"] = {
            "status_code": signup_response.status_code,
            "latency_ms": signup_latency,
            "user": signup_body["user"],
            "access_token_recorded": False,
        }

        for test_case in TEST_CASES:
            with corpus_path.open("rb") as input_file:
                response, latency = send_request(
                    "POST",
                    "/documents/upload",
                    headers=authorization,
                    files={
                        "file": (
                            test_case["submitted_filename"],
                            input_file,
                            "application/pdf",
                        )
                    },
                )
            body = response_json(response)
            response.raise_for_status()
            public_document = body["document"]
            document_id = public_document["document_id"]
            record = get_application_database().get_document(document_id, user_id)
            if record is None:
                raise RuntimeError("Uploaded metadata was not found for inspection.")

            stored_path = (upload_directory / record.stored_filename).resolve()
            created_documents.append((document_id, stored_path))
            public_response_text = json.dumps(body, ensure_ascii=False)
            case_passed = all(
                (
                    response.status_code == 201,
                    public_document.get("original_filename")
                    == test_case["expected_display_filename"],
                    "stored_filename" not in public_response_text,
                    UUID_STORAGE_PATTERN.fullmatch(record.stored_filename) is not None,
                    stored_path.parent == upload_directory,
                    stored_path.is_file(),
                    sha256(stored_path) == input_hash,
                )
            )
            evidence["cases"].append(
                {
                    "case": test_case["case"],
                    "submitted_filename": test_case["submitted_filename"],
                    "expected_display_filename": test_case[
                        "expected_display_filename"
                    ],
                    "status_code": response.status_code,
                    "latency_ms": latency,
                    "actual_display_filename": public_document.get(
                        "original_filename"
                    ),
                    "internal_filename_exposed": (
                        "stored_filename" in public_response_text
                    ),
                    "internal_filename_matches_uuid_pattern": (
                        UUID_STORAGE_PATTERN.fullmatch(record.stored_filename)
                        is not None
                    ),
                    "stored_path_inside_upload_directory": (
                        stored_path.parent == upload_directory
                    ),
                    "stored_file_exists": stored_path.is_file(),
                    "stored_file_hash_matches_input": (
                        stored_path.is_file() and sha256(stored_path) == input_hash
                    ),
                    "outcome": "Pass" if case_passed else "Fail",
                    "public_response": body,
                }
            )

        list_response, list_latency = send_request(
            "GET",
            "/documents",
            headers=authorization,
        )
        list_body = response_json(list_response)
        list_response.raise_for_status()
        listed_names = sorted(
            item["original_filename"]
            for item in list_body
            if item.get("document_id")
            in {document_id for document_id, _ in created_documents}
        )
        expected_names = sorted(
            test_case["expected_display_filename"] for test_case in TEST_CASES
        )
        evidence["library_check"] = {
            "status_code": list_response.status_code,
            "latency_ms": list_latency,
            "sanitized_names_match_expected": listed_names == expected_names,
            "listed_display_filenames": listed_names,
        }

        passed_cases = sum(
            case["outcome"] == "Pass" for case in evidence["cases"]
        )
        evidence["summary"] = {
            "cases_executed": len(evidence["cases"]),
            "cases_passed": passed_cases,
            "cases_failed": len(evidence["cases"]) - passed_cases,
            "all_paths_inside_upload_directory": all(
                case["stored_path_inside_upload_directory"]
                for case in evidence["cases"]
            ),
            "all_internal_names_use_uuid_pattern": all(
                case["internal_filename_matches_uuid_pattern"]
                for case in evidence["cases"]
            ),
            "no_internal_filename_exposure": all(
                not case["internal_filename_exposed"]
                for case in evidence["cases"]
            ),
            "all_file_hashes_match": all(
                case["stored_file_hash_matches_input"]
                for case in evidence["cases"]
            ),
            "sanitized_library_names_correct": listed_names == expected_names,
            "outcome": (
                "Pass"
                if passed_cases == len(TEST_CASES) and listed_names == expected_names
                else "Fail"
            ),
        }
    finally:
        if authorization:
            for document_id, _ in reversed(created_documents):
                delete_response, delete_latency = send_request(
                    "DELETE",
                    f"/documents/{document_id}",
                    headers=authorization,
                )
                evidence["cleanup"].append(
                    {
                        "resource": "test_document",
                        "resource_id": document_id,
                        "status_code": delete_response.status_code,
                        "latency_ms": delete_latency,
                        "response": response_json(delete_response),
                    }
                )

        final_pdf_paths = set(upload_directory.glob("*.pdf"))
        evidence["post_cleanup"] = {
            "all_test_files_removed": all(
                not stored_path.exists() for _, stored_path in created_documents
            ),
            "upload_directory_returned_to_baseline": (
                final_pdf_paths == baseline_pdf_paths
            ),
            "final_upload_pdf_count": len(final_pdf_paths),
        }
        evidence["finished_at"] = utc_now()
        evidence["cleanup_succeeded"] = (
            len(evidence["cleanup"]) == len(created_documents)
            and all(item["status_code"] == 200 for item in evidence["cleanup"])
            and evidence["post_cleanup"]["all_test_files_removed"]
            and evidence["post_cleanup"][
                "upload_directory_returned_to_baseline"
            ]
        )
        if evidence.get("summary") and not evidence["cleanup_succeeded"]:
            evidence["summary"]["outcome"] = "Fail"

        EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        evidence_path = EVIDENCE_DIRECTORY / f"sec-path-traversal-{run_stamp}.json"
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(f"Evidence: {evidence_path}")
        print(json.dumps(evidence.get("summary", {}), indent=2))
        print(f"Cleanup succeeded: {evidence['cleanup_succeeded']}")


if __name__ == "__main__":
    main()
