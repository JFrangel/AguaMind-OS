"""SBERT embedding service with configurable model.

Default is `sentence-transformers/all-MiniLM-L6-v2` because it ships in
~80 MB, runs on CPU at ~100 docs/sec, and gives a 384-dim space that
plays nicely with the bundled pgvector schema (`vector(384)`). It's
the right choice when you want the boilerplate to install and run
anywhere with no GPU.

Override via ``EMBEDDING_MODEL`` env var. Recommended free upgrades
(MTEB ranking, all open-source, all loadable via sentence-transformers):

    Model                            Dim    Ctx     MTEB   License   Notes
    ─────────────────────────────────────────────────────────────────────
    BAAI/bge-m3                      1024   8192    63.0   MIT       ★ best CPU+multilingual upgrade
    BAAI/bge-large-en-v1.5            1024   512     64.2   MIT       English-only, very strong
    intfloat/multilingual-e5-large    1024   514     63.4   MIT       solid multilingual
    Qwen/Qwen3-Embedding-8B           7168   32K     70.6   Apache    needs ~24 GB GPU VRAM
    nvidia/NV-Embed-v2                4096   32K     69.3   CC-BY-NC  needs GPU; non-commercial license

Switching model means:
  - The vector dim of new embeddings changes (e.g. 384 → 1024).
  - The pgvector `documents.embedding` column must match — recreate
    the table with the new dim, OR set ``EMBEDDING_DIM`` so the
    migration uses it (see supabase/migrations/002_pgvector.sql).
  - The FAISS in-memory index detects dim at first encode, so the
    FAISS path auto-adapts.
"""
from __future__ import annotations

import os

from sentence_transformers import SentenceTransformer

DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def _default_model_name() -> str:
    """Read ``EMBEDDING_MODEL`` env, falling back to the lightweight default."""
    return os.getenv("EMBEDDING_MODEL", "").strip() or DEFAULT_EMBEDDING_MODEL


class EmbeddingService:
    """Lazy-loaded SBERT model wrapper. Singleton across the process so the
    model weights are loaded once even if many `EmbeddingService()` are
    constructed.

    The class-level cache is keyed by model name — switching models at
    runtime (e.g. between tests) reloads cleanly without leaking the
    previous one's GPU memory.
    """

    _model: SentenceTransformer | None = None
    _model_name_loaded: str | None = None

    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or _default_model_name()

    @property
    def model(self) -> SentenceTransformer:
        if (
            EmbeddingService._model is None
            or EmbeddingService._model_name_loaded != self._model_name
        ):
            EmbeddingService._model = SentenceTransformer(self._model_name)
            EmbeddingService._model_name_loaded = self._model_name
        return EmbeddingService._model

    def encode(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()

    @property
    def model_name(self) -> str:
        return self._model_name
