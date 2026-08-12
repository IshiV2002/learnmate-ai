from pathlib import Path
from typing import TypedDict

import chromadb

from app.core.config import CHROMA_COLLECTION_NAME, CHROMA_DATA_DIRECTORY
from app.services.text_processing_service import TextChunk


class VectorStoreError(Exception):
    """Raised when ChromaDB cannot store or retrieve document chunks."""


class VectorSearchResult(TypedDict):
    """A retrieved chunk and its source information."""

    text: str
    page_number: int
    chunk_index: int
    source: str
    distance: float


class VectorStoreService:
    """Store and search LearnMate document chunks in persistent ChromaDB."""

    def __init__(
        self,
        persistence_directory: Path = CHROMA_DATA_DIRECTORY,
        collection_name: str = CHROMA_COLLECTION_NAME,
    ) -> None:
        self.persistence_directory = persistence_directory
        self.persistence_directory.mkdir(parents=True, exist_ok=True)

        try:
            self.client = chromadb.PersistentClient(
                path=str(self.persistence_directory)
            )
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                configuration={"hnsw": {"space": "cosine"}},
                embedding_function=None,
            )
        except Exception as error:
            raise VectorStoreError("ChromaDB could not be initialized.") from error

    def add_document_chunks(
        self,
        document_id: str,
        original_filename: str,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
    ) -> None:
        """Store all chunks for one document in a single Chroma operation."""
        if len(chunks) != len(embeddings):
            raise ValueError("Every chunk must have exactly one embedding.")

        if not chunks:
            return

        record_ids = [
            f"{document_id}:{chunk['page_number']}:{chunk['chunk_index']}"
            for chunk in chunks
        ]
        metadata = [
            {
                "document_id": document_id,
                "original_filename": original_filename,
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
            }
            for chunk in chunks
        ]

        try:
            self.collection.add(
                ids=record_ids,
                embeddings=embeddings,
                documents=[chunk["text"] for chunk in chunks],
                metadatas=metadata,
            )
        except Exception as error:
            # A single batch is normally atomic. Deleting by document_id is an
            # extra safeguard in case a backend failure leaves partial records.
            self.delete_document(document_id, ignore_errors=True)
            raise VectorStoreError("Document chunks could not be indexed.") from error

    def search_document(
        self,
        document_id: str,
        query_embedding: list[float],
        top_k: int,
    ) -> list[VectorSearchResult]:
        """Search only chunks belonging to the requested document."""
        try:
            query_result = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"document_id": document_id},
                include=["documents", "metadatas", "distances"],
            )
        except Exception as error:
            raise VectorStoreError("Document chunks could not be searched.") from error

        documents = query_result.get("documents") or [[]]
        metadatas = query_result.get("metadatas") or [[]]
        distances = query_result.get("distances") or [[]]

        if not documents[0]:
            return []

        results: list[VectorSearchResult] = []

        for text, metadata, distance in zip(
            documents[0],
            metadatas[0],
            distances[0],
        ):
            if text is None or metadata is None:
                continue

            results.append(
                {
                    "text": text,
                    "page_number": int(metadata["page_number"]),
                    "chunk_index": int(metadata["chunk_index"]),
                    "source": str(metadata["original_filename"]),
                    "distance": float(distance),
                }
            )

        return results

    def count_document_chunks(self, document_id: str) -> int:
        """Return the number of stored chunks for one document."""
        try:
            records = self.collection.get(
                where={"document_id": document_id},
                include=[],
            )
        except Exception as error:
            raise VectorStoreError("Document chunks could not be counted.") from error

        return len(records["ids"])

    def delete_document(
        self,
        document_id: str,
        ignore_errors: bool = False,
    ) -> None:
        """Remove every Chroma record belonging to one document."""
        try:
            self.collection.delete(where={"document_id": document_id})
        except Exception as error:
            if not ignore_errors:
                raise VectorStoreError(
                    "Document chunks could not be removed."
                ) from error

    def close(self) -> None:
        """Release Chroma's persistent files, especially for isolated tests."""
        self.client.close()
        self.client.clear_system_cache()
