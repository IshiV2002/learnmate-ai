"""Run SEC-03 cross-user metadata and deletion authorization checks."""

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
from uuid import uuid4

import requests


ASSESSMENT_DIRECTORY = Path(__file__).resolve().parent.parent
REPOSITORY_DIRECTORY = ASSESSMENT_DIRECTORY.parent.parent
BACKEND_DIRECTORY = REPOSITORY_DIRECTORY / "backend"
CORPUS_DIRECTORY = ASSESSMENT_DIRECTORY / "generated"
EVIDENCE_DIRECTORY = ASSESSMENT_DIRECTORY / "evidence" / "raw"
BASE_URL = os.getenv("LEARNMATE_ASSESSMENT_API_URL", "http://127.0.0.1:8000")
PRIVATE_PHRASE = "violet lighthouse 731"
DENIAL_BODY = {"detail": "Document not found."}

sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.core.config import UPLOAD_DIRECTORY  # noqa: E402
from app.database.database import get_application_database  # noqa: E402


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


def signup_user(
    *,
    label: str,
    email: str,
    password: str,
) -> tuple[dict[str, str], str, dict[str, Any]]:
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
    return authorization, body["user"]["user_id"], sanitized_setup


def inspect_owner_storage(
    *,
    document_id: str,
    user_id: str,
    expected_hash: str,
) -> dict[str, bool]:
    """Record safe booleans without exposing the internal UUID filename."""
    record = get_application_database().get_document(document_id, user_id)
    if record is None:
        return {
            "metadata_exists": False,
            "stored_file_exists": False,
            "stored_file_hash_matches_input": False,
        }

    upload_directory = UPLOAD_DIRECTORY.resolve()
    stored_path = (upload_directory / record.stored_filename).resolve()
    inside_upload_directory = stored_path.parent == upload_directory
    stored_file_exists = inside_upload_directory and stored_path.is_file()
    return {
        "metadata_exists": True,
        "stored_file_exists": stored_file_exists,
        "stored_file_hash_matches_input": (
            stored_file_exists and sha256(stored_path) == expected_hash
        ),
    }


