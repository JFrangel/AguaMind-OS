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

            return FAISSStore()
        raise ValueError(f"Unknown vector backend: {backend}")
