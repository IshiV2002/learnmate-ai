"""Run irrelevant-query and keyword-stuffing tests against the local API."""

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
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    return response, latency_ms


def response_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except requests.JSONDecodeError:
        return {"non_json_body": response.text[:1000]}


def upload_document(
    path: Path,
    authorization: dict[str, str],
) -> dict[str, Any]:
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
    }


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


def rank_for_page(results: list[dict[str, Any]], page_number: int) -> int | None:
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

    accuracy_path = CORPUS_DIRECTORY / "ir-accuracy.pdf"
    manipulation_path = CORPUS_DIRECTORY / "ir-manipulation.pdf"
    if not accuracy_path.is_file() or not manipulation_path.is_file():
        raise SystemExit("Generate the controlled corpus before running these tests.")

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    test_email = f"ir-manipulation-{run_stamp.lower()}@example.test"
    evidence: dict[str, Any] = {
        "run_id": run_stamp,
        "started_at": utc_now(),
        "base_url": BASE_URL,
        "git_commit": current_commit(),
        "synthetic_account": test_email,
        "secret_handling": "Password and bearer token were not recorded.",
        "inputs": [
            {"filename": accuracy_path.name, "sha256": sha256(accuracy_path)},
            {
                "filename": manipulation_path.name,
                "sha256": sha256(manipulation_path),
            },
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
                "full_name": "IR Manipulation Tester",
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

        accuracy_upload = upload_document(accuracy_path, authorization)
        accuracy_id = accuracy_upload["response"]["document"]["document_id"]
        uploaded_document_ids.append(accuracy_id)
        evidence["accuracy_upload"] = accuracy_upload

        irrelevant_search = search_document(
            accuracy_id,
            "At what temperature and for how long should sourdough bread bake?",
            authorization,
        )
        irrelevant_results = irrelevant_search["response"].get("results", [])
        evidence["tests"].append(
            {
                "test_id": "IR-06",
                "title": "Irrelevant query handling",
                **irrelevant_search,
                "ground_truth": (
                    "The controlled document contains no cooking, bread, temperature, "
                    "or baking information."
                ),
                "irrelevant_results_returned": len(irrelevant_results),
                "pass_criterion": "No retrieval results are returned.",
                "outcome": "Pass" if len(irrelevant_results) == 0 else "Fail",
            }
        )

        manipulation_upload = upload_document(manipulation_path, authorization)
        manipulation_id = manipulation_upload["response"]["document"]["document_id"]
        uploaded_document_ids.append(manipulation_id)
        evidence["manipulation_upload"] = manipulation_upload

        manipulation_search = search_document(
            manipulation_id,
            "Explain how photosynthesis uses chlorophyll and sunlight to convert energy.",
            authorization,
        )
        manipulation_results = manipulation_search["response"].get("results", [])
        factual_rank = rank_for_page(manipulation_results, 1)
        stuffed_rank = rank_for_page(manipulation_results, 2)
        passed_manipulation_test = (
            factual_rank == 1
            and stuffed_rank is not None
            and factual_rank < stuffed_rank
        )
        evidence["tests"].append(
            {
                "test_id": "IR-07",
                "title": "Keyword-stuffing manipulation",
                **manipulation_search,
                "expected_factual_page": 1,
                "keyword_stuffed_page": 2,
                "factual_page_rank": factual_rank,
                "keyword_stuffed_page_rank": stuffed_rank,
                "pass_criterion": (
                    "The factual page is rank 1 and outranks the keyword-stuffed page."
                ),
                "outcome": "Pass" if passed_manipulation_test else "Fail",
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
            "tests_failed": sum(
                test["outcome"] == "Fail" for test in evidence["tests"]
            ),
            "all_uploads_cleaned_up": bool(evidence["cleanup"])
            and all(item["status_code"] == 200 for item in evidence["cleanup"]),
        }

        EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        evidence_path = (
            EVIDENCE_DIRECTORY / f"ir-relevance-manipulation-{run_stamp}.json"
        )
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(f"Evidence: {evidence_path}")
        print(json.dumps(evidence["summary"], indent=2))


if __name__ == "__main__":
    main()
