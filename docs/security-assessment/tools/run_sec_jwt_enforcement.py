"""Run SEC-01 JWT enforcement checks against all document operations.

The runner never writes bearer tokens, passwords, or the assessment signing
secret to its evidence file. It records token-case labels only.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jwt
import requests


ASSESSMENT_DIRECTORY = Path(__file__).resolve().parent.parent
CORPUS_DIRECTORY = ASSESSMENT_DIRECTORY / "generated"
EVIDENCE_DIRECTORY = ASSESSMENT_DIRECTORY / "evidence" / "raw"
BASE_URL = os.getenv("LEARNMATE_ASSESSMENT_API_URL", "http://127.0.0.1:8000")
GENERIC_AUTHENTICATION_MESSAGE = "The login session is invalid or has expired."


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


def tamper_token(token: str) -> str:
    """Change a significant signature character while preserving JWT shape.

    The final Base64URL character can contain unused padding bits, so changing
    it does not always change the decoded signature bytes. Changing the first
    signature character reliably changes signed data.
    """
    header, payload, signature = token.split(".")
    replacement = "A" if signature[0] != "A" else "B"
    return f"{header}.{payload}.{replacement}{signature[1:]}"


def create_expired_token(user_id: str, signing_secret: str) -> str:
    """Create a correctly signed token whose expiry is already in the past."""
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": user_id,
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        },
        signing_secret,
        algorithm="HS256",
    )


def sanitized_case_result(
    *,
    token_case: str,
    operation: str,
    method: str,
    path: str,
    response: requests.Response,
    latency_ms: float,
) -> dict[str, Any]:
    body = response_json(response)
    generic_message = body == {"detail": GENERIC_AUTHENTICATION_MESSAGE}
    bearer_challenge = response.headers.get("WWW-Authenticate") == "Bearer"
    body_text = json.dumps(body).lower()
    no_internal_details = not any(
        marker in body_text
        for marker in (
            "traceback",
            "sqlite",
            "chroma",
            "jwt_secret",
            "signature verification failed",
        )
    )
    passed = (
        response.status_code == 401
        and generic_message
        and bearer_challenge
        and no_internal_details
    )
    return {
        "token_case": token_case,
        "token_recorded": False,
        "operation": operation,
        "method": method,
        "path_template": path,
        "status_code": response.status_code,
        "latency_ms": latency_ms,
        "www_authenticate": response.headers.get("WWW-Authenticate"),
        "generic_message": generic_message,
        "no_internal_details": no_internal_details,
        "response": body,
        "outcome": "Pass" if passed else "Fail",
    }


def main() -> None:
    password = os.getenv("LEARNMATE_ASSESSMENT_PASSWORD")
    signing_secret = os.getenv("LEARNMATE_ASSESSMENT_JWT_SECRET")
    if not password:
        raise SystemExit(
            "Set LEARNMATE_ASSESSMENT_PASSWORD to a temporary synthetic password."
        )
    if not signing_secret or len(signing_secret) < 32:
        raise SystemExit(
            "Set LEARNMATE_ASSESSMENT_JWT_SECRET to the same test-only secret "
            "used by the local assessment backend."
        )

    corpus_path = CORPUS_DIRECTORY / "ir-accuracy.pdf"
    if not corpus_path.is_file():
        raise SystemExit("Generate the controlled corpus before running SEC-01.")

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    test_email = f"sec-jwt-{run_stamp.lower()}@example.test"
    evidence: dict[str, Any] = {
        "run_id": run_stamp,
        "started_at": utc_now(),
        "base_url": BASE_URL,
        "git_commit": current_commit(),
        "synthetic_account": test_email,
        "secret_handling": (
            "Password, valid JWT, invalid JWT values, and signing secret were "
            "not recorded."
        ),
        "input_filename": corpus_path.name,
        "input_sha256": sha256(corpus_path),
        "test_id": "SEC-01",
        "cases": [],
        "cleanup": [],
    }

    valid_authorization: dict[str, str] | None = None
    document_id: str | None = None
    unexpected_document_ids: list[str] = []

    try:
        signup_response, signup_latency = send_request(
            "POST",
            "/auth/signup",
            json_body={
                "full_name": "SEC JWT Tester",
                "email": test_email,
                "password": password,
            },
        )
        signup_body = response_json(signup_response)
        signup_response.raise_for_status()
        valid_token = signup_body["access_token"]
        user_id = signup_body["user"]["user_id"]
        valid_authorization = {"Authorization": f"Bearer {valid_token}"}
        evidence["setup_signup"] = {
            "status_code": signup_response.status_code,
            "latency_ms": signup_latency,
            "user": signup_body["user"],
            "access_token_recorded": False,
        }

        with corpus_path.open("rb") as input_file:
            upload_response, upload_latency = send_request(
                "POST",
                "/documents/upload",
                headers=valid_authorization,
                files={"file": (corpus_path.name, input_file, "application/pdf")},
            )
        upload_body = response_json(upload_response)
        upload_response.raise_for_status()
        document_id = upload_body["document"]["document_id"]
        evidence["setup_upload"] = {
            "status_code": upload_response.status_code,
            "latency_ms": upload_latency,
            "document": upload_body["document"],
        }

        token_cases: list[tuple[str, dict[str, str] | None]] = [
            ("missing", None),
            ("malformed", {"Authorization": "Bearer not-a-valid-jwt"}),
            (
                "tampered_signature",
                {"Authorization": f"Bearer {tamper_token(valid_token)}"},
            ),
            (
                "expired",
                {
                    "Authorization": (
                        "Bearer " + create_expired_token(user_id, signing_secret)
                    )
                },
            ),
        ]

        for token_case, invalid_headers in token_cases:
            operations = [
                ("list", "GET", "/documents", None),
                ("get", "GET", f"/documents/{document_id}", None),
                (
                    "search",
                    "POST",
                    "/documents/search",
                    {
                        "document_id": document_id,
                        "query": "When was the Orion Protocol launched?",
                        "top_k": 1,
                    },
                ),
                ("delete", "DELETE", f"/documents/{document_id}", None),
            ]

            for operation, method, path, json_body in operations:
                response, latency = send_request(
                    method,
                    path,
                    headers=invalid_headers,
                    json_body=json_body,
                )
                evidence["cases"].append(
                    sanitized_case_result(
                        token_case=token_case,
                        operation=operation,
                        method=method,
                        path=(
                            "/documents/{document_id}"
                            if document_id in path
                            else path
                        ),
                        response=response,
                        latency_ms=latency,
                    )
                )

            with corpus_path.open("rb") as input_file:
                response, latency = send_request(
                    "POST",
                    "/documents/upload",
                    headers=invalid_headers,
                    files={
                        "file": (
                            corpus_path.name,
                            input_file,
                            "application/pdf",
                        )
                    },
                )
            evidence["cases"].append(
                sanitized_case_result(
                    token_case=token_case,
                    operation="upload",
                    method="POST",
                    path="/documents/upload",
                    response=response,
                    latency_ms=latency,
                )
            )
            upload_body = response_json(response)
            if response.status_code == 201 and isinstance(upload_body, dict):
                unexpected_document = upload_body.get("document", {})
                unexpected_document_id = unexpected_document.get("document_id")
                if isinstance(unexpected_document_id, str):
                    unexpected_document_ids.append(unexpected_document_id)

        list_response, list_latency = send_request(
            "GET",
            "/documents",
            headers=valid_authorization,
        )
        list_body = response_json(list_response)
        list_response.raise_for_status()
        owner_document_still_present = any(
            item.get("document_id") == document_id for item in list_body
        )

        search_response, search_latency = send_request(
            "POST",
            "/documents/search",
            headers=valid_authorization,
            json_body={
                "document_id": document_id,
                "query": "When was the Orion Protocol launched?",
                "top_k": 1,
            },
        )
        search_body = response_json(search_response)
        search_response.raise_for_status()
        owner_search_still_works = bool(search_body.get("results"))
        evidence["postcondition"] = {
            "owner_list_status_code": list_response.status_code,
            "owner_list_latency_ms": list_latency,
            "owner_document_still_present": owner_document_still_present,
            "owner_search_status_code": search_response.status_code,
            "owner_search_latency_ms": search_latency,
            "owner_search_still_works": owner_search_still_works,
        }
    finally:
        if valid_authorization:
            for unexpected_document_id in unexpected_document_ids:
                delete_response, delete_latency = send_request(
                    "DELETE",
                    f"/documents/{unexpected_document_id}",
                    headers=valid_authorization,
                )
                evidence["cleanup"].append(
                    {
                        "resource": "unexpected_document",
                        "resource_id": unexpected_document_id,
                        "status_code": delete_response.status_code,
                        "latency_ms": delete_latency,
                        "response": response_json(delete_response),
                    }
                )

        if valid_authorization and document_id:
            delete_response, delete_latency = send_request(
                "DELETE",
                f"/documents/{document_id}",
                headers=valid_authorization,
            )
            evidence["cleanup"].append(
                {
                    "resource": "document",
                    "resource_id": document_id,
                    "status_code": delete_response.status_code,
                    "latency_ms": delete_latency,
                    "response": response_json(delete_response),
                }
            )

        case_count = len(evidence["cases"])
        passed_count = sum(
            case["outcome"] == "Pass" for case in evidence["cases"]
        )
        postcondition = evidence.get("postcondition", {})
        protected_state_preserved = bool(
            postcondition.get("owner_document_still_present")
            and postcondition.get("owner_search_still_works")
        )
        evidence["finished_at"] = utc_now()
        evidence["summary"] = {
            "request_cases_executed": case_count,
            "request_cases_passed": passed_count,
            "request_cases_failed": case_count - passed_count,
            "protected_state_preserved": protected_state_preserved,
            "cleanup_succeeded": bool(evidence["cleanup"])
            and all(item["status_code"] == 200 for item in evidence["cleanup"]),
            "outcome": (
                "Pass"
                if case_count == 20
                and passed_count == case_count
                and protected_state_preserved
                else "Fail"
            ),
        }

        EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        evidence_path = EVIDENCE_DIRECTORY / f"sec-jwt-{run_stamp}.json"
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(f"Evidence: {evidence_path}")
        print(json.dumps(evidence["summary"], indent=2))


if __name__ == "__main__":
    main()
