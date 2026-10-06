"""Run SEC-09 controlled query-length and request-burst checks."""

from __future__ import annotations

import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
QUERY_LENGTHS = (128, 1024, 8192, 32768)
BURST_REQUEST_COUNT = 12
BURST_WORKERS = 4

sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.core.config import UPLOAD_DIRECTORY  # noqa: E402
from app.database.database import get_application_database  # noqa: E402
from app.services.vector_store_service import VectorStoreService  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def compact_search_response(body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        return {"body_type": type(body).__name__}

    results = body.get("results")
    if not isinstance(results, list):
        return {"detail": body.get("detail"), "result_count": None}

    first_result = results[0] if results else {}
    return {
        "result_count": len(results),
        "first_result_page": first_result.get("page_number"),
        "first_result_distance": first_result.get("distance"),
    }


def query_for_length(length: int) -> str:
    seed = "What year was the Orion Protocol created? controlled context "
    repeated = (seed * math.ceil(length / len(seed)))[:length]
    if len(repeated) != length:
        raise AssertionError("The controlled query length is incorrect.")
    return repeated


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def nearest_rank_percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


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


def main() -> None:
    password = os.getenv("LEARNMATE_ASSESSMENT_PASSWORD")
    if not password:
        raise SystemExit(
            "Set LEARNMATE_ASSESSMENT_PASSWORD to a temporary synthetic password."
        )

    source_path = CORPUS_DIRECTORY / "ir-accuracy.pdf"
    if not source_path.is_file():
        raise SystemExit("Generate the controlled corpus before running SEC-09.")

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    test_email = f"sec09-query-{run_stamp.lower()}@example.test"
    evidence: dict[str, Any] = {
        "run_id": run_stamp,
        "started_at": utc_now(),
        "base_url": BASE_URL,
        "git_commit": current_commit(),
        "test_id": "SEC-09",
        "synthetic_account": test_email,
        "safety_boundary": {
            "query_lengths": list(QUERY_LENGTHS),
            "burst_request_count": BURST_REQUEST_COUNT,
            "burst_workers": BURST_WORKERS,
            "public_or_external_target_used": False,
        },
        "secret_handling": (
            "Password, bearer token, full long queries, and internal filenames were "
            "not recorded."
        ),
        "query_length_cases": [],
        "burst_requests": [],
        "cleanup": [],
    }

    vector_store = VectorStoreService()
    authorization: dict[str, str] | None = None
    user_id: str | None = None
    document_id: str | None = None
    initial_state: dict[str, int | set[Path]] | None = None

    try:
        signup_response, signup_latency = send_request(
            "POST",
            "/auth/signup",
            json_body={
                "full_name": "SEC09 Query Abuse Tester",
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

        initial_state = state_snapshot(user_id, vector_store)
        evidence["initial_state"] = public_snapshot(initial_state)
        evidence["health_before"] = service_health()

        with source_path.open("rb") as source_file:
            upload_response, upload_latency = send_request(
                "POST",
                "/documents/upload",
                headers=authorization,
                files={
                    "file": (
                        "sec09-query-source.pdf",
                        source_file,
                        "application/pdf",
                    )
                },
            )
        upload_body = response_json(upload_response)
        upload_response.raise_for_status()
        document_id = upload_body["document"]["document_id"]
        evidence["setup_upload"] = {
            "status_code": upload_response.status_code,
            "latency_ms": upload_latency,
            "document": upload_body["document"],
        }

        query_baseline = state_snapshot(user_id, vector_store)
        evidence["query_state_baseline"] = public_snapshot(query_baseline)

        for length in QUERY_LENGTHS:
            query = query_for_length(length)
            response, latency = send_request(
                "POST",
                "/documents/search",
                headers=authorization,
                json_body={
                    "document_id": document_id,
                    "query": query,
                    "top_k": 3,
                },
            )
            body = response_json(response)
            body_text = json.dumps(body).lower()
            evidence["query_length_cases"].append(
                {
                    "query_length_characters": length,
                    "query_sha256": sha256_text(query),
                    "status_code": response.status_code,
                    "latency_ms": latency,
                    "response_summary": compact_search_response(body),
                    "bounded_rejection": response.status_code in (413, 422, 429),
                    "no_internal_details": not any(
                        marker in body_text
                        for marker in (
                            "traceback",
                            "sentence_transformers",
                            "sqlite",
                            "chroma",
                            "stored_filename",
                        )
                    ),
                }
            )

        def burst_request(index: int) -> dict[str, Any]:
            response, latency = send_request(
                "POST",
                "/documents/search",
                headers=authorization,
                json_body={
                    "document_id": document_id,
                    "query": f"What year was the Orion Protocol created? burst {index}",
                    "top_k": 1,
                },
            )
            body = response_json(response)
            return {
                "request_number": index,
                "status_code": response.status_code,
                "latency_ms": latency,
                "response_summary": compact_search_response(body),
            }

        with ThreadPoolExecutor(max_workers=BURST_WORKERS) as executor:
            futures = [
                executor.submit(burst_request, index)
                for index in range(1, BURST_REQUEST_COUNT + 1)
            ]
            for future in as_completed(futures):
                evidence["burst_requests"].append(future.result())
        evidence["burst_requests"].sort(key=lambda item: item["request_number"])

        query_after = state_snapshot(user_id, vector_store)
        health_after = service_health()
        length_latencies = [
            float(case["latency_ms"]) for case in evidence["query_length_cases"]
        ]
        burst_latencies = [
            float(item["latency_ms"]) for item in evidence["burst_requests"]
        ]
        burst_status_distribution: dict[str, int] = {}
        for item in evidence["burst_requests"]:
            status_key = str(item["status_code"])
            burst_status_distribution[status_key] = (
                burst_status_distribution.get(status_key, 0) + 1
            )

        max_accepted_query_length = max(
            (
                int(case["query_length_characters"])
                for case in evidence["query_length_cases"]
                if case["status_code"] == 200
            ),
            default=0,
        )
        excessive_query_rejected = any(
            case["bounded_rejection"]
            for case in evidence["query_length_cases"]
            if int(case["query_length_characters"]) >= 8192
        )
        rate_limit_observed = any(
            item["status_code"] == 429 for item in evidence["burst_requests"]
        )
        all_safe_responses = all(
            case["no_internal_details"] for case in evidence["query_length_cases"]
        )
        state_preserved = state_matches(query_after, query_baseline)

        evidence["summary"] = {
            "query_length_cases_executed": len(QUERY_LENGTHS),
            "maximum_accepted_query_length": max_accepted_query_length,
            "excessive_query_rejected": excessive_query_rejected,
            "query_latency_median_ms": round(statistics.median(length_latencies), 2),
            "query_latency_p95_ms": round(
                nearest_rank_percentile(length_latencies, 0.95),
                2,
            ),
            "burst_request_count": BURST_REQUEST_COUNT,
            "burst_status_distribution": burst_status_distribution,
            "rate_limit_observed": rate_limit_observed,
            "burst_latency_median_ms": round(statistics.median(burst_latencies), 2),
            "burst_latency_p95_ms": round(
                nearest_rank_percentile(burst_latencies, 0.95),
                2,
            ),
            "no_internal_details_exposed": all_safe_responses,
            "query_operations_preserved_storage_state": state_preserved,
            "service_healthy_after_test": health_after["healthy"],
            "outcome": (
                "Pass"
                if excessive_query_rejected
                and rate_limit_observed
                and all_safe_responses
                and state_preserved
                and health_after["healthy"]
                else "Fail"
            ),
        }
    finally:
        if authorization and document_id:
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

        if user_id and initial_state:
            final_state = state_snapshot(user_id, vector_store)
            evidence["post_cleanup"] = public_snapshot(final_state)
            evidence["post_cleanup"]["returned_to_initial_state"] = state_matches(
                final_state,
                initial_state,
            )
        else:
            evidence["post_cleanup"] = {"returned_to_initial_state": False}

        evidence["health_after_cleanup"] = service_health()
        evidence["finished_at"] = utc_now()
        evidence["cleanup_succeeded"] = (
            bool(evidence["cleanup"])
            and all(item["status_code"] == 200 for item in evidence["cleanup"])
            and bool(evidence["post_cleanup"].get("returned_to_initial_state"))
            and bool(evidence["health_after_cleanup"]["healthy"])
        )

        EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        evidence_path = EVIDENCE_DIRECTORY / f"sec-query-abuse-{run_stamp}.json"
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(f"Evidence: {evidence_path}")
        print(json.dumps(evidence.get("summary", {}), indent=2))
        print(f"Cleanup succeeded: {evidence['cleanup_succeeded']}")


if __name__ == "__main__":
    main()
