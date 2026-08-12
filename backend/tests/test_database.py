import tempfile
import unittest
from pathlib import Path

from app.database.database import DocumentDatabase, DocumentDatabaseError
from app.database.models import DocumentRecord


def make_record(document_id: str, created_at: str) -> DocumentRecord:
    return DocumentRecord(
        document_id=document_id,
        original_filename=f"{document_id}.pdf",
        stored_filename=f"{document_id}.stored.pdf",
        page_count=2,
        pages_with_text=2,
        chunk_count=3,
        file_size_bytes=100,
        created_at=created_at,
    )


class DocumentDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "learnmate.db"
        self.database = DocumentDatabase(self.database_path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_initialization_creates_database_and_documents_table(self) -> None:
        self.database.initialize()

        self.assertTrue(self.database_path.is_file())
        self.assertEqual(self.database.list_documents(), [])

    def test_document_creation_and_primary_key_uniqueness(self) -> None:
        record = make_record("document-1", "2026-01-01T00:00:00+00:00")
        self.database.create_document(record)

        self.assertEqual(self.database.get_document("document-1"), record)

        with self.assertRaises(DocumentDatabaseError):
            self.database.create_document(record)

    def test_metadata_persists_after_database_reinitialization(self) -> None:
        record = make_record("persistent", "2026-01-01T00:00:00+00:00")
        self.database.create_document(record)

        reopened_database = DocumentDatabase(self.database_path)

        self.assertEqual(reopened_database.get_document("persistent"), record)

    def test_list_documents_orders_newest_first(self) -> None:
        older = make_record("older", "2026-01-01T00:00:00+00:00")
        newer = make_record("newer", "2026-02-01T00:00:00+00:00")
        self.database.create_document(older)
        self.database.create_document(newer)

        self.assertEqual(self.database.list_documents(), [newer, older])

    def test_delete_document_removes_metadata(self) -> None:
        self.database.create_document(
            make_record("document-1", "2026-01-01T00:00:00+00:00")
        )

        self.assertTrue(self.database.delete_document("document-1"))
        self.assertIsNone(self.database.get_document("document-1"))
        self.assertFalse(self.database.delete_document("document-1"))
