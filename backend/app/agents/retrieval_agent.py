from app.services.embedding_service import EmbeddingService
from app.services.text_processing_service import TextChunk
from app.services.vector_store_service import VectorSearchResult, VectorStoreService


class RetrievalAgentError(Exception):
    """Raised when a document cannot be indexed or searched."""


class RetrievalAgent:
    """Reusable semantic indexing and retrieval for Tutor and Quiz agents."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store_service: VectorStoreService | None = None,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store_service = vector_store_service or VectorStoreService()

    def index_document(
        self,
        document_id: str,
        original_filename: str,
        chunks: list[TextChunk],
    ) -> None:
        """Embed and persist all usable chunks from one uploaded document."""
        try:
            embeddings = self.embedding_service.embed_documents(
                [chunk["text"] for chunk in chunks]
            )
            self.vector_store_service.add_document_chunks(
                document_id=document_id,
                original_filename=original_filename,
                chunks=chunks,
                embeddings=embeddings,
            )
        except Exception as error:
            self.vector_store_service.delete_document(
                document_id,
                ignore_errors=True,
            )
            raise RetrievalAgentError(
                "The document could not be indexed for semantic search."
            ) from error

    def search(
        self,
        document_id: str,
        query: str,
        top_k: int = 3,
    ) -> list[VectorSearchResult]:
        """Return relevant chunks only from the selected document."""
        if not document_id.strip():
            raise ValueError("document_id cannot be empty.")

        if not query.strip():
            raise ValueError("query cannot be empty.")

        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be between 1 and 10.")

        try:
            query_embedding = self.embedding_service.embed_query(query)
            return self.vector_store_service.search_document(
                document_id=document_id,
                query_embedding=query_embedding,
                top_k=top_k,
            )
        except Exception as error:
            raise RetrievalAgentError(
                "The semantic search could not be completed."
            ) from error

    def delete_document(self, document_id: str) -> None:
        """Remove every indexed chunk belonging to one document."""
        try:
            self.vector_store_service.delete_document(document_id)
        except Exception as error:
            raise RetrievalAgentError(
                "The document could not be removed from semantic search."
            ) from error
