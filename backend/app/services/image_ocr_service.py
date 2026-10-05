from pathlib import Path

import pymupdf

from app.core.config import MAX_IMAGE_PIXELS, OCR_LANGUAGE, TESSDATA_DIRECTORY
from app.services.pdf_service import ExtractedPage


class ImageExtractionError(Exception):
    """Raised when an uploaded image cannot be decoded or OCR processed."""


class ImagePixelLimitError(ImageExtractionError):
    """Raised when decoded image dimensions exceed the configured limit."""


class ImageOCRUnavailableError(ImageExtractionError):
    """Raised when the local Tesseract language data is unavailable."""


def _ocr_pixmap(
    pixmap: pymupdf.Pixmap,
    tessdata_directory: Path,
) -> bytes:
    """Create a one-page PDF with an invisible searchable OCR text layer."""
    return pixmap.pdfocr_tobytes(
        language=OCR_LANGUAGE,
        tessdata=str(tessdata_directory),
        compress=True,
    )


def extract_image_page(
    image_content: bytes,
    *,
    tessdata_directory: Path | None = TESSDATA_DIRECTORY,
    max_image_pixels: int = MAX_IMAGE_PIXELS,
) -> tuple[list[ExtractedPage], bytes]:
    """OCR one image as page 1 and return text plus a normalized internal PDF."""
    if (
        tessdata_directory is None
        or not (tessdata_directory / f"{OCR_LANGUAGE}.traineddata").is_file()
    ):
        raise ImageOCRUnavailableError(
            "Image OCR is unavailable because Tesseract language data is not configured."
        )

    try:
        pixmap = pymupdf.Pixmap(image_content)
    except (
        RuntimeError,
        ValueError,
        OSError,
        pymupdf.mupdf.FzErrorBase,
    ) as error:
        raise ImageExtractionError(
            "The uploaded image could not be opened or processed."
        ) from error

    pixel_count = pixmap.width * pixmap.height
    if pixmap.width <= 0 or pixmap.height <= 0 or pixel_count > max_image_pixels:
        raise ImagePixelLimitError(
            "The uploaded image dimensions are too large to process safely."
        )

    # Tesseract expects RGB pixels without transparency. This conversion also
    # creates a normalized representation without carrying original metadata.
    if pixmap.colorspace is None:
        raise ImageExtractionError(
            "The uploaded image uses an unsupported color format."
        )
    if pixmap.colorspace.n != 3:
        pixmap = pymupdf.Pixmap(pymupdf.csRGB, pixmap)
    if pixmap.alpha:
        pixmap = pymupdf.Pixmap(pixmap, 0)

    try:
        normalized_pdf = _ocr_pixmap(pixmap, tessdata_directory)
        with pymupdf.open(stream=normalized_pdf, filetype="pdf") as document:
            extracted_text = document[0].get_text("text").strip()
    except (
        RuntimeError,
        ValueError,
        OSError,
        pymupdf.FileDataError,
        pymupdf.mupdf.FzErrorBase,
    ) as error:
        raise ImageExtractionError(
            "The uploaded image could not be processed with OCR."
        ) from error

    return ([{"page_number": 1, "text": extracted_text}], normalized_pdf)
