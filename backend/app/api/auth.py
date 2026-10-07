from datetime import datetime, timezone
from hashlib import sha256
import secrets
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import (
    AuthenticationConfigurationError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_dummy_password,
    verify_password,
)
from app.core.google_auth import (
    GoogleAuthenticationConfigurationError,
    GoogleIdentityServiceError,
    GoogleIdentityVerificationError,
    verify_google_id_token,
)
from app.core.config import (
    AUTH_ACCOUNT_RATE_LIMIT_REQUESTS,
    AUTH_CLIENT_RATE_LIMIT_REQUESTS,
    AUTH_RATE_LIMIT_WINDOW_SECONDS,
)
from app.database.database import (
    DocumentDatabase,
    DocumentDatabaseError,
    get_application_database,
)
from app.database.models import (
    AuthenticationResponse,
    GoogleLoginRequest,
    LoginRequest,
    SignupRequest,
    UserRecord,
    UserResponse,
)
from app.services.rate_limit_service import (
    RateLimitExceededError,
    SlidingWindowRateLimiter,
)


router = APIRouter(prefix="/auth", tags=["authentication"])
bearer_scheme = HTTPBearer(auto_error=False)
_auth_client_rate_limiter = SlidingWindowRateLimiter(
    max_requests=AUTH_CLIENT_RATE_LIMIT_REQUESTS,
    window_seconds=AUTH_RATE_LIMIT_WINDOW_SECONDS,
)
_auth_identity_rate_limiter = SlidingWindowRateLimiter(
    max_requests=AUTH_ACCOUNT_RATE_LIMIT_REQUESTS,
    window_seconds=AUTH_RATE_LIMIT_WINDOW_SECONDS,
)


def _client_rate_limit_key(http_request: Request) -> str:
    host = http_request.client.host if http_request.client else "unknown"
    return f"client:{host}"


def _identity_rate_limit_key(provider: str, identifier: str) -> str:
    """Hash account identifiers so the limiter does not retain personal data."""
    normalized_identifier = identifier.strip().lower().encode("utf-8")
    return f"{provider}:{sha256(normalized_identifier).hexdigest()}"


def _enforce_authentication_limit(
    limiter: SlidingWindowRateLimiter,
    key: str,
) -> None:
    try:
        limiter.check_request(key)
    except RateLimitExceededError as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Try again shortly.",
            headers={"Retry-After": str(error.retry_after_seconds)},
        ) from error


def _authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="The login session is invalid or has expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    database: Annotated[DocumentDatabase, Depends(get_application_database)],
) -> UserRecord:
    """Resolve the authenticated user from a signed bearer token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _authentication_error()

    try:
        user_id = decode_access_token(credentials.credentials)
        user = database.get_user_by_id(user_id)
    except (ValueError, DocumentDatabaseError, AuthenticationConfigurationError):
        raise _authentication_error()

    if user is None:
        raise _authentication_error()
    return user


CurrentUser = Annotated[UserRecord, Depends(get_current_user)]
ApplicationDatabase = Annotated[
    DocumentDatabase, Depends(get_application_database)
]


def _build_authentication_response(user: UserRecord) -> AuthenticationResponse:
    try:
        token, expiry_seconds = create_access_token(user.user_id)
    except AuthenticationConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    return AuthenticationResponse(
        access_token=token,
        expires_in_seconds=expiry_seconds,
        user=UserResponse(**user.to_public_dict()),
    )


@router.post(
    "/signup",
    response_model=AuthenticationResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    request: SignupRequest,
    database: ApplicationDatabase,
    http_request: Request,
) -> AuthenticationResponse:
    """Create an account and return its first short-lived login token."""
    client_key = _client_rate_limit_key(http_request)
    identity_key = _identity_rate_limit_key("password", request.email)
    _enforce_authentication_limit(_auth_client_rate_limiter, client_key)
    _enforce_authentication_limit(_auth_identity_rate_limiter, identity_key)

    try:
        if database.get_user_by_email(request.email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        user = UserRecord(
            user_id=str(uuid4()),
            full_name=request.full_name,
            email=request.email,
            password_hash=hash_password(request.password),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        authentication = _build_authentication_response(user)
        database.create_user(user)
    except HTTPException:
        raise
    except DocumentDatabaseError as error:
        if "already exists" in str(error).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            ) from error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The account could not be created.",
        ) from error

    _auth_identity_rate_limiter.clear_key(identity_key)
    return authentication


@router.post("/login", response_model=AuthenticationResponse)
def login(
    request: LoginRequest,
    database: ApplicationDatabase,
    http_request: Request,
) -> AuthenticationResponse:
    """Verify an account without revealing which credential was incorrect."""
    client_key = _client_rate_limit_key(http_request)
    identity_key = _identity_rate_limit_key("password", request.email)
    _enforce_authentication_limit(_auth_client_rate_limiter, client_key)
    _enforce_authentication_limit(_auth_identity_rate_limiter, identity_key)

    try:
        user = database.get_user_by_email(request.email)
    except DocumentDatabaseError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The login could not be completed.",
        ) from error

    if user is None:
        verify_dummy_password(request.password)
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    authentication = _build_authentication_response(user)
    _auth_identity_rate_limiter.clear_key(identity_key)
    return authentication


@router.post("/google", response_model=AuthenticationResponse)
def google_login(
    request: GoogleLoginRequest,
    database: ApplicationDatabase,
    http_request: Request,
) -> AuthenticationResponse:
    """Verify a Google ID token and continue with a normal LearnMate session."""
    client_key = _client_rate_limit_key(http_request)
    _enforce_authentication_limit(_auth_client_rate_limiter, client_key)

    try:
        identity = verify_google_id_token(request.credential)
    except GoogleAuthenticationConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except GoogleIdentityVerificationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    except GoogleIdentityServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    identity_key = _identity_rate_limit_key("google", identity.subject)
    _enforce_authentication_limit(_auth_identity_rate_limiter, identity_key)

    try:
        user = database.get_user_by_google_subject(identity.subject)
        if user is not None:
            authentication = _build_authentication_response(user)
            _auth_identity_rate_limiter.clear_key(identity_key)
            return authentication

        user = database.get_user_by_email(identity.email)
        if user is not None:
            if user.google_subject is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This email is linked to a different Google account.",
                )
            if not identity.email_is_google_authoritative:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "This email already has a password account. "
                        "Sign in with your password instead."
                    ),
                )

            authentication = _build_authentication_response(user)
            database.link_google_identity(user.user_id, identity.subject)
            _auth_identity_rate_limiter.clear_key(identity_key)
            return authentication

        user = UserRecord(
            user_id=str(uuid4()),
            full_name=identity.full_name,
            email=identity.email,
            # Keep the existing non-null database shape while making password
            # login impossible for accounts created only through Google.
            password_hash=hash_password(secrets.token_urlsafe(48)),
            created_at=datetime.now(timezone.utc).isoformat(),
            google_subject=identity.subject,
        )
        authentication = _build_authentication_response(user)
        database.create_user(user)
        _auth_identity_rate_limiter.clear_key(identity_key)
        return authentication
    except HTTPException:
        raise
    except DocumentDatabaseError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google sign-in could not be completed.",
        ) from error


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: CurrentUser) -> UserResponse:
    """Return safe profile fields for the signed-in user."""
    return UserResponse(**current_user.to_public_dict())
