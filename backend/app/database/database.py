import sqlite3
from contextlib import closing
from pathlib import Path
from threading import Lock

from app.core.config import SQLITE_DATABASE_PATH
from app.database.models import DocumentRecord


class DocumentDatabaseError(Exception):
    """Raised when document metadata cannot be read or changed."""


class DocumentDatabase:
    """Store document metadata in a small local SQLite database."""

    def __init__(self, database_path: Path = SQLITE_DATABASE_PATH) -> None:
        self.database_path = database_path
        self._initialized = False
        self._initialization_lock = Lock()

    def initialize(self) -> None:
        """Create the database and documents table once when first needed."""
        if self._initialized:
            return

        with self._initialization_lock:
            if self._initialized:
                return

            try:
                self.database_path.parent.mkdir(parents=True, exist_ok=True)

                with closing(sqlite3.connect(self.database_path)) as connection:
                    with connection:
                        connection.execute(
                            """
                            CREATE TABLE IF NOT EXISTS documents (
                                document_id TEXT PRIMARY KEY,
                                original_filename TEXT NOT NULL,
                                stored_filename TEXT NOT NULL,
                                page_count INTEGER NOT NULL,
                                pages_with_text INTEGER NOT NULL,
                                chunk_count INTEGER NOT NULL,
                                file_size_bytes INTEGER NOT NULL,
                                created_at TEXT NOT NULL
                            )
                            """
                        )
            except (OSError, sqlite3.Error) as error:
                raise DocumentDatabaseError(
                    "The document database could not be initialized."
                ) from error

            self._initialized = True

    def _connect(self) -> sqlite3.Connection:
        """Open a connection that returns rows with named columns."""
        self.initialize()
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> DocumentRecord:
        return DocumentRecord(
            document_id=row["document_id"],
            original_filename=row["original_filename"],
            stored_filename=row["stored_filename"],
            page_count=row["page_count"],
            pages_with_text=row["pages_with_text"],
            chunk_count=row["chunk_count"],
            file_size_bytes=row["file_size_bytes"],
            created_at=row["created_at"],
        )

    def create_document(self, document: DocumentRecord) -> None:
        """Insert metadata after the PDF has been indexed in ChromaDB."""
        try:
            with closing(self._connect()) as connection:
                with connection:
                    connection.execute(
                        """
                        INSERT INTO documents (
                            document_id,
                            original_filename,
                            stored_filename,
                            page_count,
                            pages_with_text,
                            chunk_count,
                            file_size_bytes,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            document.document_id,
                            document.original_filename,
                            document.stored_filename,
                            document.page_count,
                            document.pages_with_text,
                            document.chunk_count,
                            document.file_size_bytes,
                            document.created_at,
                        ),
                    )
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The document metadata could not be saved."
            ) from error

    def list_documents(self) -> list[DocumentRecord]:
        """Return all documents with the newest uploads first."""
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    """
                    SELECT * FROM documents
                    ORDER BY created_at DESC, rowid DESC
                    """
                ).fetchall()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The document metadata could not be listed."
            ) from error

        return [self._row_to_record(row) for row in rows]

    def get_document(self, document_id: str) -> DocumentRecord | None:
        """Return one document, or None when its ID is unknown."""
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT * FROM documents WHERE document_id = ?",
                    (document_id,),
                ).fetchone()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The document metadata could not be read."
            ) from error

        if row is None:
            return None

        return self._row_to_record(row)

    def delete_document(self, document_id: str) -> bool:
        """Delete one metadata row and report whether it existed."""
        try:
            with closing(self._connect()) as connection:
                with connection:
                    cursor = connection.execute(
                        "DELETE FROM documents WHERE document_id = ?",
                        (document_id,),
                    )
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The document metadata could not be deleted."
            ) from error

        return cursor.rowcount > 0
