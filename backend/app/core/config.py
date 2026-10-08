import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIRECTORY / ".env")

UPLOAD_DIRECTORY = BACKEND_DIRECTORY / "uploads"
CHROMA_DATA_DIRECTORY = BACKEND_DIRECTORY / "chroma_data"
DATA_DIRECTORY = BACKEND_DIRECTORY / "data"
SQLITE_DATABASE_PATH = DATA_DIRECTORY / "learnmate.db"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_COLLECTION_NAME = "learnmate_documents"
GEMINI_MODEL_NAME = os.getenv(
    "LEARNMATE_GEMINI_MODEL_NAME",
    "gemini-2.5-flash",
).strip() or "gemini-2.5-flash"

# Only the local Vite development servers may call this API from a browser.
FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

DEFAULT_MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
DEFAULT_MAX_IMAGE_PIXELS = 25_000_000
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
DEFAULT_MAX_SEARCH_QUERY_CHARACTERS = 4_096
DEFAULT_SEARCH_RATE_LIMIT_REQUESTS = 10
DEFAULT_SEARCH_RATE_LIMIT_WINDOW_SECONDS = 10
DEFAULT_AUTH_ACCOUNT_RATE_LIMIT_REQUESTS = 5
DEFAULT_AUTH_CLIENT_RATE_LIMIT_REQUESTS = 20
DEFAULT_AUTH_RATE_LIMIT_WINDOW_SECONDS = 60
DEFAULT_MAX_RETRIEVAL_COSINE_DISTANCE = 0.8

JWT_SECRET_KEY = os.getenv("LEARNMATE_JWT_SECRET_KEY", "").strip()
JWT_ALGORITHM = "HS256"
GOOGLE_CLIENT_ID = os.getenv("LEARNMATE_GOOGLE_CLIENT_ID", "").strip()

# Text chunks use words because this is simple to understand and inspect.
CHUNK_SIZE_WORDS = 180
CHUNK_OVERLAP_WORDS = 30

if CHUNK_SIZE_WORDS <= 0:
    raise RuntimeError("CHUNK_SIZE_WORDS must be greater than zero.")

if CHUNK_OVERLAP_WORDS < 0:
    raise RuntimeError("CHUNK_OVERLAP_WORDS cannot be negative.")

if CHUNK_OVERLAP_WORDS >= CHUNK_SIZE_WORDS:
    raise RuntimeError("CHUNK_OVERLAP_WORDS must be smaller than CHUNK_SIZE_WORDS.")


def _read_max_upload_size() -> int:
    """Read the upload limit from the environment or use the safe default."""
    configured_value = os.getenv(
        "LEARNMATE_MAX_UPLOAD_SIZE_BYTES",
        str(DEFAULT_MAX_UPLOAD_SIZE_BYTES),
    )

    try:
        maximum_size = int(configured_value)
    except ValueError as error:
        raise RuntimeError(
            "LEARNMATE_MAX_UPLOAD_SIZE_BYTES must be a whole number."
        ) from error

    if maximum_size <= 0:
        raise RuntimeError(
            "LEARNMATE_MAX_UPLOAD_SIZE_BYTES must be greater than zero."
        )

    return maximum_size


MAX_UPLOAD_SIZE_BYTES = _read_max_upload_size()


def _read_positive_integer(name: str, default: int) -> int:
    """Read a positive whole-number security setting from the environment."""
    configured_value = os.getenv(name, str(default))

    try:
        value = int(configured_value)
    except ValueError as error:
        raise RuntimeError(f"{name} must be a whole number.") from error

    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero.")

    return value