def main() -> None:
    password = os.getenv("LEARNMATE_ASSESSMENT_PASSWORD")
    if not password:
        raise SystemExit(
            "Set LEARNMATE_ASSESSMENT_PASSWORD to a temporary synthetic password."
        )

    corpus_path = CORPUS_DIRECTORY / "user-a-private.pdf"
    if not corpus_path.is_file():
        raise SystemExit("Generate the controlled corpus before running SEC-03.")
    input_hash = sha256(corpus_path)

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    user_a_email = f"sec03-user-a-{run_stamp.lower()}@example.test"
    user_b_email = f"sec03-user-b-{run_stamp.lower()}@example.test"
    evidence: dict[str, Any] = {
        "run_id": run_stamp,
        "started_at": utc_now(),
        "base_url": BASE_URL,
        "git_commit": current_commit(),
        "test_id": "SEC-03",
        "secret_handling": (
            "Passwords, bearer tokens, and internal stored filenames were not recorded."
        ),
        "synthetic_accounts": {
            "user_a": user_a_email,
            "user_b": user_b_email,
        },
        "input_filename": corpus_path.name,
        "input_sha256": input_hash,
        "expected_private_phrase": PRIVATE_PHRASE,
        "cleanup": [],
    }

    user_a_authorization: dict[str, str] | None = None
    user_b_authorization: dict[str, str] | None = None
    user_a_id: str | None = None
    document_id: str | None = None
    stored_path_for_cleanup_check: Path | None = None

    try:
        user_a_authorization, user_a_id, user_a_setup = signup_user(
            label="SEC03 User A",
            email=user_a_email,
            password=password,
        )
        user_b_authorization, _, user_b_setup = signup_user(
            label="SEC03 User B",
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
        record = get_application_database().get_document(document_id, user_a_id)
        if record is not None:
            stored_path_for_cleanup_check = (
                UPLOAD_DIRECTORY.resolve() / record.stored_filename
            ).resolve()
        evidence["user_a_upload"] = {
            "status_code": upload_response.status_code,
            "latency_ms": upload_latency,
            "response": upload_body,
        }

        owner_get_response, owner_get_latency = send_request(
            "GET",
            f"/documents/{document_id}",
            headers=user_a_authorization,
        )
        owner_get_body = response_json(owner_get_response)
        owner_get_response.raise_for_status()
        owner_storage_before = inspect_owner_storage(
            document_id=document_id,
            user_id=user_a_id,
            expected_hash=input_hash,
        )
        evidence["owner_before"] = {
            "get_status_code": owner_get_response.status_code,
            "get_latency_ms": owner_get_latency,
            "metadata_response": owner_get_body,
            "storage": owner_storage_before,
        }

        user_b_list_response, user_b_list_latency = send_request(
            "GET",
            "/documents",
            headers=user_b_authorization,
        )
        user_b_list_body = response_json(user_b_list_response)
        user_b_list_response.raise_for_status()
        user_b_list_isolated = not any(
            item.get("document_id") == document_id for item in user_b_list_body
        )

        nonexistent_document_id = str(uuid4())
        user_b_get_response, user_b_get_latency = send_request(
            "GET",
            f"/documents/{document_id}",
            headers=user_b_authorization,
        )
        user_b_get_body = response_json(user_b_get_response)
        control_get_response, control_get_latency = send_request(
            "GET",
            f"/documents/{nonexistent_document_id}",
            headers=user_b_authorization,
        )
        control_get_body = response_json(control_get_response)

        user_b_delete_response, user_b_delete_latency = send_request(
            "DELETE",
            f"/documents/{document_id}",
            headers=user_b_authorization,
        )
        user_b_delete_body = response_json(user_b_delete_response)
        control_delete_response, control_delete_latency = send_request(
            "DELETE",
            f"/documents/{nonexistent_document_id}",
            headers=user_b_authorization,
        )
        control_delete_body = response_json(control_delete_response)

        evidence["user_b_attempts"] = {
            "list": {
                "status_code": user_b_list_response.status_code,
                "latency_ms": user_b_list_latency,
                "owner_document_visible": not user_b_list_isolated,
                "response": user_b_list_body,
            },
            "get_owner_document": {
                "status_code": user_b_get_response.status_code,
                "latency_ms": user_b_get_latency,
                "response": user_b_get_body,
                "private_phrase_disclosed": (
                    PRIVATE_PHRASE in json.dumps(user_b_get_body).lower()
                ),
            },
            "get_nonexistent_control": {
                "status_code": control_get_response.status_code,
                "latency_ms": control_get_latency,
                "response": control_get_body,
            },
            "delete_owner_document": {
                "status_code": user_b_delete_response.status_code,
                "latency_ms": user_b_delete_latency,
                "response": user_b_delete_body,
                "private_phrase_disclosed": (
                    PRIVATE_PHRASE in json.dumps(user_b_delete_body).lower()
                ),
            },
            "delete_nonexistent_control": {
                "status_code": control_delete_response.status_code,
                "latency_ms": control_delete_latency,
                "response": control_delete_body,
            },
        }

        owner_get_after_response, owner_get_after_latency = send_request(
            "GET",
            f"/documents/{document_id}",
            headers=user_a_authorization,
        )
        owner_get_after_body = response_json(owner_get_after_response)

        owner_search_after_response, owner_search_after_latency = send_request(
            "POST",
            "/documents/search",
            headers=user_a_authorization,
            json_body={
                "document_id": document_id,
                "query": "What is the unique authorization phrase?",
                "top_k": 3,
            },
        )
        owner_search_after_body = response_json(owner_search_after_response)
        owner_phrase_retrieved = any(
            PRIVATE_PHRASE in str(result.get("text", "")).lower()
            for result in owner_search_after_body.get("results", [])
        )
        owner_storage_after = inspect_owner_storage(
            document_id=document_id,
            user_id=user_a_id,
            expected_hash=input_hash,
        )
        evidence["owner_after_user_b_attempts"] = {
            "get_status_code": owner_get_after_response.status_code,
            "get_latency_ms": owner_get_after_latency,
            "metadata_response": owner_get_after_body,
            "search_status_code": owner_search_after_response.status_code,
            "search_latency_ms": owner_search_after_latency,
            "private_phrase_retrieved": owner_phrase_retrieved,
            "storage": owner_storage_after,
        }

        get_indistinguishable = (
            user_b_get_response.status_code == control_get_response.status_code == 404
            and user_b_get_body == control_get_body == DENIAL_BODY
        )
        delete_indistinguishable = (
            user_b_delete_response.status_code
            == control_delete_response.status_code
            == 404
            and user_b_delete_body == control_delete_body == DENIAL_BODY
        )
        storage_preserved = all(owner_storage_after.values())
        evidence["summary"] = {
            "owner_metadata_available_before": owner_get_response.status_code == 200,
            "user_b_list_isolated": user_b_list_isolated,
            "cross_user_get_denied": user_b_get_response.status_code == 404,
            "cross_user_delete_denied": user_b_delete_response.status_code == 404,
            "get_response_indistinguishable": get_indistinguishable,
            "delete_response_indistinguishable": delete_indistinguishable,
            "private_metadata_or_phrase_leakage_count": sum(
                (
                    PRIVATE_PHRASE in json.dumps(user_b_get_body).lower(),
                    PRIVATE_PHRASE in json.dumps(user_b_delete_body).lower(),
                    not user_b_list_isolated,
                )
            ),
            "owner_metadata_preserved": owner_get_after_response.status_code == 200,
            "owner_vector_search_preserved": (
                owner_search_after_response.status_code == 200
                and owner_phrase_retrieved
            ),
            "owner_database_and_file_preserved": storage_preserved,
            "outcome": (
                "Pass"
                if owner_get_response.status_code == 200
                and user_b_list_isolated
                and get_indistinguishable
                and delete_indistinguishable
                and owner_get_after_response.status_code == 200
                and owner_search_after_response.status_code == 200
                and owner_phrase_retrieved
                and storage_preserved
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

        evidence["post_cleanup"] = {
            "metadata_removed": bool(
                document_id
                and user_a_id
                and get_application_database().get_document(document_id, user_a_id)
                is None
            ),
            "stored_file_removed": bool(
                stored_path_for_cleanup_check
                and not stored_path_for_cleanup_check.exists()
            ),
        }
        evidence["finished_at"] = utc_now()
        evidence["cleanup_succeeded"] = (
            bool(evidence["cleanup"])
            and all(item["status_code"] == 200 for item in evidence["cleanup"])
            and all(evidence["post_cleanup"].values())
        )
        if evidence.get("summary") and not evidence["cleanup_succeeded"]:
            evidence["summary"]["outcome"] = "Fail"

        EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        evidence_path = (
            EVIDENCE_DIRECTORY / f"sec-cross-user-management-{run_stamp}.json"
        )
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(f"Evidence: {evidence_path}")
        print(json.dumps(evidence.get("summary", {}), indent=2))
        print(f"Cleanup succeeded: {evidence['cleanup_succeeded']}")


if __name__ == "__main__":
    main()
