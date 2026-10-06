"""Run the first three LearnMate retrieval accuracy tests against a local API."""

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

TEST_CASES = [
    {
        "test_id": "IR-01",
        "title": "Exact-fact retrieval",
        "query": "In what year was the Orion Protocol launched?",
        "expected_page": 1,
        "pass_rank": 1,
    },
    {
        "test_id": "IR-02",
        "title": "Paraphrased semantic retrieval",
        "query": "When did the evidence-organizing initiative begin?",
        "expected_page": 1,
        "pass_rank": 3,
    },
    {
        "test_id": "IR-03",
        "title": "Acronym retrieval",
        "query": "What three activities are used by LEF?",
        "expected_page": 2,
        "pass_rank": 3,
    },
]


def utc_now() -> str:
    """Return an ISO timestamp suitable for an evidence record."""

    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    """Hash the exact uploaded file."""

    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for block in iter(lambda: input_file.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def current_commit() -> str:
    """Read the tested Git commit without changing repository state."""

    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ASSESSMENT_DIRECTORY.parent.parent,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def request_json(
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    timeout: int = 120,
) -> tuple[requests.Response, float]:
    """Send one request and measure end-to-end client-observed latency."""

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


def safe_json(response: requests.Response) -> Any:
    """Return JSON when available without hiding a non-JSON server response."""

    try:
        return response.json()
    except requests.JSONDecodeError:
        return {"non_json_body": response.text[:1000]}


def relevant_rank(results: list[dict[str, Any]], expected_page: int) -> int | None:
    """Return the one-based rank of the first result from the expected page."""

    for rank, result in enumerate(results, start=1):
        if result.get("page_number") == expected_page:
            return rank
    return None


def main() -> None:
    password = os.getenv("LEARNMATE_ASSESSMENT_PASSWORD")
    if not password:
        raise SystemExit(
            "Set LEARNMATE_ASSESSMENT_PASSWORD to a temporary synthetic test password."
        )

    corpus_path = CORPUS_DIRECTORY / "ir-accuracy.pdf"
    if not corpus_path.is_file():
        raise SystemExit(
            "Generate the controlled corpus before running the retrieval baseline."
        )

    health_response, health_latency = request_json("GET", "/health", timeout=10)
    health_response.raise_for_status()

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    test_email = f"ir-baseline-{run_stamp.lower()}@example.test"
    evidence: dict[str, Any] = {
        "run_id": run_stamp,
        "started_at": utc_now(),
        "base_url": BASE_URL,
        "git_commit": current_commit(),
        "input_filename": corpus_path.name,
        "input_sha256": sha256(corpus_path),
        "synthetic_account": test_email,
        "secret_handling": "Password and bearer token were not recorded.",
        "health_check": {
            "status_code": health_response.status_code,
            "latency_ms": health_latency,
            "response": safe_json(health_response),
        },
        "tests": [],
    }

    document_id: str | None = None
    authorization: dict[str, str] | None = None

    try:
        signup_response, signup_latency = request_json(
            "POST",
            "/auth/signup",
            json_body={
                "full_name": "IR Baseline Tester",
                "email": test_email,
                "password": password,
            },
        )
        signup_body = safe_json(signup_response)
        signup_response.raise_for_status()
        authorization = {"Authorization": f"Bearer {signup_body['access_token']}"}
        evidence["signup"] = {
            "status_code": signup_response.status_code,
            "latency_ms": signup_latency,
            "user": signup_body["user"],
        }

        with corpus_path.open("rb") as corpus_file:
            upload_response, upload_latency = request_json(
                "POST",
                "/documents/upload",
                headers=authorization,
                files={"file": (corpus_path.name, corpus_file, "application/pdf")},
            )
        upload_body = safe_json(upload_response)
        upload_response.raise_for_status()
        document_id = upload_body["document"]["document_id"]
        evidence["upload"] = {
            "status_code": upload_response.status_code,
            "latency_ms": upload_latency,
            "response": upload_body,
        }

        for test_case in TEST_CASES:
            search_response, search_latency = request_json(
                "POST",
                "/documents/search",
                headers=authorization,
                json_body={
                    "document_id": document_id,
                    "query": test_case["query"],
                    "top_k": 3,
                },
            )
            search_body = safe_json(search_response)
            search_response.raise_for_status()
            results = search_body.get("results", [])
            rank = relevant_rank(results, test_case["expected_page"])
            passed = rank is not None and rank <= test_case["pass_rank"]

            evidence["tests"].append(
                {
                    **test_case,
                    "status_code": search_response.status_code,
                    "latency_ms": search_latency,
                    "actual_relevant_rank": rank,
                    "hit_at_1": rank == 1,
                    "hit_at_3": rank is not None and rank <= 3,
                    "reciprocal_rank": round(1 / rank, 4) if rank else 0,
                    "outcome": "Pass" if passed else "Fail",
                    "response": search_body,
                }
            )
    finally:
        if document_id and authorization:
            delete_response, delete_latency = request_json(
                "DELETE",
                f"/documents/{document_id}",
                headers=authorization,
            )
            evidence["cleanup"] = {
                "status_code": delete_response.status_code,
                "latency_ms": delete_latency,
                "response": safe_json(delete_response),
            }

        evidence["finished_at"] = utc_now()
        test_results = evidence.get("tests", [])
        evidence["summary"] = {
            "tests_executed": len(test_results),
            "tests_passed": sum(test["outcome"] == "Pass" for test in test_results),
            "hit_at_1_rate": round(
                sum(test["hit_at_1"] for test in test_results) / len(test_results),
                4,
            )
            if test_results
            else 0,
            "hit_at_3_rate": round(
                sum(test["hit_at_3"] for test in test_results) / len(test_results),
                4,
            )
            if test_results
            else 0,
            "mean_reciprocal_rank": round(
                sum(test["reciprocal_rank"] for test in test_results)
                / len(test_results),
                4,
            )
            if test_results
            else 0,
        }

        EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        evidence_path = EVIDENCE_DIRECTORY / f"ir-baseline-{run_stamp}.json"
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(f"Evidence: {evidence_path}")
        print(json.dumps(evidence["summary"], indent=2))


if __name__ == "__main__":
    main()
