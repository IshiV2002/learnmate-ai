import gc
import io
import re
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pymupdf
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from starlette.datastructures import Headers

from app.api import documents
from app.agents.retrieval_agent import RetrievalAgent
from app.database.database import DocumentDatabase, DocumentDatabaseError
from app.database.models import DocumentRecord
from app.main import app
from app.services.pdf_service import extract_pdf_pages
from app.services.vector_store_service import VectorStoreService


def create_test_pdf(page_texts: list[str]) -> bytes:
    """Create a small PDF in memory so no PDF fixture is committed."""
    document = pymupdf.open()

    for page_text in page_texts:
        page = document.new_page()
        page.insert_text((72, 72), page_text)

    pdf_content = document.tobytes()
    document.close()
    return pdf_content


def create_upload(
    content: bytes,
    filename: str,
    content_type: str,
) -> UploadFile:
    """Create an UploadFile object for direct endpoint tests."""
    return UploadFile(
        file=io.BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


class FakeRetrievalAgent:
    """Avoid loading the real embedding model and Chroma in API unit tests."""

    def __init__(self) -> None:
        self.indexed_document_ids: list[str] = []
        self.deleted_document_ids: list[str] = []

    def index_document(
        self,
        document_id: str,
        original_filename: str,
        chunks: list[dict[str, object]],
    ) -> None:
        self.indexed_document_ids.append(document_id)

    def search(
        self,
        document_id: str,
        query: str,
        top_k: int,
    ) -> list[dict[str, object]]:
        return []

    def delete_document(self, document_id: str) -> None:
        self.deleted_document_ids.append(document_id)


class DocumentUploadTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.upload_directory = Path(self.temporary_directory.name)
        self.database = DocumentDatabase(
            self.upload_directory / "test-learnmate.db"
        )
        self.upload_directory_patch = patch.object(
            documents,
            "UPLOAD_DIRECTORY",
            self.upload_directory,
        )
        self.upload_directory_patch.start()
        self.fake_retrieval_agent = FakeRetrievalAgent()
        self.retrieval_agent_patch = patch.object(
            documents,
            "get_retrieval_agent",
            return_value=self.fake_retrieval_agent,
        )
        self.retrieval_agent_patch.start()
        self.database_patch = patch.object(
            documents,
            "get_document_database",
            return_value=self.database,
        )
        self.database_patch.start()

    def tearDown(self) -> None:
        self.database_patch.stop()
        self.retrieval_agent_patch.stop()
        self.upload_directory_patch.stop()
        self.temporary_directory.cleanup()

    async def test_valid_pdf_upload(self) -> None:
        pdf_content = create_test_pdf(["LearnMate lecture notes"])
        upload = create_upload(pdf_content, "lecture.pdf", "application/pdf")

        response = await documents.upload_document(upload)
        document_metadata = response["document"]

        self.assertEqual(
            response["message"],
            "PDF uploaded, processed, and indexed successfully",
        )
        self.assertTrue(document_metadata["document_id"])
        self.assertEqual(document_metadata["original_filename"], "lecture.pdf")
        self.assertEqual(document_metadata["page_count"], 1)
        self.assertEqual(document_metadata["pages_with_text"], 1)
        self.assertEqual(document_metadata["chunk_count"], 1)
        self.assertEqual(document_metadata["file_size_bytes"], len(pdf_content))
        self.assertTrue(document_metadata["created_at"])
        self.assertNotIn("stored_filename", document_metadata)
        self.assertNotIn("pages", response)
        self.assertEqual(
            self.fake_retrieval_agent.indexed_document_ids,
            [document_metadata["document_id"]],
        )
        stored_record = self.database.get_document(document_metadata["document_id"])
        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record.original_filename, "lecture.pdf")

    async def test_document_ids_are_unique(self) -> None:
        first_upload = create_upload(
            create_test_pdf(["First lecture"]),
            "first.pdf",
            "application/pdf",
        )
        second_upload = create_upload(
            create_test_pdf(["Second lecture"]),
            "second.pdf",
            "application/pdf",
        )

        first_response = await documents.upload_document(first_upload)
        second_response = await documents.upload_document(second_upload)

        self.assertNotEqual(
            first_response["document"]["document_id"],
            second_response["document"]["document_id"],
        )

    async def test_pdf_without_extractable_text_is_rejected_and_removed(self) -> None:
        upload = create_upload(
            create_test_pdf([""]),
            "scanned-notes.pdf",
            "application/pdf",
        )

        with self.assertRaises(HTTPException) as raised_error:
            await documents.upload_document(upload)

        self.assertEqual(raised_error.exception.status_code, 422)
        self.assertEqual(
            raised_error.exception.detail,
            (
                "The PDF contains no extractable text. "
                "Scanned or image-only PDFs are not currently supported."
            ),
        )
        self.assertEqual(self.fake_retrieval_agent.indexed_document_ids, [])
        self.assertEqual(self.database.list_documents(), [])
        self.assertEqual(list(self.upload_directory.glob("*.pdf")), [])

    async def test_database_failure_rolls_back_chroma_and_uploaded_pdf(self) -> None:
        upload = create_upload(
            create_test_pdf(["Rollback lecture notes"]),
            "rollback.pdf",
            "application/pdf",
        )

        with patch.object(
            self.database,
            "create_document",
            side_effect=DocumentDatabaseError("Test database failure"),
        ):
            with self.assertRaises(HTTPException) as raised_error:
                await documents.upload_document(upload)

        self.assertEqual(raised_error.exception.status_code, 500)
        self.assertEqual(len(self.fake_retrieval_agent.indexed_document_ids), 1)
        self.assertEqual(
            self.fake_retrieval_agent.deleted_document_ids,
            self.fake_retrieval_agent.indexed_document_ids,
        )
        self.assertEqual(self.database.list_documents(), [])
        self.assertEqual(list(self.upload_directory.glob("*.pdf")), [])

    async def test_non_pdf_extension_is_rejected(self) -> None:
        upload = create_upload(b"plain text", "notes.txt", "application/pdf")

        with self.assertRaises(HTTPException) as raised_error:
            await documents.upload_document(upload)

        self.assertEqual(raised_error.exception.status_code, 400)

    async def test_invalid_content_type_is_rejected(self) -> None:
        pdf_content = create_test_pdf(["Lecture notes"])
        upload = create_upload(pdf_content, "lecture.pdf", "text/plain")

        with self.assertRaises(HTTPException) as raised_error:
            await documents.upload_document(upload)

        self.assertEqual(raised_error.exception.status_code, 415)

    async def test_empty_upload_is_rejected(self) -> None:
        upload = create_upload(b"", "empty.pdf", "application/pdf")

        with self.assertRaises(HTTPException) as raised_error:
            await documents.upload_document(upload)

        self.assertEqual(raised_error.exception.status_code, 400)

    async def test_oversized_upload_is_rejected(self) -> None:
        upload = create_upload(b"%PDF-too-large", "large.pdf", "application/pdf")

        with patch.object(documents, "MAX_UPLOAD_SIZE_BYTES", 5):
            with self.assertRaises(HTTPException) as raised_error:
                await documents.upload_document(upload)

        self.assertEqual(raised_error.exception.status_code, 413)

    async def test_safe_stored_filename_prevents_path_traversal(self) -> None:
        pdf_content = create_test_pdf(["Secure upload test"])
        upload = create_upload(
            pdf_content,
            "../../unsafe lecture.pdf",
            "application/pdf",
        )

        response = await documents.upload_document(upload)
        document_metadata = response["document"]
        stored_files = list(self.upload_directory.glob("*.pdf"))

        self.assertEqual(document_metadata["original_filename"], "unsafe lecture.pdf")
        self.assertNotIn("stored_filename", document_metadata)
        self.assertEqual(len(stored_files), 1)
        self.assertRegex(stored_files[0].name, re.compile(r"^[0-9a-f]{32}\.pdf$"))
        self.assertTrue(stored_files[0].is_file())

    async def test_non_pdf_content_is_rejected(self) -> None:
        upload = create_upload(b"not a real PDF", "fake.pdf", "application/pdf")

        with self.assertRaises(HTTPException) as raised_error:
            await documents.upload_document(upload)

        self.assertEqual(raised_error.exception.status_code, 400)

    def test_pdf_service_preserves_page_numbers(self) -> None:
        pdf_path = self.upload_directory / "pages.pdf"
        pdf_path.write_bytes(create_test_pdf(["Page one", "Page two"]))

        pages = extract_pdf_pages(pdf_path)

        self.assertEqual([page["page_number"] for page in pages], [1, 2])
        self.assertIn("Page one", pages[0]["text"])
        self.assertIn("Page two", pages[1]["text"])


class DocumentSearchApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database = DocumentDatabase(
            Path(self.temporary_directory.name) / "test-learnmate.db"
        )
        self.fake_retrieval_agent = FakeRetrievalAgent()
        self.retrieval_agent_patch = patch.object(
            documents,
            "get_retrieval_agent",
            return_value=self.fake_retrieval_agent,
        )
        self.retrieval_agent_patch.start()
        self.database_patch = patch.object(
            documents,
            "get_document_database",
            return_value=self.database,
        )
        self.database_patch.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.database_patch.stop()
        self.retrieval_agent_patch.stop()
        self.temporary_directory.cleanup()

    def test_empty_query_is_rejected(self) -> None:
        response = self.client.post(
            "/documents/search",
            json={"document_id": "document-1", "query": "   ", "top_k": 3},
        )

        self.assertEqual(response.status_code, 422)

    def test_empty_document_id_is_rejected(self) -> None:
        response = self.client.post(
            "/documents/search",
            json={"document_id": "", "query": "machine learning", "top_k": 3},
        )

        self.assertEqual(response.status_code, 422)

    def test_invalid_top_k_is_rejected(self) -> None:
        for top_k in (0, 11):
            with self.subTest(top_k=top_k):
                response = self.client.post(
                    "/documents/search",
                    json={
                        "document_id": "document-1",
                        "query": "machine learning",
                        "top_k": top_k,
                    },
                )

                self.assertEqual(response.status_code, 422)

    def test_unknown_document_returns_not_found(self) -> None:
        response = self.client.post(
            "/documents/search",
            json={
                "document_id": "unknown-document",
                "query": "machine learning",
                "top_k": 3,
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Document not found."})

    def test_known_document_still_uses_semantic_search(self) -> None:
        self.database.create_document(make_document_record("document-1"))

        response = self.client.post(
            "/documents/search",
            json={
                "document_id": "document-1",
                "query": "machine learning",
                "top_k": 3,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"query": "machine learning", "results": []},
        )


def make_document_record(
    document_id: str,
    stored_filename: str = "0123456789abcdef0123456789abcdef.pdf",
    created_at: str | None = None,
) -> DocumentRecord:
    """Create predictable metadata for document-management API tests."""
    return DocumentRecord(
        document_id=document_id,
        original_filename=f"{document_id}.pdf",
        stored_filename=stored_filename,
        page_count=2,
        pages_with_text=2,
        chunk_count=3,
        file_size_bytes=100,
        created_at=created_at or datetime.now(timezone.utc).isoformat(),
    )


class DocumentManagementApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.upload_directory = Path(self.temporary_directory.name) / "uploads"
        self.upload_directory.mkdir()
        self.database = DocumentDatabase(
            Path(self.temporary_directory.name) / "test-learnmate.db"
        )
        self.fake_retrieval_agent = FakeRetrievalAgent()
        self.upload_directory_patch = patch.object(
            documents,
            "UPLOAD_DIRECTORY",
            self.upload_directory,
        )
        self.database_patch = patch.object(
            documents,
            "get_document_database",
            return_value=self.database,
        )
        self.retrieval_agent_patch = patch.object(
            documents,
            "get_retrieval_agent",
            return_value=self.fake_retrieval_agent,
        )
        self.upload_directory_patch.start()
        self.database_patch.start()
        self.retrieval_agent_patch.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.retrieval_agent_patch.stop()
        self.database_patch.stop()
        self.upload_directory_patch.stop()
        self.temporary_directory.cleanup()

    def test_list_documents_returns_newest_first_without_internal_filename(self) -> None:
        self.database.create_document(
            make_document_record("older", created_at="2026-01-01T00:00:00+00:00")
        )
        self.database.create_document(
            make_document_record("newer", created_at="2026-02-01T00:00:00+00:00")
        )

        response = self.client.get("/documents")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [record["document_id"] for record in response.json()],
            ["newer", "older"],
        )
        self.assertNotIn("stored_filename", response.json()[0])

    def test_get_one_document_does_not_expose_internal_filename(self) -> None:
        self.database.create_document(make_document_record("document-1"))

        response = self.client.get("/documents/document-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["document_id"], "document-1")
        self.assertNotIn("stored_filename", response.json())

    def test_unknown_document_and_delete_return_not_found(self) -> None:
        get_response = self.client.get("/documents/unknown")
        delete_response = self.client.delete("/documents/unknown")

        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)

    def test_delete_removes_metadata_chroma_records_and_pdf(self) -> None:
        stored_filename = "0123456789abcdef0123456789abcdef.pdf"
        stored_pdf = self.upload_directory / stored_filename
        stored_pdf.write_bytes(create_test_pdf(["Delete this document"]))
        self.database.create_document(
            make_document_record("document-1", stored_filename=stored_filename)
        )

        response = self.client.delete("/documents/document-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.database.get_document("document-1"), None)
        self.assertEqual(
            self.fake_retrieval_agent.deleted_document_ids,
            ["document-1"],
        )
        self.assertFalse(stored_pdf.exists())

    def test_delete_rejects_unsafe_internal_stored_filename(self) -> None:
        outside_pdf = Path(self.temporary_directory.name) / "outside.pdf"
        outside_pdf.write_bytes(create_test_pdf(["Do not delete this file"]))
        self.database.create_document(
            make_document_record(
                "unsafe-document",
                stored_filename="../outside.pdf",
            )
        )

        response = self.client.delete("/documents/unsafe-document")

        self.assertEqual(response.status_code, 500)
        self.assertTrue(outside_pdf.exists())
        self.assertIsNotNone(self.database.get_document("unsafe-document"))
        self.assertEqual(self.fake_retrieval_agent.deleted_document_ids, [])


class WorkflowEmbeddingService:
    """Tiny deterministic vectors keep the full API workflow test fast."""

    def _embed(self, text: str) -> list[float]:
        lowercase_text = text.lower()
        vector = [
            float(lowercase_text.count(keyword))
            for keyword in ("cat", "space", "plant")
        ]
        return vector if any(vector) else [0.1, 0.1, 0.1]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._embed(query)


class DocumentWorkflowIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.mkdtemp(
            prefix="learnmate-document-workflow-"
        )
        temporary_path = Path(self.temporary_directory)
        self.upload_directory = temporary_path / "uploads"
        self.database_path = temporary_path / "learnmate.db"
        self.database = DocumentDatabase(self.database_path)
        self.vector_store = VectorStoreService(
            persistence_directory=temporary_path / "chroma",
            collection_name="learnmate_workflow_documents",
        )
        self.retrieval_agent = RetrievalAgent(
            embedding_service=WorkflowEmbeddingService(),  # type: ignore[arg-type]
            vector_store_service=self.vector_store,
        )
        self.upload_directory_patch = patch.object(
            documents,
            "UPLOAD_DIRECTORY",
            self.upload_directory,
        )
        self.database_patch = patch.object(
            documents,
            "get_document_database",
            return_value=self.database,
        )
        self.retrieval_agent_patch = patch.object(
            documents,
            "get_retrieval_agent",
            return_value=self.retrieval_agent,
        )
        self.upload_directory_patch.start()
        self.database_patch.start()
        self.retrieval_agent_patch.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.retrieval_agent_patch.stop()
        self.database_patch.stop()
        self.upload_directory_patch.stop()
        self.vector_store.close()
        del self.retrieval_agent
        del self.vector_store
        gc.collect()
        shutil.rmtree(self.temporary_directory)

    def test_complete_upload_list_get_search_persist_and_delete_workflow(self) -> None:
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/health").status_code, 200)

        upload_response = self.client.post(
            "/documents/upload",
            files={
                "file": (
                    "workflow.pdf",
                    create_test_pdf(["Cats are friendly household pets."]),
                    "application/pdf",
                )
            },
        )
        self.assertEqual(upload_response.status_code, 201)
        public_document = upload_response.json()["document"]
        document_id = public_document["document_id"]
        self.assertNotIn("stored_filename", public_document)

        list_response = self.client.get("/documents")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()[0]["document_id"], document_id)

        get_response = self.client.get(f"/documents/{document_id}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), public_document)

        search_response = self.client.post(
            "/documents/search",
            json={"document_id": document_id, "query": "cats", "top_k": 1},
        )
        self.assertEqual(search_response.status_code, 200)
        self.assertIn("Cats", search_response.json()["results"][0]["text"])

        reopened_database = DocumentDatabase(self.database_path)
        self.assertIsNotNone(reopened_database.get_document(document_id))
        stored_pdfs = list(self.upload_directory.glob("*.pdf"))
        self.assertEqual(len(stored_pdfs), 1)

        delete_response = self.client.delete(f"/documents/{document_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(self.client.get("/documents").json(), [])
        self.assertEqual(
            self.vector_store.count_document_chunks(document_id),
            0,
        )
        self.assertFalse(stored_pdfs[0].exists())
