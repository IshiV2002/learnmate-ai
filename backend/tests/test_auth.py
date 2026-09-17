import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import documents
from app.core import security
from app.database.database import DocumentDatabase, get_application_database
from app.database.models import DocumentRecord
from app.main import app


TEST_SECRET = "test-only-secret-key-with-at-least-thirty-two-characters"


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
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
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
