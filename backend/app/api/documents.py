from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from threading import Lock
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool

from app.agents.retrieval_agent import RetrievalAgent, RetrievalAgentError
from app.core.config import MAX_UPLOAD_SIZE_BYTES, UPLOAD_DIRECTORY
from app.database.database import DocumentDatabase, DocumentDatabaseError
from app.database.models import DocumentRecord
from app.services.pdf_service import PDFExtractionError, extract_pdf_pages
from app.services.text_processing_service import chunk_pages


router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
PDF_SIGNATURE = b"%PDF-"

_retrieval_agent: RetrievalAgent | None = None
_retrieval_agent_lock = Lock()
_document_database: DocumentDatabase | None = None
_document_database_lock = Lock()


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


def get_document_database() -> DocumentDatabase:
    """Create one reusable SQLite database service when first needed."""
    global _document_database

    if _document_database is None:
        with _document_database_lock:
            if _document_database is None:
                _document_database = DocumentDatabase()

    return _document_database


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


def _stored_document_path(stored_filename: str) -> Path:
    """Resolve a server-generated filename without trusting client path data."""
    upload_directory = UPLOAD_DIRECTORY.resolve()

    if Path(stored_filename).name != stored_filename:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The stored document path is invalid.",
        )

    stored_path = (upload_directory / stored_filename).resolve()

    if stored_path.parent != upload_directory:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The stored document path is invalid.",
        )

    return stored_path


def _database_error_response(error: DocumentDatabaseError) -> HTTPException:
    """Hide internal database details from public error responses."""
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="The document metadata operation could not be completed.",
    )


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
        retrieval_agent = get_retrieval_agent()
        await run_in_threadpool(
            retrieval_agent.index_document,
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

    document_record = DocumentRecord(
        document_id=document_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        page_count=len(pages),
        pages_with_text=pages_with_text,
        chunk_count=len(chunks),
        file_size_bytes=len(file_content),
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    try:
        await run_in_threadpool(
            get_document_database().create_document,
            document_record,
        )
    except DocumentDatabaseError as error:
        # SQLite is the final upload step. If it fails, remove the Chroma
        # records and PDF so the API does not report a partial success.
        try:
            await run_in_threadpool(
                retrieval_agent.delete_document,
                document_id,
            )
        except RetrievalAgentError:
            pass

        try:
            stored_path.unlink(missing_ok=True)
        except OSError:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The PDF was indexed but its metadata could not be saved.",
        ) from error

    return {
        "message": "PDF uploaded, processed, and indexed successfully",
        "document": document_record.to_public_dict(),
    }


@router.post("/search")
def search_documents(request: DocumentSearchRequest) -> dict[str, object]:
    """Search the selected indexed document using semantic similarity."""
    try:
        document = get_document_database().get_document(request.document_id)
    except DocumentDatabaseError as error:
        raise _database_error_response(error) from error

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

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


@router.get("")
def list_documents() -> list[dict[str, str | int]]:
    """List all local documents; user ownership is not available yet."""
    try:
        records = get_document_database().list_documents()
    except DocumentDatabaseError as error:
        raise _database_error_response(error) from error

    return [record.to_public_dict() for record in records]


@router.get("/{document_id}")
def get_document(document_id: str) -> dict[str, str | int]:
    """Return public metadata for one locally stored document."""
    try:
        record = get_document_database().get_document(document_id)
    except DocumentDatabaseError as error:
        raise _database_error_response(error) from error

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return record.to_public_dict()


@router.delete("/{document_id}")
def delete_document(document_id: str) -> dict[str, str]:
    """Remove a document from ChromaDB, local storage, and then SQLite."""
    database = get_document_database()

    try:
        record = database.get_document(document_id)
    except DocumentDatabaseError as error:
        raise _database_error_response(error) from error

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    stored_path = _stored_document_path(record.stored_filename)

    # SQLite is deleted last. If an earlier cleanup fails, its metadata stays
    # available so the operation can be diagnosed and safely retried.
    try:
        get_retrieval_agent().delete_document(document_id)
    except RetrievalAgentError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The document could not be removed from semantic search.",
        ) from error

    try:
        stored_path.unlink(missing_ok=True)
    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The stored PDF could not be removed.",
        ) from error

    try:
        metadata_deleted = database.delete_document(document_id)
    except DocumentDatabaseError as error:
        raise _database_error_response(error) from error

    if not metadata_deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The document metadata could not be deleted.",
        )

    return {
        "message": "Document deleted successfully",
        "document_id": document_id,
    }
