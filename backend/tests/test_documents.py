import io
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.api import documents
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

    def tearDown(self) -> None:
        self.upload_directory_patch.stop()
        self.temporary_directory.cleanup()

    async def test_valid_pdf_upload(self) -> None:
        pdf_content = create_test_pdf(["LearnMate lecture notes"])
        upload = create_upload(pdf_content, "lecture.pdf", "application/pdf")

        response = await documents.upload_document(upload)
        document_metadata = response["document"]

        self.assertEqual(response["message"], "PDF uploaded and processed successfully")
        self.assertEqual(document_metadata["original_filename"], "lecture.pdf")
        self.assertEqual(document_metadata["page_count"], 1)
        self.assertEqual(document_metadata["pages_with_text"], 1)
        self.assertEqual(document_metadata["file_size_bytes"], len(pdf_content))
        self.assertNotIn("stored_filename", document_metadata)
        self.assertNotIn("pages", response)

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
