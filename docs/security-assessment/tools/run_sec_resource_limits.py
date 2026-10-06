"""Run SEC-08 upload-byte and decoded-image resource-limit checks."""

from __future__ import annotations

import binascii
import hashlib
import json
import os
import struct
import subprocess
import sys
import time
import zlib
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

from app.core.config import (  # noqa: E402
    MAX_IMAGE_PIXELS,
    MAX_UPLOAD_SIZE_BYTES,
    UPLOAD_DIRECTORY,
)
from app.database.database import get_application_database  # noqa: E402
from app.services.vector_store_service import VectorStoreService  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


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
    timeout: int = 240,
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
    body = response_json(response)
    return {
        "status_code": response.status_code,
        "latency_ms": latency,
        "response": body,
        "healthy": response.status_code == 200 and body == {"status": "healthy"},
    }


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    checksum = binascii.crc32(chunk_type)
    checksum = binascii.crc32(data, checksum) & 0xFFFFFFFF
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", checksum)
    )


def create_compressed_grayscale_png(width: int, height: int) -> bytes:
    """Create a small file whose decoded image dimensions are deliberately large."""
    compressor = zlib.compressobj(level=9)
    compressed_rows = bytearray()
    white_row = b"\x00" + (b"\xff" * width)
    for _ in range(height):
        compressed_rows.extend(compressor.compress(white_row))
    compressed_rows.extend(compressor.flush())

    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", bytes(compressed_rows))
        + png_chunk(b"IEND", b"")
    )


