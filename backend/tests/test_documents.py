import io
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from starlette.datastructures import Headers

from app.api import documents
from app.main import app
from app.services.pdf_service import extract_pdf_pages


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


class DocumentUploadTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.upload_directory = Path(self.temporary_directory.name)
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

    def tearDown(self) -> None:
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
        self.assertNotIn("stored_filename", document_metadata)
        self.assertNotIn("pages", response)
        self.assertEqual(
            self.fake_retrieval_agent.indexed_document_ids,
            [document_metadata["document_id"]],
        )

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
        self.fake_retrieval_agent = FakeRetrievalAgent()
        self.retrieval_agent_patch = patch.object(
            documents,
            "get_retrieval_agent",
            return_value=self.fake_retrieval_agent,
        )
        self.retrieval_agent_patch.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.retrieval_agent_patch.stop()

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

    def test_unknown_document_returns_empty_results(self) -> None:
        response = self.client.post(
            "/documents/search",
            json={
                "document_id": "unknown-document",
                "query": "machine learning",
                "top_k": 3,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"query": "machine learning", "results": []},
        )
