import unittest

from app.services.pdf_service import ExtractedPage
from app.services.text_processing_service import chunk_pages, clean_text


def make_page(page_number: int, text: str) -> ExtractedPage:
    """Create page data in the same format returned by the PDF service."""
    return {"page_number": page_number, "text": text}


class TextCleaningTests(unittest.TestCase):
    def test_normal_text_keeps_words_and_punctuation(self) -> None:
        text = "  LearnMate explains AI clearly.  "

        self.assertEqual(clean_text(text), "LearnMate explains AI clearly.")

    def test_repeated_spaces_and_line_breaks_are_normalized(self) -> None:
        text = "First   line\ncontinues here.\n\n\nSecond\t paragraph."

        self.assertEqual(
            clean_text(text),
            "First line continues here.\n\nSecond paragraph.",
        )

    def test_control_characters_are_removed(self) -> None:
        self.assertEqual(clean_text("Learn\x00Mate\x07 AI"), "LearnMate AI")

    def test_empty_text_returns_empty_text(self) -> None:
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text("  \n\t  "), "")


class PageChunkingTests(unittest.TestCase):
    def test_short_text_creates_one_chunk(self) -> None:
        chunks = chunk_pages(
            [make_page(1, "one two three")],
            chunk_size_words=5,
            chunk_overlap_words=1,
        )

        self.assertEqual(
            chunks,
            [{"page_number": 1, "chunk_index": 0, "text": "one two three"}],
        )

    def test_long_text_creates_several_chunks_with_overlap(self) -> None:
        chunks = chunk_pages(
            [make_page(4, "one two three four five six seven eight")],
            chunk_size_words=4,
            chunk_overlap_words=1,
        )

        self.assertEqual([chunk["text"] for chunk in chunks], [
            "one two three four",
            "four five six seven",
            "seven eight",
        ])

        first_words = chunks[0]["text"].split()
        second_words = chunks[1]["text"].split()
        self.assertEqual(first_words[-1:], second_words[:1])

    def test_page_numbers_and_zero_based_chunk_indexes_are_preserved(self) -> None:
        chunks = chunk_pages(
            [
                make_page(5, "one two three four five"),
                make_page(9, "six seven eight nine ten"),
            ],
            chunk_size_words=3,
            chunk_overlap_words=1,
        )

        self.assertEqual(
            [(chunk["page_number"], chunk["chunk_index"]) for chunk in chunks],
            [(5, 0), (5, 1), (9, 0), (9, 1)],
        )

    def test_empty_pages_are_skipped_and_no_empty_chunks_are_created(self) -> None:
        chunks = chunk_pages(
            [
                make_page(1, ""),
                make_page(2, " \n\t "),
                make_page(3, "usable text"),
            ],
            chunk_size_words=4,
            chunk_overlap_words=1,
        )

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["page_number"], 3)
        self.assertTrue(all(chunk["text"].strip() for chunk in chunks))

    def test_pages_are_never_combined_into_one_chunk(self) -> None:
        chunks = chunk_pages(
            [make_page(1, "page one"), make_page(2, "page two")],
            chunk_size_words=10,
            chunk_overlap_words=0,
        )

        self.assertEqual(len(chunks), 2)
        self.assertEqual([chunk["page_number"] for chunk in chunks], [1, 2])

    def test_invalid_chunk_size_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            chunk_pages([], chunk_size_words=0, chunk_overlap_words=0)

    def test_negative_overlap_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            chunk_pages([], chunk_size_words=10, chunk_overlap_words=-1)

    def test_overlap_equal_to_or_larger_than_size_is_rejected(self) -> None:
        for overlap in (10, 11):
            with self.subTest(overlap=overlap):
                with self.assertRaisesRegex(ValueError, "must be smaller"):
                    chunk_pages(
                        [],
                        chunk_size_words=10,
                        chunk_overlap_words=overlap,
                    )