def main() -> None:
    password = os.getenv("LEARNMATE_ASSESSMENT_PASSWORD")
    if not password:
        raise SystemExit(
            "Set LEARNMATE_ASSESSMENT_PASSWORD to a temporary synthetic password."
        )

    valid_pdf_path = CORPUS_DIRECTORY / "ir-accuracy.pdf"
    if not valid_pdf_path.is_file():
        raise SystemExit("Generate the controlled corpus before running SEC-08.")

    valid_pdf = valid_pdf_path.read_bytes()
    below_limit_size = MAX_UPLOAD_SIZE_BYTES - 1
    if len(valid_pdf) >= below_limit_size:
        raise SystemExit("The controlled PDF is unexpectedly too large.")

    # PDF readers permit trailing comment data after the final %%EOF marker.
    # This keeps the boundary input parseable without adding more PDF content.
    padding_prefix = b"\n%"
    below_limit_pdf = valid_pdf + padding_prefix + (
        b"A" * (below_limit_size - len(valid_pdf) - len(padding_prefix))
    )
    above_limit_pdf = b"%PDF-" + (
        b"A" * (MAX_UPLOAD_SIZE_BYTES + 1 - len(b"%PDF-"))
    )

    image_width = 5001
    image_height = 5000
    decoded_pixels = image_width * image_height
    if decoded_pixels <= MAX_IMAGE_PIXELS:
        raise SystemExit("The controlled image does not exceed the pixel limit.")
    oversized_dimension_png = create_compressed_grayscale_png(
        image_width,
        image_height,
    )

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    test_email = f"sec08-limits-{run_stamp.lower()}@example.test"
    evidence: dict[str, Any] = {
        "run_id": run_stamp,
        "started_at": utc_now(),
        "base_url": BASE_URL,
        "git_commit": current_commit(),
        "test_id": "SEC-08",
        "synthetic_account": test_email,
        "configured_limits": {
            "max_upload_size_bytes": MAX_UPLOAD_SIZE_BYTES,
            "max_image_pixels": MAX_IMAGE_PIXELS,
        },
        "secret_handling": (
            "Password, bearer token, and internal filenames were not recorded."
        ),
        "rejection_cases": [],
        "cleanup": [],
    }

    vector_store = VectorStoreService()
    authorization: dict[str, str] | None = None
    user_id: str | None = None
    created_document_ids: list[str] = []

    try:
        signup_response, signup_latency = send_request(
            "POST",
            "/auth/signup",
            json_body={
                "full_name": "SEC08 Resource Limit Tester",
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

        baseline = state_snapshot(user_id, vector_store)
        evidence["baseline_state"] = public_snapshot(baseline)
        evidence["health_before"] = service_health()

        rejection_cases = [
            {
                "case": "one_byte_above_upload_limit",
                "filename": "above-limit.pdf",
                "content_type": "application/pdf",
                "content": above_limit_pdf,
                "expected_detail": (
                    "The uploaded file is too large. "
                    f"The maximum size is {MAX_UPLOAD_SIZE_BYTES} bytes."
                ),
                "decoded_pixels": None,
            },
            {
                "case": "decoded_image_pixel_limit",
                "filename": "over-pixel-limit.png",
                "content_type": "image/png",
                "content": oversized_dimension_png,
                "expected_detail": (
                    "The uploaded image dimensions are too large to process safely."
                ),
                "decoded_pixels": decoded_pixels,
            },
        ]

        for test_case in rejection_cases:
            case_baseline = state_snapshot(user_id, vector_store)
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
            after = state_snapshot(user_id, vector_store)
            health = service_health()
            expected_body = {"detail": test_case["expected_detail"]}
            body_text = json.dumps(body).lower()
            no_internal_details = not any(
                marker in body_text
                for marker in (
                    "traceback",
                    "pymupdf",
                    "tesseract",
                    "sqlite",
                    "chroma",
                    "stored_filename",
                )
            )
            passed = (
                response.status_code == 413
                and body == expected_body
                and no_internal_details
                and state_matches(after, case_baseline)
                and health["healthy"]
            )
            evidence["rejection_cases"].append(
                {
                    "case": test_case["case"],
                    "filename": test_case["filename"],
                    "input_size_bytes": len(test_case["content"]),
                    "input_sha256": sha256_bytes(test_case["content"]),
                    "decoded_pixels": test_case["decoded_pixels"],
                    "status_code": response.status_code,
                    "latency_ms": latency,
                    "response": body,
                    "no_internal_details": no_internal_details,
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
                    "service_healthy_after_case": health["healthy"],
                    "outcome": "Pass" if passed else "Fail",
                }
            )

        accepted_baseline = state_snapshot(user_id, vector_store)
        accepted_response, accepted_latency = send_request(
            "POST",
            "/documents/upload",
            headers=authorization,
            files={
                "file": (
                    "one-byte-below-limit.pdf",
                    below_limit_pdf,
                    "application/pdf",
                )
            },
        )
        accepted_body = response_json(accepted_response)
        if accepted_response.status_code == 201:
            document_id = accepted_body["document"]["document_id"]
            created_document_ids.append(document_id)
        accepted_after = state_snapshot(user_id, vector_store)
        accepted_health = service_health()
        accepted_passed = (
            accepted_response.status_code == 201
            and accepted_body.get("document", {}).get("file_size_bytes")
            == below_limit_size
            and len(accepted_after["upload_paths"] - accepted_baseline["upload_paths"])
            == 1
            and accepted_after["user_document_count"]
            == int(accepted_baseline["user_document_count"]) + 1
            and accepted_after["chroma_record_count"]
            > int(accepted_baseline["chroma_record_count"])
            and accepted_health["healthy"]
        )
        evidence["accepted_boundary_case"] = {
            "case": "one_byte_below_upload_limit",
            "filename": "one-byte-below-limit.pdf",
            "input_size_bytes": len(below_limit_pdf),
            "input_sha256": sha256_bytes(below_limit_pdf),
            "status_code": accepted_response.status_code,
            "latency_ms": accepted_latency,
            "response": accepted_body,
            "upload_count_increased_by_one": len(
                accepted_after["upload_paths"] - accepted_baseline["upload_paths"]
            )
            == 1,
            "sqlite_count_increased_by_one": (
                accepted_after["user_document_count"]
                == int(accepted_baseline["user_document_count"]) + 1
            ),
            "chroma_count_increased": (
                accepted_after["chroma_record_count"]
                > int(accepted_baseline["chroma_record_count"])
            ),
            "service_healthy_after_case": accepted_health["healthy"],
            "outcome": "Pass" if accepted_passed else "Fail",
        }

        rejection_passes = sum(
            case["outcome"] == "Pass" for case in evidence["rejection_cases"]
        )
        evidence["summary"] = {
            "cases_executed": 3,
            "cases_passed": rejection_passes + int(accepted_passed),
            "cases_failed": 3 - rejection_passes - int(accepted_passed),
            "above_byte_limit_rejected_safely": (
                evidence["rejection_cases"][0]["outcome"] == "Pass"
            ),
            "above_pixel_limit_rejected_safely": (
                evidence["rejection_cases"][1]["outcome"] == "Pass"
            ),
            "below_byte_limit_accepted": accepted_passed,
            "service_healthy_after_every_case": all(
                case["service_healthy_after_case"]
                for case in evidence["rejection_cases"]
            )
            and accepted_health["healthy"],
            "outcome": (
                "Pass" if rejection_passes == 2 and accepted_passed else "Fail"
            ),
        }
    finally:
        if authorization:
            for document_id in reversed(created_document_ids):
                response, latency = send_request(
                    "DELETE",
                    f"/documents/{document_id}",
                    headers=authorization,
                )
                evidence["cleanup"].append(
                    {
                        "resource": "test_document",
                        "resource_id": document_id,
                        "status_code": response.status_code,
                        "latency_ms": latency,
                        "response": response_json(response),
                    }
                )

        if user_id:
            final_state = state_snapshot(user_id, vector_store)
            evidence["post_cleanup"] = public_snapshot(final_state)
            evidence["post_cleanup"]["returned_to_baseline"] = (
                evidence.get("baseline_state") == public_snapshot(final_state)
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
        evidence_path = EVIDENCE_DIRECTORY / f"sec-resource-limits-{run_stamp}.json"
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(f"Evidence: {evidence_path}")
        print(json.dumps(evidence.get("summary", {}), indent=2))
        print(f"Cleanup succeeded: {evidence['cleanup_succeeded']}")


if __name__ == "__main__":
    main()
