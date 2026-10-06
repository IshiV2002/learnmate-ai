"""Run SEC-06 corrupt, truncated, protected, and malformed-file checks."""

from __future__ import annotations

import hashlib
import json
import os
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

sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.core.config import UPLOAD_DIRECTORY  # noqa: E402
from app.database.database import get_application_database  # noqa: E402
from app.services.vector_store_service import VectorStoreService  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


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


def state_snapshot(
    *,
    user_id: str,
    vector_store: VectorStoreService,
) -> dict[str, int | set[Path]]:
    upload_paths = set(UPLOAD_DIRECTORY.resolve().glob("*.pdf"))
    return {
        "upload_paths": upload_paths,
        "upload_pdf_count": len(upload_paths),
        "user_document_count": len(
            get_application_database().list_documents(user_id)
        ),
        "chroma_record_count": vector_store.collection.count(),
    }


def public_snapshot(snapshot: dict[str, int | set[Path]]) -> dict[str, int]:
    return {
        "upload_pdf_count": int(snapshot["upload_pdf_count"]),
        "user_document_count": int(snapshot["user_document_count"]),
        "chroma_record_count": int(snapshot["chroma_record_count"]),
    }


def state_matches(
    current: dict[str, int | set[Path]],
    baseline: dict[str, int | set[Path]],
) -> bool:
    return (
        current["upload_paths"] == baseline["upload_paths"]
        and current["user_document_count"] == baseline["user_document_count"]
        and current["chroma_record_count"] == baseline["chroma_record_count"]
    )


def service_health() -> dict[str, Any]:
    response, latency = send_request("GET", "/health", timeout=10)
    return {
        "status_code": response.status_code,
        "latency_ms": latency,
        "response": response_json(response),
        "healthy": response.status_code == 200
        and response_json(response) == {"status": "healthy"},
    }