MAX_SEARCH_QUERY_CHARACTERS = _read_positive_integer(
    "LEARNMATE_MAX_SEARCH_QUERY_CHARACTERS",
    DEFAULT_MAX_SEARCH_QUERY_CHARACTERS,
)
SEARCH_RATE_LIMIT_REQUESTS = _read_positive_integer(
    "LEARNMATE_SEARCH_RATE_LIMIT_REQUESTS",
    DEFAULT_SEARCH_RATE_LIMIT_REQUESTS,
)
SEARCH_RATE_LIMIT_WINDOW_SECONDS = _read_positive_integer(
    "LEARNMATE_SEARCH_RATE_LIMIT_WINDOW_SECONDS",
    DEFAULT_SEARCH_RATE_LIMIT_WINDOW_SECONDS,
)
AUTH_ACCOUNT_RATE_LIMIT_REQUESTS = _read_positive_integer(
    "LEARNMATE_AUTH_ACCOUNT_RATE_LIMIT_REQUESTS",
    DEFAULT_AUTH_ACCOUNT_RATE_LIMIT_REQUESTS,
)
AUTH_CLIENT_RATE_LIMIT_REQUESTS = _read_positive_integer(
    "LEARNMATE_AUTH_CLIENT_RATE_LIMIT_REQUESTS",
    DEFAULT_AUTH_CLIENT_RATE_LIMIT_REQUESTS,
)
AUTH_RATE_LIMIT_WINDOW_SECONDS = _read_positive_integer(
    "LEARNMATE_AUTH_RATE_LIMIT_WINDOW_SECONDS",
    DEFAULT_AUTH_RATE_LIMIT_WINDOW_SECONDS,
)


def _read_retrieval_distance_limit() -> float:
    """Read a valid cosine-distance cutoff for semantic retrieval."""
    configured_value = os.getenv(
        "LEARNMATE_MAX_RETRIEVAL_COSINE_DISTANCE",
        str(DEFAULT_MAX_RETRIEVAL_COSINE_DISTANCE),
    )

    try:
        maximum_distance = float(configured_value)
    except ValueError as error:
        raise RuntimeError(
            "LEARNMATE_MAX_RETRIEVAL_COSINE_DISTANCE must be a number."
        ) from error

    if not 0 < maximum_distance <= 2:
        raise RuntimeError(
            "LEARNMATE_MAX_RETRIEVAL_COSINE_DISTANCE must be greater than 0 "
            "and no greater than 2."
        )

    return maximum_distance


MAX_RETRIEVAL_COSINE_DISTANCE = _read_retrieval_distance_limit()


def _read_max_image_pixels() -> int:
    """Limit decoded image dimensions to reduce memory-exhaustion attacks."""
    configured_value = os.getenv(
        "LEARNMATE_MAX_IMAGE_PIXELS",
        str(DEFAULT_MAX_IMAGE_PIXELS),
    )

    try:
        maximum_pixels = int(configured_value)
    except ValueError as error:
        raise RuntimeError(
            "LEARNMATE_MAX_IMAGE_PIXELS must be a whole number."
        ) from error

    if maximum_pixels <= 0:
        raise RuntimeError(
            "LEARNMATE_MAX_IMAGE_PIXELS must be greater than zero."
        )

    return maximum_pixels


def _find_tessdata_directory() -> Path | None:
    """Find Tesseract language data without depending on the shell PATH."""
    configured_path = (
        os.getenv("LEARNMATE_TESSDATA_PATH", "").strip()
        or os.getenv("TESSDATA_PREFIX", "").strip()
    )
    if configured_path:
        return Path(configured_path)

    common_locations = [
        Path(r"C:\Program Files\Tesseract-OCR\tessdata"),
        Path("/usr/share/tesseract-ocr/5/tessdata"),
        Path("/usr/share/tessdata"),
        Path("/opt/homebrew/share/tessdata"),
    ]
    return next(
        (path for path in common_locations if (path / "eng.traineddata").is_file()),
        None,
    )


MAX_IMAGE_PIXELS = _read_max_image_pixels()
TESSDATA_DIRECTORY = _find_tessdata_directory()
OCR_LANGUAGE = "eng"


def _read_access_token_expiry() -> int:
    """Read the login duration while rejecting unsafe configuration values."""
    configured_value = os.getenv(
        "LEARNMATE_ACCESS_TOKEN_EXPIRE_MINUTES",
        str(DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    try:
        expiry_minutes = int(configured_value)
    except ValueError as error:
        raise RuntimeError(
            "LEARNMATE_ACCESS_TOKEN_EXPIRE_MINUTES must be a whole number."
        ) from error

    if expiry_minutes <= 0:
        raise RuntimeError(
            "LEARNMATE_ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero."
        )

    return expiry_minutes


ACCESS_TOKEN_EXPIRE_MINUTES = _read_access_token_expiry()
