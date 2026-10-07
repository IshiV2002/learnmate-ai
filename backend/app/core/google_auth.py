from dataclasses import dataclass

from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests
from google.oauth2 import id_token

from app.core.config import GOOGLE_CLIENT_ID


class GoogleAuthenticationConfigurationError(Exception):
    """Raised when Google sign-in has not been configured."""


class GoogleIdentityVerificationError(Exception):
    """Raised when a Google credential is missing or cannot be trusted."""


class GoogleIdentityServiceError(Exception):
    """Raised when Google's verification service cannot be reached."""


@dataclass(frozen=True)
class GoogleIdentity:
    subject: str
    email: str
    full_name: str
    email_is_google_authoritative: bool


def verify_google_id_token(credential: str) -> GoogleIdentity:
    """Verify a Google ID token and return only the claims LearnMate needs."""
    if not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID.startswith("replace_with_"):
        raise GoogleAuthenticationConfigurationError(
            "Google sign-in is not configured on the server."
        )

    try:
        claims = id_token.verify_oauth2_token(
            credential,
            requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except ValueError as error:
        raise GoogleIdentityVerificationError(
            "Google sign-in could not be verified."
        ) from error
    except GoogleAuthError as error:
        raise GoogleIdentityServiceError(
            "Google sign-in is temporarily unavailable."
        ) from error

    if claims.get("iss") not in {
        "accounts.google.com",
        "https://accounts.google.com",
    }:
        raise GoogleIdentityVerificationError(
            "Google sign-in could not be verified."
        )

    subject = str(claims.get("sub", "")).strip()
    email = str(claims.get("email", "")).strip().lower()
    email_verified = claims.get("email_verified") in {True, "true"}
    if not subject or not email or not email_verified:
        raise GoogleIdentityVerificationError(
            "Google did not provide a verified account identity."
        )

    full_name = " ".join(str(claims.get("name", "")).split())
    if len(full_name) < 2:
        full_name = email.split("@", 1)[0].replace(".", " ").title()
    full_name = full_name[:80]

    hosted_domain = str(claims.get("hd", "")).strip()
    google_is_authoritative = email.endswith("@gmail.com") or bool(hosted_domain)

    return GoogleIdentity(
        subject=subject,
        email=email,
        full_name=full_name,
        email_is_google_authoritative=google_is_authoritative,
    )
