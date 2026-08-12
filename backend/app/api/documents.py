from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import MAX_UPLOAD_SIZE_BYTES, UPLOAD_DIRECTORY
from app.services.pdf_service import PDFExtractionError, extract_pdf_pages
from app.services.text_processing_service import chunk_pages


router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
PDF_SIGNATURE = b"%PDF-"


def _safe_display_filename(filename: str | None) -> str:
    """Remove any directory information supplied by the client."""
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    # Replacing backslashes also handles filenames sent by Windows clients.
    normalized_filename = filename.replace("\\", "/")
    return PurePosixPath(normalized_filename).name


def _validate_file_metadata(filename: str, content_type: str | None) -> None:
    """Validate the filename extension and the reported MIME type."""
    if Path(filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only files with a .pdf extension are allowed.",
        )

    if content_type not in ALLOWED_PDF_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The uploaded file must use a PDF content type.",
        )


def _validate_file_content(file_content: bytes) -> None:
    """Reject empty, oversized, or obviously non-PDF file content."""
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF is empty.",
        )

    if len(file_content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=(
                "The uploaded PDF is too large. "
                f"The maximum size is {MAX_UPLOAD_SIZE_BYTES} bytes."
            ),
        )

    if not file_content.startswith(PDF_SIGNATURE):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file does not contain valid PDF content.",
        )


def _create_safe_storage_path() -> tuple[str, Path]:
    """Create a unique server-side filename that cannot contain user paths."""
    stored_filename = f"{uuid4().hex}.pdf"
    upload_directory = UPLOAD_DIRECTORY.resolve()
    stored_path = (upload_directory / stored_filename).resolve()

    # This extra check protects the storage directory if this code changes later.
    if stored_path.parent != upload_directory:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create a safe upload path.",
        )

    return stored_filename, stored_path


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)) -> dict[str, object]:
    """Validate, save, and extract page-level text from one uploaded PDF."""
    try:
        original_filename = _safe_display_filename(file.filename)
        _validate_file_metadata(original_filename, file.content_type)

        # Reading one byte beyond the limit lets us detect an oversized upload
        # without loading an unlimited file into memory.
        file_content = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    finally:
        await file.close()

    _validate_file_content(file_content)
    stored_filename, stored_path = _create_safe_storage_path()

    try:
        UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
        stored_path.write_bytes(file_content)
    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The PDF could not be saved.",
        ) from error

    try:
        pages = extract_pdf_pages(stored_path)
    except PDFExtractionError as error:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    chunks = chunk_pages(pages)
    pages_with_text = len({chunk["page_number"] for chunk in chunks})

    return {
        "message": "PDF uploaded and processed successfully",
        "document": {
            "original_filename": original_filename,
            "page_count": len(pages),
            "pages_with_text": pages_with_text,
            "chunk_count": len(chunks),
            "file_size_bytes": len(file_content),
        },
    }
