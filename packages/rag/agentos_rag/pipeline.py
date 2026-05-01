from .embeddings import EmbeddingService
from .vectorstore.factory import VectorStoreFactory


class RAGPipeline:
    """Ingest documents → chunk → embed → upsert. Query with semantic search.

    Use `metadata_defaults` to tag every chunk from this pipeline (e.g.
    `tenant_id`, `source_type`) so multi-tenant search via `filters` works
    out of the box.
    """

    def __init__(
        self,
        vector_backend: str | None = None,
        *,
        chunk_size: int = 500,
        overlap: int = 50,
        metadata_defaults: dict | None = None,
    ):
        self.embedder = EmbeddingService()
        self.store = VectorStoreFactory.create(vector_backend)
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._metadata_defaults = metadata_defaults or {}

    async def ingest(self, documents: list[dict]) -> int:
        from .chunking import chunk_documents

        if self._metadata_defaults:
            documents = [
                {**d, "metadata": {**self._metadata_defaults, **d.get("metadata", {})}}
                for d in documents
            ]

        chunks = chunk_documents(
            documents, chunk_size=self._chunk_size, overlap=self._overlap
        )
        if not chunks:
            return 0
        texts = [c["content"] for c in chunks]
        embeddings = self.embedder.encode(texts)
        await self.store.upsert(chunks, embeddings)
        return len(chunks)

    async def query(
        self, question: str, top_k: int = 5, filters: dict | None = None
    ) -> list[dict]:
        query_embedding = self.embedder.encode([question])[0]
        results = await self.store.search(query_embedding, top_k=top_k, filters=filters)
        return [
            {"content": r.content, "score": r.score, "metadata": r.metadata, "id": r.document_id}
            for r in results
        ]

    async def delete(self, document_ids: list[str]) -> None:
        await self.store.delete(document_ids)

    async def delete_by_source(self, source_id: str) -> int:
        """Delete all chunks belonging to a single source document.

        Useful when re-ingesting an updated version: delete the old chunks
        first, then call `ingest()` with the new content. Returns the number
        of chunks removed when the backend supports introspection.
        """
        # FAISS keeps documents in memory; iterate manually.
        store = self.store
        if hasattr(store, "_documents"):
            ids = [
                d.get("id") for d in store._documents
                if d.get("metadata", {}).get("source_id") == source_id
            ]
            if not ids:
                return 0
            await store.delete([i for i in ids if i])
            return len(ids)

        # pgvector: rely on metadata filter via raw SQL since the abstract
        # interface doesn't expose filtered delete.
        if hasattr(store, "_get_pool"):
            pool = await store._get_pool()
            async with pool.acquire() as conn:
                # cmdstatus returns "DELETE N"
                status = await conn.execute(
                    "DELETE FROM documents WHERE metadata->>'source_id' = $1",
                    source_id,
                )
                parts = status.split()
                return int(parts[-1]) if parts and parts[-1].isdigit() else 0
        return 0
