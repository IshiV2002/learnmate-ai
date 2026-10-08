"""Run SEC-02 cross-user semantic-search authorization checks."""

from __future__ import annotations

import hashlib
import json
import os
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests


ASSESSMENT_DIRECTORY = Path(__file__).resolve().parent.parent
CORPUS_DIRECTORY = ASSESSMENT_DIRECTORY / "generated"
EVIDENCE_DIRECTORY = ASSESSMENT_DIRECTORY / "evidence" / "raw"
BASE_URL = os.getenv("LEARNMATE_ASSESSMENT_API_URL", "http://127.0.0.1:8000")
PRIVATE_PHRASE = "violet lighthouse 731"
DENIAL_BODY = {"detail": "Document not found."}
REPETITIONS = 5


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


def signup_user(
    *,
    label: str,
    email: str,
    password: str,
) -> tuple[dict[str, str], dict[str, Any]]:
    response, latency = send_request(
        "POST",
        "/auth/signup",
        json_body={"full_name": label, "email": email, "password": password},
    )
    body = response_json(response)
    response.raise_for_status()
    authorization = {"Authorization": f"Bearer {body['access_token']}"}
    sanitized_setup = {
        "status_code": response.status_code,
        "latency_ms": latency,
        "user": body["user"],
        "access_token_recorded": False,
    }
    return authorization, sanitized_setup


def search(
    *,
    authorization: dict[str, str],
    document_id: str,
) -> tuple[requests.Response, float, Any]:
    response, latency = send_request(
        "POST",
        "/documents/search",
        headers=authorization,
        json_body={
            "document_id": document_id,
            "query": "What is the unique authorization phrase?",
            "top_k": 3,
        },
    )
    return response, latency, response_json(response)


