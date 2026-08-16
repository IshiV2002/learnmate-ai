from pathlib import Path
from typing import TypedDict

import pymupdf


class ExtractedPage(TypedDict):
    """Text and page number extracted from one PDF page."""

    page_number: int
    text: str


class PDFExtractionError(Exception):
    """Raised when text cannot be extracted from an uploaded PDF."""


def extract_pdf_pages(pdf_path: Path) -> list[ExtractedPage]:
    """Extract text one page at a time while preserving page numbers."""
    try:
        with pymupdf.open(pdf_path) as document:
            return [
                {
                    "page_number": page_index + 1,
                    "text": page.get_text("text").strip(),
                }
                for page_index, page in enumerate(document)
            ]
    except (
        pymupdf.EmptyFileError,
        pymupdf.FileDataError,
        OSError,
        RuntimeError,
        ValueError,
    ) as error:
        raise PDFExtractionError(
            "The uploaded PDF could not be opened or processed."
        ) from error
