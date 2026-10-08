import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf

from app.services.image_ocr_service import (
    ImageExtractionError,
    ImageOCRUnavailableError,
    ImagePixelLimitError,
    extract_image_page,
)


def create_test_png(width: int = 120, height: int = 60) -> bytes:
    """Create an in-memory RGB image without adding a binary fixture."""
    pixmap = pymupdf.Pixmap(
        pymupdf.csRGB,
        pymupdf.IRect(0, 0, width, height),
        False,
    )
    pixmap.clear_with(255)
    return pixmap.tobytes("png")


def create_ocr_pdf(text: str) -> bytes:
    """Create the normalized OCR PDF returned by the mocked OCR boundary."""
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((30, 30), text)
    content = document.tobytes()
    document.close()
    return content


class ImageOCRServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.tessdata_directory = Path(self.temporary_directory.name)
        (self.tessdata_directory / "eng.traineddata").write_bytes(b"test")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_image_is_returned_as_page_one_with_normalized_pdf(self) -> None:
        normalized_pdf = create_ocr_pdf("Readable OCR text")

        with patch(
            "app.services.image_ocr_service._ocr_pixmap",
            return_value=normalized_pdf,
        ):
            pages, stored_content = extract_image_page(
                create_test_png(),
                tessdata_directory=self.tessdata_directory,
            )

        self.assertEqual(pages[0]["page_number"], 1)
        self.assertIn("Readable OCR text", pages[0]["text"])
        self.assertEqual(stored_content, normalized_pdf)

    def test_decoded_pixel_limit_is_enforced_before_ocr(self) -> None:
        with self.assertRaises(ImagePixelLimitError):
            extract_image_page(
                create_test_png(width=101, height=100),
                tessdata_directory=self.tessdata_directory,
                max_image_pixels=10_000,
            )

    def test_corrupt_image_content_is_rejected(self) -> None:
        with self.assertRaises(ImageExtractionError):
            extract_image_page(
                b"not-an-image",
                tessdata_directory=self.tessdata_directory,
            )

    def test_missing_english_language_data_is_reported(self) -> None:
        empty_directory = self.tessdata_directory / "empty"
        empty_directory.mkdir()

        with self.assertRaises(ImageOCRUnavailableError):
            extract_image_page(
                create_test_png(),
                tessdata_directory=empty_directory,
            )
