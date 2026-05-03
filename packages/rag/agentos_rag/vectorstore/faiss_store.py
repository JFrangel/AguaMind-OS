import faiss
import numpy as np

from .base import BaseVectorStore, SearchResult


class FAISSStore(BaseVectorStore):
    """In-memory FAISS index for development. Persists nothing — restart
    wipes the store. Use PgVectorStore for production.

    Stores documents alongside their embeddings so deletes can rebuild the
    index from the surviving rows. Metadata filtering is applied
    post-search (FAISS doesn't natively support it) — fine for the small
    document counts typical in dev.
    """

    def __init__(self, dimension: int | None = None):
        # Default 384 matches the lightweight all-MiniLM-L6-v2; pass a
        # different value when using a larger embedding model (e.g. 1024
        # for BGE-M3, 4096 for NV-Embed-v2). The factory reads this from
        # the live EmbeddingService so the index always matches.
        self._dimension = dimension if dimension is not None else 384
        self._index = faiss.IndexFlatIP(self._dimension)
        self._documents: list[dict] = []
        self._embeddings: list[list[float]] = []

    async def upsert(self, documents: list[dict], embeddings: list[list[float]]) -> None:
        if not documents:
            return
        vectors = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)
        self._index.add(vectors)
        self._documents.extend(documents)
        self._embeddings.extend(embeddings)

    async def search(
        self, query_embedding: list[float], top_k: int = 5, filters: dict | None = None
    ) -> list[SearchResult]:
        if self._index.ntotal == 0:
            return []

        query = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query)
        # Over-fetch to compensate for filter rejections — capped to total count.
        fetch = min(top_k * 4 if filters else top_k, self._index.ntotal)
        scores, indices = self._index.search(query, fetch)

        results: list[SearchResult] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            doc = self._documents[idx]
            if filters and not self._matches(doc.get("metadata", {}), filters):
                continue
            results.append(
                SearchResult(
                    content=doc["content"],
                    metadata=doc.get("metadata", {}),
                    score=float(score),
                    document_id=doc.get("id", ""),
                )
            )
            if len(results) >= top_k:
                break
        return results

    async def delete(self, document_ids: list[str]) -> None:
        if not document_ids:
            return
        ids = set(document_ids)
        keep_pairs = [
            (doc, emb)
            for doc, emb in zip(self._documents, self._embeddings)
            if doc.get("id") not in ids
        ]
        self._documents = [d for d, _ in keep_pairs]
        self._embeddings = [e for _, e in keep_pairs]
        self._index = faiss.IndexFlatIP(self._dimension)
        if self._embeddings:
            vectors = np.array(self._embeddings, dtype=np.float32)
            faiss.normalize_L2(vectors)
            self._index.add(vectors)

    def __len__(self) -> int:
        return len(self._documents)

    @staticmethod
    def _matches(metadata: dict, filters: dict) -> bool:
        for key, expected in filters.items():
            actual = metadata.get(key)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True
