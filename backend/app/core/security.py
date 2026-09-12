from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)


class AuthenticationConfigurationError(Exception):
    """Raised when secure token signing has not been configured."""


password_hash = PasswordHash.recommended()
# A dummy hash makes unknown-email and wrong-password attempts take similar time.
DUMMY_PASSWORD_HASH = password_hash.hash("LearnMate dummy password 2026")


def hash_password(password: str) -> str:
    """Convert a plaintext password into a one-way Argon2 hash."""
    return password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    """Check a plaintext password without exposing the stored hash."""
    return password_hash.verify(password, stored_hash)


def verify_dummy_password(password: str) -> None:
    """Perform password work even when an account does not exist."""
    password_hash.verify(password, DUMMY_PASSWORD_HASH)


def _validated_secret_key() -> str:
    placeholder_prefix = "replace_with_"
    if len(JWT_SECRET_KEY) < 32 or JWT_SECRET_KEY.startswith(placeholder_prefix):
        raise AuthenticationConfigurationError(
            "JWT signing is not configured. Set LEARNMATE_JWT_SECRET_KEY in backend/.env."
        )
    return JWT_SECRET_KEY


def create_access_token(user_id: str) -> tuple[str, int]:
    """Create a signed token containing only the user's stable identifier."""
    issued_at = datetime.now(timezone.utc)
    expiry = issued_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = jwt.encode(
        {"sub": user_id, "iat": issued_at, "exp": expiry},
        _validated_secret_key(),
        algorithm=JWT_ALGORITHM,
    )
    return token, ACCESS_TOKEN_EXPIRE_MINUTES * 60


def decode_access_token(token: str) -> str:
    """Validate a token and return its user identifier."""
    try:
        payload = jwt.decode(
            token,
            _validated_secret_key(),
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "iat", "exp"]},
        )
    except InvalidTokenError as error:
        raise ValueError("The login session is invalid or has expired.") from error

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("The login session is invalid or has expired.")
    return user_id
