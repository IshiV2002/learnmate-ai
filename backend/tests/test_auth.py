import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import auth, documents
from app.core import security
from app.core.google_auth import (
    GoogleIdentity,
    GoogleIdentityVerificationError,
)
from app.database.database import DocumentDatabase, get_application_database
from app.database.models import DocumentRecord
from app.main import app
from app.services.rate_limit_service import SlidingWindowRateLimiter


TEST_SECRET = "test-only-secret-key-with-at-least-thirty-two-characters"


class FakeClock:
    def __init__(self) -> None:
        self.current_time = 0.0

    def __call__(self) -> float:
        return self.current_time

    def advance(self, seconds: float) -> None:
        self.current_time += seconds


class AuthenticationApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database = DocumentDatabase(
            Path(self.temporary_directory.name) / "authentication.db"
        )
        app.dependency_overrides[get_application_database] = lambda: self.database
        self.document_database_patch = patch.object(
            documents,
            "get_document_database",
            return_value=self.database,
        )
        self.document_database_patch.start()
        self.secret_patch = patch.object(
            security,
            "JWT_SECRET_KEY",
            TEST_SECRET,
        )
        self.secret_patch.start()
        self.client_rate_limiter_patch = patch.object(
            auth,
            "_auth_client_rate_limiter",
            SlidingWindowRateLimiter(max_requests=1_000, window_seconds=60),
        )
        self.identity_rate_limiter_patch = patch.object(
            auth,
            "_auth_identity_rate_limiter",
            SlidingWindowRateLimiter(max_requests=1_000, window_seconds=60),
        )
        self.client_rate_limiter_patch.start()
        self.identity_rate_limiter_patch.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.identity_rate_limiter_patch.stop()
        self.client_rate_limiter_patch.stop()
        self.secret_patch.stop()
        self.document_database_patch.stop()
        app.dependency_overrides.clear()
        self.temporary_directory.cleanup()

    def signup(self, email: str = "student@example.com") -> dict[str, object]:
        response = self.client.post(
            "/auth/signup",
            json={
                "full_name": "Student One",
                "email": email,
                "password": "LearnMate9",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    @staticmethod
    def authorization(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def test_signup_hashes_password_and_returns_safe_profile(self) -> None:
        body = self.signup()
        stored_user = self.database.get_user_by_email("student@example.com")

        self.assertIsNotNone(stored_user)
        self.assertNotEqual(stored_user.password_hash, "LearnMate9")
        self.assertTrue(security.verify_password("LearnMate9", stored_user.password_hash))
        self.assertNotIn("password", body["user"])
        self.assertNotIn("password_hash", body["user"])
        self.assertEqual(body["token_type"], "bearer")

    def test_login_and_me_accept_valid_credentials_and_token(self) -> None:
        signup_body = self.signup()
        login_response = self.client.post(
            "/auth/login",
            json={"email": "STUDENT@example.com", "password": "LearnMate9"},
        )

        self.assertEqual(login_response.status_code, 200, login_response.text)
        me_response = self.client.get(
            "/auth/me",
            headers=self.authorization(login_response.json()["access_token"]),
        )
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(
            me_response.json()["user_id"],
            signup_body["user"]["user_id"],
        )

    def test_duplicate_signup_and_invalid_login_are_rejected(self) -> None:
        self.signup()
        duplicate = self.client.post(
            "/auth/signup",
            json={
                "full_name": "Another Student",
                "email": "student@example.com",
                "password": "LearnMate8",
            },
        )
        invalid_login = self.client.post(
            "/auth/login",
            json={"email": "student@example.com", "password": "WrongPass9"},
        )

        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(invalid_login.status_code, 401)
        self.assertEqual(invalid_login.json()["detail"], "Incorrect email or password.")

    def test_password_policy_and_missing_token_are_rejected(self) -> None:
        weak_signup = self.client.post(
            "/auth/signup",
            json={
                "full_name": "Student One",
                "email": "student@example.com",
                "password": "weakpass",
            },
        )

        self.assertEqual(weak_signup.status_code, 422)
        self.assertEqual(self.client.get("/documents").status_code, 401)

    def test_tampered_token_is_rejected(self) -> None:
        authentication = self.signup()
        tampered_token = authentication["access_token"] + "changed"

        response = self.client.get(
            "/auth/me",
            headers=self.authorization(tampered_token),
        )

        self.assertEqual(response.status_code, 401)

    def test_google_login_creates_account_and_reuses_stable_subject(self) -> None:
        identity = GoogleIdentity(
            subject="google-student-123",
            email="google.student@gmail.com",
            full_name="Google Student",
            email_is_google_authoritative=True,
        )
        with patch.object(auth, "verify_google_id_token", return_value=identity):
            first_response = self.client.post(
                "/auth/google",
                json={"credential": "x" * 120},
            )
            second_response = self.client.post(
                "/auth/google",
                json={"credential": "y" * 120},
            )

        self.assertEqual(first_response.status_code, 200, first_response.text)
        self.assertEqual(second_response.status_code, 200, second_response.text)
        self.assertEqual(
            first_response.json()["user"]["user_id"],
            second_response.json()["user"]["user_id"],
        )
        stored_user = self.database.get_user_by_google_subject(identity.subject)
        self.assertIsNotNone(stored_user)
        self.assertNotIn("google_subject", first_response.json()["user"])

    def test_google_login_links_authoritative_email_account(self) -> None:
        signup_body = self.signup("student@gmail.com")
        identity = GoogleIdentity(
            subject="google-linked-456",
            email="student@gmail.com",
            full_name="Student One",
            email_is_google_authoritative=True,
        )

        with patch.object(auth, "verify_google_id_token", return_value=identity):
            response = self.client.post(
                "/auth/google",
                json={"credential": "z" * 120},
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            response.json()["user"]["user_id"],
            signup_body["user"]["user_id"],
        )
        stored_user = self.database.get_user_by_google_subject(identity.subject)
        self.assertEqual(stored_user.user_id, signup_body["user"]["user_id"])

    def test_google_login_does_not_silently_link_third_party_email(self) -> None:
        self.signup("student@example.com")
        identity = GoogleIdentity(
            subject="google-third-party-789",
            email="student@example.com",
            full_name="Student One",
            email_is_google_authoritative=False,
        )

        with patch.object(auth, "verify_google_id_token", return_value=identity):
            response = self.client.post(
                "/auth/google",
                json={"credential": "q" * 120},
            )

        self.assertEqual(response.status_code, 409)
        self.assertIsNone(
            self.database.get_user_by_google_subject(identity.subject)
        )

    def test_invalid_google_token_is_rejected(self) -> None:
        with patch.object(
            auth,
            "verify_google_id_token",
            side_effect=GoogleIdentityVerificationError(
                "Google sign-in could not be verified."
            ),
        ):
            response = self.client.post(
                "/auth/google",
                json={"credential": "invalid" * 20},
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["detail"],
            "Google sign-in could not be verified.",
        )

    def test_login_rate_limit_enforces_boundary_and_recovers(self) -> None:
        self.signup()
        clock = FakeClock()
        account_limiter = SlidingWindowRateLimiter(
            max_requests=2,
            window_seconds=30,
            clock=clock,
        )
        client_limiter = SlidingWindowRateLimiter(
            max_requests=100,
            window_seconds=30,
            clock=clock,
        )

        with (
            patch.object(auth, "_auth_client_rate_limiter", client_limiter),
            patch.object(auth, "_auth_identity_rate_limiter", account_limiter),
        ):
            responses = [
                self.client.post(
                    "/auth/login",
                    json={
                        "email": "student@example.com",
                        "password": "WrongPass9",
                    },
                )
                for _ in range(3)
            ]
            clock.advance(30)
            recovered_response = self.client.post(
                "/auth/login",
                json={
                    "email": "student@example.com",
                    "password": "WrongPass9",
                },
            )

        self.assertEqual(
            [response.status_code for response in responses],
            [401, 401, 429],
        )
        self.assertEqual(responses[-1].headers["Retry-After"], "30")
        self.assertEqual(
            responses[-1].json()["detail"],
            "Too many authentication attempts. Try again shortly.",
        )
        self.assertEqual(recovered_response.status_code, 401)

    def test_successful_login_clears_account_failure_allowance(self) -> None:
        self.signup()
        account_limiter = SlidingWindowRateLimiter(
            max_requests=2,
            window_seconds=60,
        )

        with patch.object(
            auth,
            "_auth_identity_rate_limiter",
            account_limiter,
        ):
            first_failure = self.client.post(
                "/auth/login",
                json={
                    "email": "student@example.com",
                    "password": "WrongPass9",
                },
            )
            success = self.client.post(
                "/auth/login",
                json={
                    "email": "student@example.com",
                    "password": "LearnMate9",
                },
            )
            failures_after_success = [
                self.client.post(
                    "/auth/login",
                    json={
                        "email": "student@example.com",
                        "password": "WrongPass9",
                    },
                )
                for _ in range(3)
            ]

        self.assertEqual(first_failure.status_code, 401)
        self.assertEqual(success.status_code, 200)
        self.assertEqual(
            [response.status_code for response in failures_after_success],
            [401, 401, 429],
        )

    def test_google_token_abuse_is_limited_before_third_verification(self) -> None:
        client_limiter = SlidingWindowRateLimiter(
            max_requests=2,
            window_seconds=60,
        )
        verification_error = GoogleIdentityVerificationError(
            "Google sign-in could not be verified."
        )

        with (
            patch.object(auth, "_auth_client_rate_limiter", client_limiter),
            patch.object(
                auth,
                "verify_google_id_token",
                side_effect=verification_error,
            ) as verifier,
        ):
            responses = [
                self.client.post(
                    "/auth/google",
                    json={"credential": character * 120},
                )
                for character in ["a", "b", "c"]
            ]

        self.assertEqual(
            [response.status_code for response in responses],
            [401, 401, 429],
        )
        self.assertEqual(verifier.call_count, 2)

    def test_missing_jwt_secret_does_not_create_account(self) -> None:
        with patch.object(security, "JWT_SECRET_KEY", ""):
            response = self.client.post(
                "/auth/signup",
                json={
                    "full_name": "Student One",
                    "email": "student@example.com",
                    "password": "LearnMate9",
                },
            )

        self.assertEqual(response.status_code, 503)
        self.assertIsNone(self.database.get_user_by_email("student@example.com"))

    def test_documents_are_isolated_between_users(self) -> None:
        first = self.signup("first@example.com")
        second = self.signup("second@example.com")
        first_user_id = first["user"]["user_id"]
        second_user_id = second["user"]["user_id"]
        for document_id, owner_id in [
            ("first-document", first_user_id),
            ("second-document", second_user_id),
        ]:
            self.database.create_document(
                DocumentRecord(
                    document_id=document_id,
                    original_filename=f"{document_id}.pdf",
                    stored_filename=f"{document_id}.stored.pdf",
                    page_count=1,
                    pages_with_text=1,
                    chunk_count=1,
                    file_size_bytes=100,
                    created_at="2026-01-01T00:00:00+00:00",
                    user_id=owner_id,
                )
            )

        first_headers = self.authorization(first["access_token"])
        first_list = self.client.get("/documents", headers=first_headers)
        forbidden_document = self.client.get(
            "/documents/second-document",
            headers=first_headers,
        )

        self.assertEqual(first_list.status_code, 200)
        self.assertEqual(
            [document["document_id"] for document in first_list.json()],
            ["first-document"],
        )
        self.assertEqual(forbidden_document.status_code, 404)
