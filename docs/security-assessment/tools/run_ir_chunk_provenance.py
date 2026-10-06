"""Run LearnMate chunk-boundary and page-provenance tests against a local API."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ASSESSMENT_DIRECTORY = Path(__file__).resolve().parent.parent
CORPUS_DIRECTORY = ASSESSMENT_DIRECTORY / "generated"
EVIDENCE_DIRECTORY = ASSESSMENT_DIRECTORY / "evidence" / "raw"
BASE_URL = os.getenv("LEARNMATE_ASSESSMENT_API_URL", "http://127.0.0.1:8000")


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
        cwd=ASSESSMENT_DIRECTORY.parent.parent,
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
    timeout: int = 120,
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


def upload_document(
    path: Path,
    authorization: dict[str, str],
) -> tuple[dict[str, Any], float]:
    with path.open("rb") as input_file:
        response, latency = send_request(
            "POST",
            "/documents/upload",
            headers=authorization,
            files={"file": (path.name, input_file, "application/pdf")},
        )
    body = response_json(response)
    response.raise_for_status()
    return {
        "status_code": response.status_code,
        "latency_ms": latency,
        "response": body,
    }, latency


def search_document(
    document_id: str,
    query: str,
    authorization: dict[str, str],
) -> dict[str, Any]:
    response, latency = send_request(
        "POST",
        "/documents/search",
        headers=authorization,
        json_body={"document_id": document_id, "query": query, "top_k": 3},
    )
    body = response_json(response)
    response.raise_for_status()
    return {
        "query": query,
        "status_code": response.status_code,
        "latency_ms": latency,
        "response": body,
    }


def first_rank_for_page(results: list[dict[str, Any]], page_number: int) -> int | None:
    for rank, result in enumerate(results, start=1):
        if result.get("page_number") == page_number:
            return rank
    return None


def main() -> None:
    password = os.getenv("LEARNMATE_ASSESSMENT_PASSWORD")
    if not password:
        raise SystemExit(
            "Set LEARNMATE_ASSESSMENT_PASSWORD to a temporary synthetic test password."
        )

    boundary_path = CORPUS_DIRECTORY / "ir-boundary.pdf"
    accuracy_path = CORPUS_DIRECTORY / "ir-accuracy.pdf"
    if not boundary_path.is_file() or not accuracy_path.is_file():
        raise SystemExit("Generate the controlled corpus before running these tests.")

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    test_email = f"ir-provenance-{run_stamp.lower()}@example.test"
    evidence: dict[str, Any] = {
        "run_id": run_stamp,
        "started_at": utc_now(),
        "base_url": BASE_URL,
        "git_commit": current_commit(),
        "synthetic_account": test_email,
        "secret_handling": "Password and bearer token were not recorded.",
        "inputs": [
            {"filename": boundary_path.name, "sha256": sha256(boundary_path)},
            {"filename": accuracy_path.name, "sha256": sha256(accuracy_path)},
        ],
        "tests": [],
        "cleanup": [],
    }

    authorization: dict[str, str] | None = None
    uploaded_document_ids: list[str] = []

    try:
        signup_response, signup_latency = send_request(
            "POST",
            "/auth/signup",
            json_body={
                "full_name": "IR Provenance Tester",
                "email": test_email,
                "password": password,
            },
        )
        signup_body = response_json(signup_response)
        signup_response.raise_for_status()
        authorization = {"Authorization": f"Bearer {signup_body['access_token']}"}
        evidence["signup"] = {
            "status_code": signup_response.status_code,
            "latency_ms": signup_latency,
            "user": signup_body["user"],
        }

        boundary_upload, _ = upload_document(boundary_path, authorization)
        boundary_id = boundary_upload["response"]["document"]["document_id"]
        uploaded_document_ids.append(boundary_id)
        evidence["boundary_upload"] = boundary_upload

        boundary_search = search_document(
            boundary_id,
            "What are the two paired verification phrases near the chunk boundary?",
            authorization,
        )
        boundary_results = boundary_search["response"].get("results", [])
        combined_text = " ".join(
            str(result.get("text", "")).lower() for result in boundary_results
        )
        returned_chunk_indexes = sorted(
            {int(result["chunk_index"]) for result in boundary_results}
        )
        phrases_present = all(
            phrase in combined_text
            for phrase in ("amber telescope", "silver compass")
        )
        adjacent_chunks_present = 0 in returned_chunk_indexes and 1 in returned_chunk_indexes
        correct_page_references = all(
            result.get("page_number") == 1 for result in boundary_results
        )

        evidence["tests"].append(
            {
                "test_id": "IR-04",
                "title": "Chunk-boundary evidence preservation",
                **boundary_search,
                "expected_phrases": ["amber telescope", "silver compass"],
                "returned_chunk_indexes": returned_chunk_indexes,
                "both_phrases_present": phrases_present,
                "adjacent_chunks_present": adjacent_chunks_present,
                "correct_page_references": correct_page_references,
                "outcome": "Pass"
                if phrases_present and adjacent_chunks_present and correct_page_references
                else "Fail",
            }
        )

        accuracy_upload, _ = upload_document(accuracy_path, authorization)
        accuracy_id = accuracy_upload["response"]["document"]["document_id"]
        uploaded_document_ids.append(accuracy_id)
        evidence["accuracy_upload"] = accuracy_upload

        provenance_probes = [
            {
                "label": "project codename",
                "query": "On which source page is Mercury described as the project codename?",
                "expected_page": 3,
                "expected_text": "project codename",
            },
            {
                "label": "chemical element",
                "query": "On which source page is Mercury described as the chemical element?",
                "expected_page": 4,
                "expected_text": "chemical element",
            },
        ]
        probe_results: list[dict[str, Any]] = []

        for probe in provenance_probes:
            search = search_document(accuracy_id, probe["query"], authorization)
            results = search["response"].get("results", [])
            rank = first_rank_for_page(results, probe["expected_page"])
            first_result = results[0] if results else {}
            probe_passed = (
                rank == 1
                and first_result.get("page_number") == probe["expected_page"]
                and probe["expected_text"] in str(first_result.get("text", "")).lower()
            )
            probe_results.append(
                {
                    **probe,
                    **search,
                    "actual_relevant_rank": rank,
                    "page_reference_correct": probe_passed,
                    "outcome": "Pass" if probe_passed else "Fail",
                }
            )

        correct_probes = sum(
            probe["page_reference_correct"] for probe in probe_results
        )
        evidence["tests"].append(
            {
                "test_id": "IR-05",
                "title": "Page-reference integrity",
                "probes": probe_results,
                "correct_references": correct_probes,
                "total_references_checked": len(probe_results),
                "page_reference_accuracy": round(
                    correct_probes / len(probe_results), 4
                ),
                "outcome": "Pass"
                if correct_probes == len(probe_results)
                else "Fail",
            }
        )
    finally:
        if authorization:
            for document_id in uploaded_document_ids:
                delete_response, delete_latency = send_request(
                    "DELETE",
                    f"/documents/{document_id}",
                    headers=authorization,
                )
                evidence["cleanup"].append(
                    {
                        "document_id": document_id,
                        "status_code": delete_response.status_code,
                        "latency_ms": delete_latency,
                        "response": response_json(delete_response),
                    }
                )

        evidence["finished_at"] = utc_now()
        evidence["summary"] = {
            "tests_executed": len(evidence["tests"]),
            "tests_passed": sum(
                test["outcome"] == "Pass" for test in evidence["tests"]
            ),
            "all_uploads_cleaned_up": bool(evidence["cleanup"])
            and all(item["status_code"] == 200 for item in evidence["cleanup"]),
        }

        EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        evidence_path = EVIDENCE_DIRECTORY / f"ir-chunk-provenance-{run_stamp}.json"
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(f"Evidence: {evidence_path}")
        print(json.dumps(evidence["summary"], indent=2))


if __name__ == "__main__":
    main()
