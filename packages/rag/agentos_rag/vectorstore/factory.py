import os

from .base import BaseVectorStore


class VectorStoreFactory:
    @staticmethod
    def create(backend: str | None = None) -> BaseVectorStore:
        backend = backend or os.getenv("VECTOR_BACKEND", "faiss")
        if backend == "pgvector":
            from .pgvector import PgVectorStore

            return PgVectorStore()
        if backend == "faiss":
            from .faiss_store import FAISSStore

            # Sync the in-memory FAISS index dimension to whatever model
            # the EmbeddingService is configured with — otherwise BGE-M3
            # (1024 dim) on a default 384-dim FAISS index will throw
            # `AssertionError: dim mismatch` on first upsert. Lazy import
            # so test suites that don't have sentence-transformers installed
            # can still construct a FAISSStore directly.
            try:
                from ..embeddings import EmbeddingService

                dim = EmbeddingService().dimension
                return FAISSStore(dimension=dim)
            except Exception:
                # Falls back to the 384 default — the model load may have
                # failed (no network on first launch, etc.) and we still
                # want the import path to work for tests.
                return FAISSStore()
        raise ValueError(f"Unknown vector backend: {backend}")
