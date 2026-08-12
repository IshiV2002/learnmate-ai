from pathlib import Path, PurePosixPath
from threading import Lock
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool

from app.agents.retrieval_agent import RetrievalAgent, RetrievalAgentError
from app.core.config import MAX_UPLOAD_SIZE_BYTES, UPLOAD_DIRECTORY
from app.services.pdf_service import PDFExtractionError, extract_pdf_pages
from app.services.text_processing_service import chunk_pages


router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
PDF_SIGNATURE = b"%PDF-"

_retrieval_agent: RetrievalAgent | None = None
_retrieval_agent_lock = Lock()


class DocumentSearchRequest(BaseModel):
    """Validated input for a document semantic search."""

    document_id: str
    query: str
    top_k: int = Field(default=3, ge=1, le=10)

    @field_validator("document_id", "query")
    @classmethod
    def value_must_not_be_blank(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("Value cannot be empty.")

        return cleaned_value


def get_retrieval_agent() -> RetrievalAgent:
    """Create one reusable Retrieval Agent when it is first needed."""
    global _retrieval_agent

    if _retrieval_agent is None:
        with _retrieval_agent_lock:
            if _retrieval_agent is None:
                try:
                    _retrieval_agent = RetrievalAgent()
                except Exception as error:
                    raise RetrievalAgentError(
                        "The Retrieval Agent could not be initialized."
                    ) from error

    return _retrieval_agent


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

    if not chunks:
        try:
            stored_path.unlink(missing_ok=True)
        except OSError:
            pass

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "The PDF contains no extractable text. "
                "Scanned or image-only PDFs are not currently supported."
            ),
        )

    pages_with_text = len({chunk["page_number"] for chunk in chunks})
    document_id = str(uuid4())

    try:
        await run_in_threadpool(
            get_retrieval_agent().index_document,
            document_id,
            original_filename,
            chunks,
        )
    except RetrievalAgentError as error:
        try:
            stored_path.unlink(missing_ok=True)
        except OSError:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The PDF was processed but could not be indexed.",
        ) from error

    return {
        "message": "PDF uploaded, processed, and indexed successfully",
        "document": {
            "document_id": document_id,
            "original_filename": original_filename,
            "page_count": len(pages),
            "pages_with_text": pages_with_text,
            "chunk_count": len(chunks),
            "file_size_bytes": len(file_content),
        },
    }


@router.post("/search")
def search_documents(request: DocumentSearchRequest) -> dict[str, object]:
    """Search the selected indexed document using semantic similarity."""
    try:
        results = get_retrieval_agent().search(
            document_id=request.document_id,
            query=request.query,
            top_k=request.top_k,
        )
    except RetrievalAgentError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The semantic search could not be completed.",
        ) from error

    return {
        "query": request.query,
        "results": results,
    }
