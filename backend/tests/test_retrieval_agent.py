import gc
import shutil
import tempfile
import unittest
from pathlib import Path

from app.agents.retrieval_agent import RetrievalAgent
from app.services.text_processing_service import TextChunk
from app.services.vector_store_service import VectorStoreService


class KeywordEmbeddingService:
    """Small deterministic embeddings keep retrieval tests fast and predictable."""

    KEYWORDS = ("cat", "space", "plant")

    def _embed(self, text: str) -> list[float]:
        lowercase_text = text.lower()
        vector = [
            float(lowercase_text.count(keyword))
            for keyword in self.KEYWORDS
        ]

        if not any(vector):
            return [0.1, 0.1, 0.1]

        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._embed(query)


def make_chunk(page: int, index: int, text: str) -> TextChunk:
    return {
        "page_number": page,
        "chunk_index": index,
        "text": text,
    }


class RetrievalAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.mkdtemp(prefix="learnmate-chroma-test-")
        self.vector_store = VectorStoreService(
            persistence_directory=Path(self.temporary_directory),
            collection_name="learnmate_test_documents",
        )
        self.agent = RetrievalAgent(
            embedding_service=KeywordEmbeddingService(),  # type: ignore[arg-type]
            vector_store_service=self.vector_store,
        )

    def tearDown(self) -> None:
        self.vector_store.close()
        del self.agent
        del self.vector_store
        gc.collect()
        shutil.rmtree(self.temporary_directory)

    def test_collection_stores_chunks_and_preserves_metadata(self) -> None:
        chunks = [make_chunk(5, 0, "Cats are playful household animals.")]

        self.agent.index_document("document-a", "animals.pdf", chunks)
        results = self.agent.search("document-a", "Tell me about cats", top_k=1)

        self.assertEqual(self.vector_store.count_document_chunks("document-a"), 1)
        self.assertEqual(results[0]["text"], chunks[0]["text"])
        self.assertEqual(results[0]["page_number"], 5)
        self.assertEqual(results[0]["chunk_index"], 0)
        self.assertEqual(results[0]["source"], "animals.pdf")
        self.assertIsInstance(results[0]["distance"], float)

    def test_semantic_query_returns_the_relevant_chunk(self) -> None:
        chunks = [
            make_chunk(1, 0, "Cats are mammals and popular pets."),
            make_chunk(2, 0, "Space contains stars, planets, and galaxies."),
        ]
        self.agent.index_document("document-a", "topics.pdf", chunks)

        results = self.agent.search("document-a", "cat care", top_k=1)

        self.assertEqual(results[0]["page_number"], 1)
        self.assertIn("Cats", results[0]["text"])

    def test_search_is_filtered_by_document_id(self) -> None:
        self.agent.index_document(
            "document-a",
            "animals-a.pdf",
            [make_chunk(1, 0, "Cats are friendly pets.")],
        )
        self.agent.index_document(
            "document-b",
            "animals-b.pdf",
            [make_chunk(9, 0, "Cats require food and water.")],
        )

        results = self.agent.search("document-a", "cats", top_k=10)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "animals-a.pdf")
        self.assertEqual(results[0]["page_number"], 1)

    def test_unknown_document_and_document_without_chunks_return_no_results(self) -> None:
        self.agent.index_document("empty-document", "empty.pdf", [])

        self.assertEqual(
            self.agent.search("empty-document", "anything", top_k=3),
            [],
        )
        self.assertEqual(
            self.agent.search("unknown-document", "anything", top_k=3),
            [],
        )

    def test_persistent_data_is_available_after_reinitialization(self) -> None:
        self.agent.index_document(
            "persistent-document",
            "persistent.pdf",
            [make_chunk(3, 0, "Plants use sunlight for photosynthesis.")],
        )
        self.vector_store.close()

        reopened_store = VectorStoreService(
            persistence_directory=Path(self.temporary_directory),
            collection_name="learnmate_test_documents",
        )
        reopened_agent = RetrievalAgent(
            embedding_service=KeywordEmbeddingService(),  # type: ignore[arg-type]
            vector_store_service=reopened_store,
        )
        # tearDown will close the newly opened client after this test.
        self.vector_store = reopened_store

        results = reopened_agent.search(
            "persistent-document",
            "How do plants use sunlight?",
            top_k=1,
        )
        self.assertEqual(results[0]["page_number"], 3)
        self.assertEqual(results[0]["source"], "persistent.pdf")

    def test_delete_document_removes_all_chroma_records(self) -> None:
        self.agent.index_document(
            "document-to-delete",
            "delete.pdf",
            [make_chunk(1, 0, "Cats are mammals and popular pets.")],
        )

        self.agent.delete_document("document-to-delete")

        self.assertEqual(
            self.vector_store.count_document_chunks("document-to-delete"),
            0,
        )
