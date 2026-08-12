import unittest

from app.services.embedding_service import EmbeddingService


class EmbeddingServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # The real model is loaded once and reused across all embedding tests.
        cls.service = EmbeddingService()

    def test_document_embedding_returns_a_vector(self) -> None:
        embeddings = self.service.embed_documents(["supervised machine learning"])

        self.assertEqual(len(embeddings), 1)
        self.assertGreater(len(embeddings[0]), 0)
        self.assertTrue(all(isinstance(value, float) for value in embeddings[0]))

    def test_document_and_query_dimensions_are_consistent(self) -> None:
        document_vector = self.service.embed_documents(["neural networks"])[0]
        query_vector = self.service.embed_query("How do neural networks learn?")

        self.assertEqual(len(document_vector), len(query_vector))
        self.assertEqual(len(document_vector), 384)

    def test_multiple_texts_create_multiple_embeddings(self) -> None:
        embeddings = self.service.embed_documents(
            ["classification lesson", "astronomy lesson"]
        )

        self.assertEqual(len(embeddings), 2)
        self.assertEqual(len(embeddings[0]), len(embeddings[1]))

    def test_empty_document_list_returns_an_empty_list(self) -> None:
        self.assertEqual(self.service.embed_documents([]), [])

    def test_blank_document_or_query_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Document text cannot be empty"):
            self.service.embed_documents(["valid text", "   "])

        with self.assertRaisesRegex(ValueError, "Search query cannot be empty"):
            self.service.embed_query("   ")
