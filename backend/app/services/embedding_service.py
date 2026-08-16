import os
import ssl
from threading import Lock
from typing import Any

from app.core.config import EMBEDDING_MODEL_NAME


class EmbeddingServiceError(Exception):
    """Raised when the local embedding model cannot create vectors."""


class EmbeddingService:
    """Load one Sentence Transformer model and reuse it for all embeddings."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME) -> None:
        self.model_name = model_name
        self._model: Any | None = None
        self._model_lock = Lock()

    def _get_model(self) -> Any:
        """Load the model only when it is first needed."""
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    try:
                        import httpx
                        from huggingface_hub import set_client_factory
                        from sentence_transformers import SentenceTransformer

                        ssl_context = ssl.create_default_context()

                        # Python 3.13 enables strict X.509 checks that reject
                        # some older Windows CA certificates. Certificate and
                        # hostname verification remain fully enabled here.
                        strict_flag = getattr(ssl, "VERIFY_X509_STRICT", 0)
                        if os.name == "nt" and strict_flag:
                            ssl_context.verify_flags &= ~strict_flag

                        set_client_factory(
                            lambda: httpx.Client(verify=ssl_context)
                        )
                        self._model = SentenceTransformer(self.model_name)
                    except Exception as error:
                        raise EmbeddingServiceError(
                            "The embedding model could not be loaded."
                        ) from error

        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Create one embedding vector for each non-empty document chunk."""
        if not texts:
            return []

        if any(not text.strip() for text in texts):
            raise ValueError("Document text cannot be empty.")

        try:
            embeddings = self._get_model().encode_document(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=False,
                show_progress_bar=False,
            )
        except EmbeddingServiceError:
            raise
        except Exception as error:
            raise EmbeddingServiceError(
                "Document embeddings could not be created."
            ) from error

        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Create one embedding vector for a non-empty search query."""
        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        try:
            embedding = self._get_model().encode_query(
                query,
                convert_to_numpy=True,
                normalize_embeddings=False,
                show_progress_bar=False,
            )
        except EmbeddingServiceError:
            raise
        except Exception as error:
            raise EmbeddingServiceError(
                "The search query embedding could not be created."
            ) from error

        return embedding.tolist()