def main() -> None:
    password = os.getenv("LEARNMATE_ASSESSMENT_PASSWORD")
    if not password:
        raise SystemExit(
            "Set LEARNMATE_ASSESSMENT_PASSWORD to a temporary synthetic password."
        )

    valid_pdf_path = CORPUS_DIRECTORY / "ir-accuracy.pdf"
    corrupt_pdf_path = CORPUS_DIRECTORY / "corrupt-truncated.pdf"
    encrypted_pdf_path = CORPUS_DIRECTORY / "encrypted-test-only.pdf"
    if not all(
        path.is_file()
        for path in (valid_pdf_path, corrupt_pdf_path, encrypted_pdf_path)
    ):
        raise SystemExit("Generate the controlled corpus before running SEC-06.")

    valid_pdf_bytes = valid_pdf_path.read_bytes()
    corrupt_pdf_bytes = corrupt_pdf_path.read_bytes()
    encrypted_pdf_bytes = encrypted_pdf_path.read_bytes()
    truncated_pdf_bytes = valid_pdf_bytes[:128]
    corrupt_png_bytes = b"\x89PNG\r\n\x1a\n" + b"intentionally corrupt PNG data"
    corrupt_jpeg_bytes = b"\xff\xd8\xff" + b"intentionally corrupt JPEG data"

    cases = [
        {
            "case": "corrupt_pdf",
            "filename": "corrupt.pdf",
            "content_type": "application/pdf",
            "content": corrupt_pdf_bytes,
            "input_sha256": sha256(corrupt_pdf_path),
            "expected_detail": "The uploaded PDF could not be opened or processed.",
        },
        {
            "case": "truncated_valid_pdf",
            "filename": "truncated.pdf",
            "content_type": "application/pdf",
            "content": truncated_pdf_bytes,
            "input_sha256": sha256_bytes(truncated_pdf_bytes),
            "expected_detail": "The uploaded PDF could not be opened or processed.",
        },
        {
            "case": "password_protected_pdf",
            "filename": "protected.pdf",
            "content_type": "application/pdf",
            "content": encrypted_pdf_bytes,
            "input_sha256": sha256(encrypted_pdf_path),
            "expected_detail": "The uploaded PDF could not be opened or processed.",
        },
        {
            "case": "corrupt_png",
            "filename": "corrupt.png",
            "content_type": "image/png",
            "content": corrupt_png_bytes,
            "input_sha256": sha256_bytes(corrupt_png_bytes),
            "expected_detail": "The uploaded image could not be opened or processed.",
        },
        {
            "case": "corrupt_jpeg",
            "filename": "corrupt.jpg",
            "content_type": "image/jpeg",
            "content": corrupt_jpeg_bytes,
            "input_sha256": sha256_bytes(corrupt_jpeg_bytes),
            "expected_detail": "The uploaded image could not be opened or processed.",
        },
    ]

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    test_email = f"sec06-malformed-{run_stamp.lower()}@example.test"
    evidence: dict[str, Any] = {
        "run_id": run_stamp,
        "started_at": utc_now(),
        "base_url": BASE_URL,
        "git_commit": current_commit(),
        "test_id": "SEC-06",
        "synthetic_account": test_email,
        "secret_handling": (
            "Password, bearer token, parser exception details, and internal filenames "
            "were not recorded."
        ),
        "cases": [],
        "cleanup": [],
    }

    authorization: dict[str, str] | None = None
    user_id: str | None = None
    created_document_ids: list[str] = []
    vector_store = VectorStoreService()

    try:
        signup_response, signup_latency = send_request(
            "POST",
            "/auth/signup",
            json_body={
                "full_name": "SEC06 Malformed File Tester",
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

        baseline = state_snapshot(user_id=user_id, vector_store=vector_store)
        evidence["baseline_state"] = public_snapshot(baseline)
        evidence["health_before"] = service_health()

        for test_case in cases:
            case_baseline = state_snapshot(
                user_id=user_id,
                vector_store=vector_store,
            )
            response, latency = send_request(
                "POST",
                "/documents/upload",
                headers=authorization,
                files={
                    "file": (
                        test_case["filename"],
                        test_case["content"],
                        test_case["content_type"],
                    )
                },
            )
            body = response_json(response)
            if response.status_code == 201 and isinstance(body, dict):
                created_document = body.get("document", {})
                created_document_id = created_document.get("document_id")
                if isinstance(created_document_id, str):
                    created_document_ids.append(created_document_id)

            after = state_snapshot(user_id=user_id, vector_store=vector_store)
            health_after_case = service_health()
            expected_body = {"detail": test_case["expected_detail"]}
            body_text = json.dumps(body).lower()
            no_internal_details = not any(
                marker in body_text
                for marker in (
                    "traceback",
                    "pymupdf",
                    "sqlite",
                    "chroma",
                    "stored_filename",
                )
            )
            case_passed = (
                response.status_code == 400
                and body == expected_body
                and no_internal_details
                and state_matches(after, case_baseline)
                and health_after_case["healthy"]
            )
            evidence["cases"].append(
                {
                    "case": test_case["case"],
                    "filename": test_case["filename"],
                    "declared_content_type": test_case["content_type"],
                    "input_sha256": test_case["input_sha256"],
                    "status_code": response.status_code,
                    "latency_ms": latency,
                    "response": body,
                    "no_internal_details": no_internal_details,
                    "upload_pdf_count_before": case_baseline["upload_pdf_count"],
                    "upload_pdf_count_after": after["upload_pdf_count"],
                    "new_orphan_upload_count": len(
                        after["upload_paths"] - case_baseline["upload_paths"]
                    ),
                    "upload_directory_unchanged": (
                        after["upload_paths"] == case_baseline["upload_paths"]
                    ),
                    "sqlite_user_document_count_unchanged": (
                        after["user_document_count"]
                        == case_baseline["user_document_count"]
                    ),
                    "chroma_record_count_unchanged": (
                        after["chroma_record_count"]
                        == case_baseline["chroma_record_count"]
                    ),
                    "service_healthy_after_case": health_after_case["healthy"],
                    "health_status_code": health_after_case["status_code"],
                    "outcome": "Pass" if case_passed else "Fail",
                }
            )

        with valid_pdf_path.open("rb") as input_file:
            control_response, control_latency = send_request(
                "POST",
                "/documents/upload",
                headers=authorization,
                files={
                    "file": (
                        "valid-after-malformed.pdf",
                        input_file,
                        "application/pdf",
                    )
                },
            )
        control_body = response_json(control_response)
        control_response.raise_for_status()
        control_document_id = control_body["document"]["document_id"]
        created_document_ids.append(control_document_id)
        evidence["valid_control"] = {
            "status_code": control_response.status_code,
            "latency_ms": control_latency,
            "response": control_body,
        }

        passed_cases = sum(
            case["outcome"] == "Pass" for case in evidence["cases"]
        )
        evidence["summary"] = {
            "cases_executed": len(cases),
            "cases_passed": passed_cases,
            "cases_failed": len(cases) - passed_cases,
            "all_responses_controlled_400": all(
                case["status_code"] == 400 for case in evidence["cases"]
            ),
            "no_internal_details_exposed": all(
                case["no_internal_details"] for case in evidence["cases"]
            ),
            "all_rejections_preserved_upload_state": all(
                case["upload_directory_unchanged"] for case in evidence["cases"]
            ),
            "all_rejections_preserved_sqlite_state": all(
                case["sqlite_user_document_count_unchanged"]
                for case in evidence["cases"]
            ),
            "all_rejections_preserved_chroma_state": all(
                case["chroma_record_count_unchanged"] for case in evidence["cases"]
            ),
            "service_healthy_after_every_case": all(
                case["service_healthy_after_case"] for case in evidence["cases"]
            ),
            "valid_upload_after_malformed_cases": control_response.status_code == 201,
            "outcome": (
                "Pass"
                if passed_cases == len(cases) and control_response.status_code == 201
                else "Fail"
            ),
        }
    finally:
        if authorization:
            for document_id in reversed(created_document_ids):
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

        if user_id:
            final_state = state_snapshot(user_id=user_id, vector_store=vector_store)
            evidence["post_cleanup"] = public_snapshot(final_state)
            evidence["post_cleanup"]["returned_to_baseline"] = (
                evidence.get("baseline_state") == public_snapshot(final_state)
            )
            evidence["post_cleanup"]["orphan_upload_pdf_count"] = max(
                0,
                int(final_state["upload_pdf_count"])
                - int(evidence["baseline_state"]["upload_pdf_count"]),
            )
        else:
            evidence["post_cleanup"] = {"returned_to_baseline": False}

        evidence["health_after_cleanup"] = service_health()
        evidence["finished_at"] = utc_now()
        evidence["cleanup_succeeded"] = (
            bool(evidence["cleanup"])
            and all(item["status_code"] == 200 for item in evidence["cleanup"])
            and bool(evidence["post_cleanup"].get("returned_to_baseline"))
            and bool(evidence["health_after_cleanup"]["healthy"])
        )
        if evidence.get("summary") and not evidence["cleanup_succeeded"]:
            evidence["summary"]["outcome"] = "Fail"

        EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        evidence_path = EVIDENCE_DIRECTORY / f"sec-malformed-files-{run_stamp}.json"
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(f"Evidence: {evidence_path}")
        print(json.dumps(evidence.get("summary", {}), indent=2))
        print(f"Cleanup succeeded: {evidence['cleanup_succeeded']}")


if __name__ == "__main__":
    main()
