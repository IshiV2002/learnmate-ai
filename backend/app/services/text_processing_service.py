import re
import unicodedata
from typing import TypedDict

from app.core.config import CHUNK_OVERLAP_WORDS, CHUNK_SIZE_WORDS
from app.services.pdf_service import ExtractedPage


class TextChunk(TypedDict):
    """A section of text that keeps its source page information."""

    page_number: int
    chunk_index: int
    text: str


def clean_text(text: str) -> str:
    """Clean extracted text without removing words or meaningful punctuation."""
    if not text:
        return ""

    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove control characters, but keep newlines and tabs for whitespace cleanup.
    normalized_text = "".join(
        character
        for character in normalized_text
        if character in {"\n", "\t"}
        or not unicodedata.category(character).startswith("C")
    )

    # Preserve paragraph breaks while joining unnecessary line wrapping.
    paragraphs = re.split(r"\n\s*\n", normalized_text)
    cleaned_paragraphs: list[str] = []

    for paragraph in paragraphs:
        paragraph = re.sub(r"\s*\n\s*", " ", paragraph)
        paragraph = re.sub(r"[^\S\n]+", " ", paragraph).strip()

        if paragraph:
            cleaned_paragraphs.append(paragraph)

    return "\n\n".join(cleaned_paragraphs)


def _validate_chunk_settings(
    chunk_size_words: int,
    chunk_overlap_words: int,
) -> None:
    """Validate chunk settings before processing any page text."""
    if chunk_size_words <= 0:
        raise ValueError("chunk_size_words must be greater than zero.")

    if chunk_overlap_words < 0:
        raise ValueError("chunk_overlap_words cannot be negative.")

    if chunk_overlap_words >= chunk_size_words:
        raise ValueError("chunk_overlap_words must be smaller than chunk_size_words.")


def chunk_pages(
    pages: list[ExtractedPage],
    chunk_size_words: int = CHUNK_SIZE_WORDS,
    chunk_overlap_words: int = CHUNK_OVERLAP_WORDS,
) -> list[TextChunk]:
    """Clean and split each page independently into overlapping word chunks."""
    _validate_chunk_settings(chunk_size_words, chunk_overlap_words)

    chunks: list[TextChunk] = []
    words_to_advance = chunk_size_words - chunk_overlap_words

    for page in pages:
        cleaned_page_text = clean_text(page["text"])
        words = cleaned_page_text.split()

        if not words:
            continue

        chunk_index = 0

        for start_index in range(0, len(words), words_to_advance):
            chunk_words = words[start_index : start_index + chunk_size_words]

            if not chunk_words:
                continue

            chunks.append(
                {
                    "page_number": page["page_number"],
                    "chunk_index": chunk_index,
                    "text": " ".join(chunk_words),
                }
            )
            chunk_index += 1

            if start_index + chunk_size_words >= len(words):
                break

    return chunks