def main() -> None:
    password = os.getenv("LEARNMATE_ASSESSMENT_PASSWORD")
    if not password:
        raise SystemExit(
            "Set LEARNMATE_ASSESSMENT_PASSWORD to a temporary synthetic password."
        )

    corpus_path = CORPUS_DIRECTORY / "user-a-private.pdf"
    if not corpus_path.is_file():
        raise SystemExit("Generate the controlled corpus before running SEC-02.")

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    user_a_email = f"sec02-user-a-{run_stamp.lower()}@example.test"
    user_b_email = f"sec02-user-b-{run_stamp.lower()}@example.test"
    evidence: dict[str, Any] = {
        "run_id": run_stamp,
        "started_at": utc_now(),
        "base_url": BASE_URL,
        "git_commit": current_commit(),
        "test_id": "SEC-02",
        "secret_handling": "Passwords and bearer tokens were not recorded.",
        "synthetic_accounts": {
            "user_a": user_a_email,
            "user_b": user_b_email,
        },
        "input_filename": corpus_path.name,
        "input_sha256": sha256(corpus_path),
        "expected_private_phrase": PRIVATE_PHRASE,
        "cleanup": [],
    }

    user_a_authorization: dict[str, str] | None = None
    user_b_authorization: dict[str, str] | None = None
    document_id: str | None = None

    try:
        user_a_authorization, user_a_setup = signup_user(
            label="SEC02 User A",
            email=user_a_email,
            password=password,
        )
        user_b_authorization, user_b_setup = signup_user(
            label="SEC02 User B",
            email=user_b_email,
            password=password,
        )
        evidence["setup_accounts"] = {
            "user_a": user_a_setup,
            "user_b": user_b_setup,
        }

        with corpus_path.open("rb") as input_file:
            upload_response, upload_latency = send_request(
                "POST",
                "/documents/upload",
                headers=user_a_authorization,
                files={"file": (corpus_path.name, input_file, "application/pdf")},
            )
        upload_body = response_json(upload_response)
        upload_response.raise_for_status()
        document_id = upload_body["document"]["document_id"]
        evidence["user_a_upload"] = {
            "status_code": upload_response.status_code,
            "latency_ms": upload_latency,
            "response": upload_body,
        }

        owner_search_response, owner_search_latency, owner_search_body = search(
            authorization=user_a_authorization,
            document_id=document_id,
        )
        owner_search_response.raise_for_status()
        owner_results = owner_search_body.get("results", [])
        owner_phrase_retrieved = any(
            PRIVATE_PHRASE in str(result.get("text", "")).lower()
            for result in owner_results
        )
        evidence["owner_search_before"] = {
            "status_code": owner_search_response.status_code,
            "latency_ms": owner_search_latency,
            "private_phrase_retrieved": owner_phrase_retrieved,
            "response": owner_search_body,
        }

        user_b_list_response, user_b_list_latency = send_request(
            "GET",
            "/documents",
            headers=user_b_authorization,
        )
        user_b_list_body = response_json(user_b_list_response)
        user_b_list_response.raise_for_status()
        user_b_list_contains_owner_document = any(
            item.get("document_id") == document_id for item in user_b_list_body
        )
        evidence["user_b_list"] = {
            "status_code": user_b_list_response.status_code,
            "latency_ms": user_b_list_latency,
            "owner_document_visible": user_b_list_contains_owner_document,
            "response": user_b_list_body,
        }

        nonexistent_document_id = str(uuid4())
        cross_user_attempts: list[dict[str, Any]] = []
        nonexistent_control_attempts: list[dict[str, Any]] = []

        for repetition in range(1, REPETITIONS + 1):
            response, latency, body = search(
                authorization=user_b_authorization,
                document_id=document_id,
            )
            cross_user_attempts.append(
                {
                    "repetition": repetition,
                    "status_code": response.status_code,
                    "latency_ms": latency,
                    "response": body,
                    "private_phrase_disclosed": PRIVATE_PHRASE in json.dumps(body).lower(),
                }
            )

            response, latency, body = search(
                authorization=user_b_authorization,
                document_id=nonexistent_document_id,
            )
            nonexistent_control_attempts.append(
                {
                    "repetition": repetition,
                    "status_code": response.status_code,
                    "latency_ms": latency,
                    "response": body,
                    "private_phrase_disclosed": PRIVATE_PHRASE in json.dumps(body).lower(),
                }
            )

        cross_user_denials_consistent = all(
            attempt["status_code"] == 404
            and attempt["response"] == DENIAL_BODY
            and not attempt["private_phrase_disclosed"]
            for attempt in cross_user_attempts
        )
        controls_consistent = all(
            attempt["status_code"] == 404
            and attempt["response"] == DENIAL_BODY
            and not attempt["private_phrase_disclosed"]
            for attempt in nonexistent_control_attempts
        )
        response_indistinguishable = all(
            cross_user_attempt["status_code"] == control_attempt["status_code"]
            and cross_user_attempt["response"] == control_attempt["response"]
            for cross_user_attempt, control_attempt in zip(
                cross_user_attempts, nonexistent_control_attempts, strict=True
            )
        )
        cross_user_latencies = [
            attempt["latency_ms"] for attempt in cross_user_attempts
        ]
        control_latencies = [
            attempt["latency_ms"] for attempt in nonexistent_control_attempts
        ]
        evidence["user_b_search_attempts"] = {
            "known_owner_document": cross_user_attempts,
            "nonexistent_document_control": nonexistent_control_attempts,
            "known_document_median_latency_ms": round(
                statistics.median(cross_user_latencies), 2
            ),
            "nonexistent_control_median_latency_ms": round(
                statistics.median(control_latencies), 2
            ),
            "status_and_body_indistinguishable": response_indistinguishable,
            "cross_document_leakage_count": sum(
                attempt["private_phrase_disclosed"]
                for attempt in cross_user_attempts
            ),
        }

        owner_after_response, owner_after_latency, owner_after_body = search(
            authorization=user_a_authorization,
            document_id=document_id,
        )
        owner_after_response.raise_for_status()
        owner_access_preserved = any(
            PRIVATE_PHRASE in str(result.get("text", "")).lower()
            for result in owner_after_body.get("results", [])
        )
        evidence["owner_search_after"] = {
            "status_code": owner_after_response.status_code,
            "latency_ms": owner_after_latency,
            "private_phrase_retrieved": owner_access_preserved,
            "response": owner_after_body,
        }

        evidence["summary"] = {
            "owner_search_before_passed": owner_phrase_retrieved,
            "user_b_list_isolated": not user_b_list_contains_owner_document,
            "cross_user_attempts_denied": cross_user_denials_consistent,
            "nonexistent_controls_denied": controls_consistent,
            "status_and_body_indistinguishable": response_indistinguishable,
            "cross_document_leakage_count": sum(
                attempt["private_phrase_disclosed"]
                for attempt in cross_user_attempts
            ),
            "owner_access_preserved": owner_access_preserved,
            "outcome": (
                "Pass"
                if owner_phrase_retrieved
                and not user_b_list_contains_owner_document
                and cross_user_denials_consistent
                and controls_consistent
                and response_indistinguishable
                and owner_access_preserved
                else "Fail"
            ),
        }
    finally:
        if user_a_authorization and document_id:
            delete_response, delete_latency = send_request(
                "DELETE",
                f"/documents/{document_id}",
                headers=user_a_authorization,
            )
            evidence["cleanup"].append(
                {
                    "resource": "user_a_document",
                    "resource_id": document_id,
                    "status_code": delete_response.status_code,
                    "latency_ms": delete_latency,
                    "response": response_json(delete_response),
                }
            )

        evidence["finished_at"] = utc_now()
        evidence["cleanup_succeeded"] = bool(evidence["cleanup"]) and all(
            item["status_code"] == 200 for item in evidence["cleanup"]
        )
        if evidence.get("summary") and not evidence["cleanup_succeeded"]:
            evidence["summary"]["outcome"] = "Fail"

        EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        evidence_path = EVIDENCE_DIRECTORY / f"sec-cross-user-search-{run_stamp}.json"
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(f"Evidence: {evidence_path}")
        print(json.dumps(evidence.get("summary", {}), indent=2))
        print(f"Cleanup succeeded: {evidence['cleanup_succeeded']}")


if __name__ == "__main__":
    main()
