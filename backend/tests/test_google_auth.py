import unittest
from unittest.mock import patch

from app.core import google_auth


class GoogleIdentityVerificationTests(unittest.TestCase):
    def test_verified_google_token_returns_minimum_identity(self) -> None:
        claims = {
            "iss": "https://accounts.google.com",
            "sub": "google-subject-123",
            "email": "Student.Name@gmail.com",
            "email_verified": True,
            "name": "  Student   Name  ",
        }

        with (
            patch.object(google_auth, "GOOGLE_CLIENT_ID", "client-id"),
            patch.object(
                google_auth.id_token,
                "verify_oauth2_token",
                return_value=claims,
            ) as verifier,
        ):
            identity = google_auth.verify_google_id_token("signed-token")

        self.assertEqual(identity.subject, "google-subject-123")
        self.assertEqual(identity.email, "student.name@gmail.com")
        self.assertEqual(identity.full_name, "Student Name")
        self.assertTrue(identity.email_is_google_authoritative)
        self.assertEqual(verifier.call_args.args[2], "client-id")

    def test_unverified_email_and_wrong_issuer_are_rejected(self) -> None:
        base_claims = {
            "iss": "https://accounts.google.com",
            "sub": "google-subject-123",
            "email": "student@gmail.com",
            "email_verified": False,
            "name": "Student Name",
        }

        with (
            patch.object(google_auth, "GOOGLE_CLIENT_ID", "client-id"),
            patch.object(
                google_auth.id_token,
                "verify_oauth2_token",
                return_value=base_claims,
            ),
            self.assertRaises(google_auth.GoogleIdentityVerificationError),
        ):
            google_auth.verify_google_id_token("signed-token")

        with (
            patch.object(google_auth, "GOOGLE_CLIENT_ID", "client-id"),
            patch.object(
                google_auth.id_token,
                "verify_oauth2_token",
                return_value={
                    **base_claims,
                    "iss": "https://untrusted.example",
                    "email_verified": True,
                },
            ),
            self.assertRaises(google_auth.GoogleIdentityVerificationError),
        ):
            google_auth.verify_google_id_token("signed-token")

    def test_missing_client_id_is_reported_before_token_verification(self) -> None:
        with (
            patch.object(google_auth, "GOOGLE_CLIENT_ID", ""),
            patch.object(
                google_auth.id_token,
                "verify_oauth2_token",
            ) as verifier,
            self.assertRaises(
                google_auth.GoogleAuthenticationConfigurationError
            ),
        ):
            google_auth.verify_google_id_token("signed-token")

        verifier.assert_not_called()


if __name__ == "__main__":
    unittest.main()
