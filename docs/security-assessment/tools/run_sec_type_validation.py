"""Run SEC-05 extension, MIME type, and file-signature validation checks."""

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

import pymupdf
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


def make_jpeg_bytes(png_path: Path) -> bytes:
    pixmap = pymupdf.Pixmap(str(png_path))
    if pixmap.alpha:
        pixmap = pymupdf.Pixmap(pixmap, 0)
    return pixmap.tobytes("jpeg")


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


def main() -> None:
    password = os.getenv("LEARNMATE_ASSESSMENT_PASSWORD")
    if not password:
        raise SystemExit(
            "Set LEARNMATE_ASSESSMENT_PASSWORD to a temporary synthetic password."
        )

    pdf_path = CORPUS_DIRECTORY / "ir-accuracy.pdf"
    png_path = CORPUS_DIRECTORY / "ocr-clean.png"
    signature_mismatch_path = CORPUS_DIRECTORY / "signature-mismatch.pdf"
    if not all(path.is_file() for path in (pdf_path, png_path, signature_mismatch_path)):
        raise SystemExit("Generate the controlled corpus before running SEC-05.")

    pdf_bytes = pdf_path.read_bytes()
    png_bytes = png_path.read_bytes()
    jpeg_bytes = make_jpeg_bytes(png_path)
    signature_mismatch_bytes = signature_mismatch_path.read_bytes()

    rejection_cases = [
        {
            "case": "pdf_extension_png_mime",
            "filename": "material.pdf",
            "content_type": "image/png",
            "content": pdf_bytes,
            "expected_status": 415,
            "expected_detail": "The uploaded file content type does not match its extension.",
        },
        {
            "case": "png_extension_pdf_mime",
            "filename": "material.png",
            "content_type": "application/pdf",
            "content": png_bytes,
            "expected_status": 415,
            "expected_detail": "The uploaded file content type does not match its extension.",
        },
        {
            "case": "jpeg_extension_png_mime",
            "filename": "material.jpg",
            "content_type": "image/png",
            "content": jpeg_bytes,
            "expected_status": 415,
            "expected_detail": "The uploaded file content type does not match its extension.",
        },
        {
            "case": "pdf_declared_with_non_pdf_signature",
            "filename": "signature-mismatch.pdf",
            "content_type": "application/pdf",
            "content": signature_mismatch_bytes,
            "expected_status": 400,
            "expected_detail": "The uploaded file signature does not match its declared format.",
        },
        {
            "case": "png_declared_with_pdf_signature",
            "filename": "material.png",
            "content_type": "image/png",
            "content": pdf_bytes,
            "expected_status": 400,
            "expected_detail": "The uploaded file signature does not match its declared format.",
        },
        {
            "case": "jpeg_declared_with_png_signature",
            "filename": "material.jpeg",
            "content_type": "image/jpeg",
            "content": png_bytes,
            "expected_status": 400,
            "expected_detail": "The uploaded file signature does not match its declared format.",
        },
        {
            "case": "unsupported_txt_extension",
            "filename": "material.txt",
            "content_type": "application/pdf",
            "content": pdf_bytes,
            "expected_status": 400,
            "expected_detail": "Only PDF, PNG, JPG, and JPEG files are allowed.",
        },
        {
            "case": "pdf_generic_binary_mime",
            "filename": "material.pdf",
            "content_type": "application/octet-stream",
            "content": pdf_bytes,
            "expected_status": 415,
            "expected_detail": "The uploaded file content type does not match its extension.",
        },
        {
            "case": "unsupported_executable",
            "filename": "material.exe",
            "content_type": "application/octet-stream",
            "content": b"MZ synthetic executable marker",
            "expected_status": 400,
            "expected_detail": "Only PDF, PNG, JPG, and JPEG files are allowed.",
        },
    ]

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    test_email = f"sec05-type-{run_stamp.lower()}@example.test"
    evidence: dict[str, Any] = {
        "run_id": run_stamp,
        "started_at": utc_now(),
        "base_url": BASE_URL,
        "git_commit": current_commit(),
        "test_id": "SEC-05",
        "synthetic_account": test_email,
        "secret_handling": "Password and bearer token were not recorded.",
        "controlled_inputs": {
            "pdf_sha256": sha256(pdf_path),
            "png_sha256": sha256(png_path),
            "signature_mismatch_sha256": sha256(signature_mismatch_path),
        },
        "rejection_cases": [],
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
                "full_name": "SEC05 Type Tester",
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

        for test_case in rejection_cases:
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
            expected_body = {"detail": test_case["expected_detail"]}
            case_passed = (
                response.status_code == test_case["expected_status"]
                and body == expected_body
                and state_matches(after, baseline)
            )
            evidence["rejection_cases"].append(
                {
                    "case": test_case["case"],
                    "filename": test_case["filename"],
                    "declared_content_type": test_case["content_type"],
                    "expected_status": test_case["expected_status"],
                    "actual_status": response.status_code,
                    "latency_ms": latency,
                    "response": body,
                    "upload_directory_unchanged": (
                        after["upload_paths"] == baseline["upload_paths"]
                    ),
                    "sqlite_user_document_count_unchanged": (
                        after["user_document_count"]
                        == baseline["user_document_count"]
                    ),
                    "chroma_record_count_unchanged": (
                        after["chroma_record_count"]
                        == baseline["chroma_record_count"]
                    ),
                    "outcome": "Pass" if case_passed else "Fail",
                }
            )

        with pdf_path.open("rb") as input_file:
            control_response, control_latency = send_request(
                "POST",
                "/documents/upload",
                headers=authorization,
                files={"file": ("VALID-UPPERCASE.PDF", input_file, "application/pdf")},
            )
        control_body = response_json(control_response)
        control_response.raise_for_status()
        control_document_id = control_body["document"]["document_id"]
        created_document_ids.append(control_document_id)
        control_state = state_snapshot(user_id=user_id, vector_store=vector_store)
        evidence["valid_control"] = {
            "status_code": control_response.status_code,
            "latency_ms": control_latency,
            "response": control_body,
            "sqlite_document_count_increased": (
                control_state["user_document_count"]
                == int(baseline["user_document_count"]) + 1
            ),
            "chroma_record_count_increased": (
                int(control_state["chroma_record_count"])
                > int(baseline["chroma_record_count"])
            ),
            "upload_pdf_count_increased": (
                int(control_state["upload_pdf_count"])
                == int(baseline["upload_pdf_count"]) + 1
            ),
        }

        passed_cases = sum(
            case["outcome"] == "Pass" for case in evidence["rejection_cases"]
        )
        valid_control_passed = all(
            (
                control_response.status_code == 201,
                evidence["valid_control"]["sqlite_document_count_increased"],
                evidence["valid_control"]["chroma_record_count_increased"],
                evidence["valid_control"]["upload_pdf_count_increased"],
            )
        )
        evidence["summary"] = {
            "rejection_cases_executed": len(rejection_cases),
            "rejection_cases_passed": passed_cases,
            "rejection_cases_failed": len(rejection_cases) - passed_cases,
            "all_rejections_preserved_upload_state": all(
                case["upload_directory_unchanged"]
                for case in evidence["rejection_cases"]
            ),
            "all_rejections_preserved_sqlite_state": all(
                case["sqlite_user_document_count_unchanged"]
                for case in evidence["rejection_cases"]
            ),
            "all_rejections_preserved_chroma_state": all(
                case["chroma_record_count_unchanged"]
                for case in evidence["rejection_cases"]
            ),
            "valid_uppercase_pdf_control_passed": valid_control_passed,
            "outcome": (
                "Pass"
                if passed_cases == len(rejection_cases) and valid_control_passed
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
            baseline_public = evidence.get("baseline_state")
            evidence["post_cleanup"]["returned_to_baseline"] = (
                baseline_public is not None
                and public_snapshot(final_state) == baseline_public
            )
        else:
            evidence["post_cleanup"] = {"returned_to_baseline": False}

        evidence["finished_at"] = utc_now()
        evidence["cleanup_succeeded"] = (
            bool(evidence["cleanup"])
            and all(item["status_code"] == 200 for item in evidence["cleanup"])
            and bool(evidence["post_cleanup"].get("returned_to_baseline"))
        )
        if evidence.get("summary") and not evidence["cleanup_succeeded"]:
            evidence["summary"]["outcome"] = "Fail"

        EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        evidence_path = EVIDENCE_DIRECTORY / f"sec-type-validation-{run_stamp}.json"
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(f"Evidence: {evidence_path}")
        print(json.dumps(evidence.get("summary", {}), indent=2))
        print(f"Cleanup succeeded: {evidence['cleanup_succeeded']}")


if __name__ == "__main__":
    main()
