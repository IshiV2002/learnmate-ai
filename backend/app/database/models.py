from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DocumentRecord:
    """Metadata kept for one successfully indexed PDF."""

    document_id: str
    original_filename: str
    stored_filename: str
    page_count: int
    pages_with_text: int
    chunk_count: int
    file_size_bytes: int
    created_at: str

    def to_public_dict(self) -> dict[str, str | int]:
        """Return only fields that are safe for API clients to see."""
        public_record = asdict(self)
        public_record.pop("stored_filename")
        return public_record
