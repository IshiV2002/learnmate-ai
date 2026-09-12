from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import (
    AuthenticationConfigurationError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_dummy_password,
    verify_password,
)
from app.database.database import (
    DocumentDatabase,
    DocumentDatabaseError,
    get_application_database,
)
from app.database.models import (
    AuthenticationResponse,
    LoginRequest,
    SignupRequest,
    UserRecord,
    UserResponse,
)


router = APIRouter(prefix="/auth", tags=["authentication"])
bearer_scheme = HTTPBearer(auto_error=False)


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
) -> AuthenticationResponse:
    """Create an account and return its first short-lived login token."""
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

    return authentication


@router.post("/login", response_model=AuthenticationResponse)
def login(
    request: LoginRequest,
    database: ApplicationDatabase,
) -> AuthenticationResponse:
    """Verify an account without revealing which credential was incorrect."""
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

    return _build_authentication_response(user)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: CurrentUser) -> UserResponse:
    """Return safe profile fields for the signed-in user."""
    return UserResponse(**current_user.to_public_dict())
