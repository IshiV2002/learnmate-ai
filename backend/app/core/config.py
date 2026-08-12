import os
from pathlib import Path


BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
UPLOAD_DIRECTORY = BACKEND_DIRECTORY / "uploads"

DEFAULT_MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024

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
