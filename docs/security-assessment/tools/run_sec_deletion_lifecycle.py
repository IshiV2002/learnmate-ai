"""Run SEC-10 deletion lifecycle and post-deletion access checks."""

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


def request_record(response: requests.Response, latency: float) -> dict[str, Any]:
    return {
        "status_code": response.status_code,
        "latency_ms": latency,
        "response": response_json(response),
    }


def main() -> None:
    password = os.getenv("LEARNMATE_ASSESSMENT_PASSWORD")
    if not password:
        raise SystemExit(
            "Set LEARNMATE_ASSESSMENT_PASSWORD to a temporary synthetic password."
        )

    source_path = CORPUS_DIRECTORY / "ir-accuracy.pdf"
    if not source_path.is_file():
        raise SystemExit("Generate the controlled corpus before running SEC-10.")

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    test_email = f"sec10-delete-{run_stamp.lower()}@example.test"
    evidence: dict[str, Any] = {
        "run_id": run_stamp,
        "started_at": utc_now(),
        "base_url": BASE_URL,
        "git_commit": current_commit(),
        "test_id": "SEC-10",
        "synthetic_account": test_email,
        "secret_handling": (
            "Password, bearer token, stored filename, and local path were not "
            "recorded."
        ),
        "cleanup": [],
    }

    vector_store = VectorStoreService()
    database = get_application_database()
    authorization: dict[str, str] | None = None
    user_id: str | None = None
    document_id: str | None = None
    stored_path: Path | None = None
    initial_state: dict[str, int | set[Path]] | None = None
    authorized_delete_succeeded = False

    try:
        signup_response, signup_latency = send_request(
            "POST",
            "/auth/signup",
            json_body={
                "full_name": "SEC10 Deletion Tester",
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
                        "sec10-deletion-source.pdf",
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

        record_before = database.get_document(document_id, user_id)
        if record_before is None:
            raise RuntimeError("Uploaded document metadata was not found.")
        stored_path = (UPLOAD_DIRECTORY.resolve() / record_before.stored_filename).resolve()
        if stored_path.parent != UPLOAD_DIRECTORY.resolve():
            raise RuntimeError("Stored test file resolved outside the upload directory.")

        get_before_response, get_before_latency = send_request(
            "GET",
            f"/documents/{document_id}",
            headers=authorization,
        )
        search_before_response, search_before_latency = send_request(
            "POST",
            "/documents/search",
            headers=authorization,
            json_body={
                "document_id": document_id,
                "query": "What year was the Orion Protocol created?",
                "top_k": 3,
            },
        )
        search_before_body = response_json(search_before_response)
        chunks_before = vector_store.count_document_chunks(document_id)
        evidence["before_delete"] = {
            "get": request_record(get_before_response, get_before_latency),
            "search": {
                "status_code": search_before_response.status_code,
                "latency_ms": search_before_latency,
                "result_count": len(search_before_body.get("results", [])),
                "expected_phrase_present": "2019"
                in json.dumps(search_before_body),
            },
            "sqlite_metadata_present": record_before is not None,
            "stored_file_present": stored_path.is_file(),
            "stored_file_matches_source_hash": (
                stored_path.is_file() and sha256(stored_path) == sha256(source_path)
            ),
            "document_chroma_chunk_count": chunks_before,
            "all_representations_present": (
                get_before_response.status_code == 200
                and search_before_response.status_code == 200
                and record_before is not None
                and stored_path.is_file()
                and chunks_before > 0
            ),
        }

        delete_response, delete_latency = send_request(
            "DELETE",
            f"/documents/{document_id}",
            headers=authorization,
        )
        authorized_delete_succeeded = delete_response.status_code == 200
        evidence["authorized_delete"] = request_record(
            delete_response,
            delete_latency,
        )

        nonexistent_id = str(uuid4())
        get_after_response, get_after_latency = send_request(
            "GET",
            f"/documents/{document_id}",
            headers=authorization,
        )
        get_control_response, get_control_latency = send_request(
            "GET",
            f"/documents/{nonexistent_id}",
            headers=authorization,
        )
        search_after_response, search_after_latency = send_request(
            "POST",
            "/documents/search",
            headers=authorization,
            json_body={
                "document_id": document_id,
                "query": "What year was the Orion Protocol created?",
                "top_k": 3,
            },
        )
        search_control_response, search_control_latency = send_request(
            "POST",
            "/documents/search",
            headers=authorization,
            json_body={
                "document_id": nonexistent_id,
                "query": "What year was the Orion Protocol created?",
                "top_k": 3,
            },
        )
        delete_again_response, delete_again_latency = send_request(
            "DELETE",
            f"/documents/{document_id}",
            headers=authorization,
        )
        delete_control_response, delete_control_latency = send_request(
            "DELETE",
            f"/documents/{nonexistent_id}",
            headers=authorization,
        )
        list_response, list_latency = send_request(
            "GET",
            "/documents",
            headers=authorization,
        )

        record_after = database.get_document(document_id, user_id)
        chunks_after = vector_store.count_document_chunks(document_id)
        final_state = state_snapshot(user_id, vector_store)
        health_after = service_health()

        get_after_body = response_json(get_after_response)
        get_control_body = response_json(get_control_response)
        search_after_body = response_json(search_after_response)
        search_control_body = response_json(search_control_response)
        delete_again_body = response_json(delete_again_response)
        delete_control_body = response_json(delete_control_response)
        list_body = response_json(list_response)
        combined_post_delete_body = json.dumps(
            {
                "get": get_after_body,
                "search": search_after_body,
                "delete": delete_again_body,
                "list": list_body,
            }
        ).lower()

        evidence["after_delete"] = {
            "get_deleted": request_record(get_after_response, get_after_latency),
            "get_nonexistent_control": request_record(
                get_control_response,
                get_control_latency,
            ),
            "get_matches_nonexistent_control": (
                get_after_response.status_code == get_control_response.status_code
                and get_after_body == get_control_body
            ),
            "search_deleted": request_record(
                search_after_response,
                search_after_latency,
            ),
            "search_nonexistent_control": request_record(
                search_control_response,
                search_control_latency,
            ),
            "search_matches_nonexistent_control": (
                search_after_response.status_code
                == search_control_response.status_code
                and search_after_body == search_control_body
            ),
            "delete_again": request_record(
                delete_again_response,
                delete_again_latency,
            ),
            "delete_nonexistent_control": request_record(
                delete_control_response,
                delete_control_latency,
            ),
            "delete_matches_nonexistent_control": (
                delete_again_response.status_code
                == delete_control_response.status_code
                and delete_again_body == delete_control_body
            ),
            "list": {
                "status_code": list_response.status_code,
                "latency_ms": list_latency,
                "document_count": len(list_body) if isinstance(list_body, list) else None,
                "deleted_document_absent": (
                    isinstance(list_body, list)
                    and all(
                        item.get("document_id") != document_id
                        for item in list_body
                        if isinstance(item, dict)
                    )
                ),
            },
            "sqlite_metadata_absent": record_after is None,
            "stored_file_absent": not stored_path.exists(),
            "document_chroma_chunk_count": chunks_after,
            "private_phrase_absent_from_post_delete_responses": (
                "orion protocol" not in combined_post_delete_body
                and "2019" not in combined_post_delete_body
            ),
            "state_returned_to_initial_baseline": state_matches(
                final_state,
                initial_state,
            ),
            "service_healthy": health_after["healthy"],
        }

        all_post_delete_denials = all(
            response.status_code == 404
            for response in (
                get_after_response,
                search_after_response,
                delete_again_response,
            )
        )
        controls_match = all(
            (
                evidence["after_delete"]["get_matches_nonexistent_control"],
                evidence["after_delete"]["search_matches_nonexistent_control"],
                evidence["after_delete"]["delete_matches_nonexistent_control"],
            )
        )
        all_representations_removed = (
            record_after is None
            and not stored_path.exists()
            and chunks_after == 0
            and evidence["after_delete"]["list"]["deleted_document_absent"]
        )
        evidence["summary"] = {
            "all_representations_present_before_delete": evidence["before_delete"][
                "all_representations_present"
            ],
            "authorized_delete_status": delete_response.status_code,
            "all_post_delete_operations_returned_404": all_post_delete_denials,
            "deleted_and_nonexistent_responses_match": controls_match,
            "all_representations_removed": all_representations_removed,
            "private_content_absent_after_delete": evidence["after_delete"][
                "private_phrase_absent_from_post_delete_responses"
            ],
            "state_returned_to_initial_baseline": state_matches(
                final_state,
                initial_state,
            ),
            "service_healthy_after_test": health_after["healthy"],
            "outcome": (
                "Pass"
                if evidence["before_delete"]["all_representations_present"]
                and authorized_delete_succeeded
                and all_post_delete_denials
                and controls_match
                and all_representations_removed
                and evidence["after_delete"][
                    "private_phrase_absent_from_post_delete_responses"
                ]
                and state_matches(final_state, initial_state)
                and health_after["healthy"]
                else "Fail"
            ),
        }
    finally:
        # This is only a recovery path if the deletion under test did not finish.
        if authorization and document_id and not authorized_delete_succeeded:
            response, latency = send_request(
                "DELETE",
                f"/documents/{document_id}",
                headers=authorization,
            )
            evidence["cleanup"].append(
                {
                    "resource": "recovery_document_delete",
                    "resource_id": document_id,
                    "status_code": response.status_code,
                    "latency_ms": latency,
                    "response": response_json(response),
                }
            )

        if user_id and initial_state:
            post_cleanup_state = state_snapshot(user_id, vector_store)
            evidence["post_cleanup"] = public_snapshot(post_cleanup_state)
            evidence["post_cleanup"]["returned_to_initial_state"] = state_matches(
                post_cleanup_state,
                initial_state,
            )
        else:
            evidence["post_cleanup"] = {"returned_to_initial_state": False}

        evidence["health_after_cleanup"] = service_health()
        evidence["finished_at"] = utc_now()
        evidence["cleanup_succeeded"] = (
            bool(evidence["post_cleanup"].get("returned_to_initial_state"))
            and bool(evidence["health_after_cleanup"]["healthy"])
        )

        EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        evidence_path = EVIDENCE_DIRECTORY / f"sec-deletion-lifecycle-{run_stamp}.json"
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(f"Evidence: {evidence_path}")
        print(json.dumps(evidence.get("summary", {}), indent=2))
        print(f"Cleanup succeeded: {evidence['cleanup_succeeded']}")


if __name__ == "__main__":
    main()
