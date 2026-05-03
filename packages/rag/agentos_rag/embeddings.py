"""Embedding service with two backends: local SBERT and Gemini API.

AgentOS is a free-tier-friendly boilerplate (Koyeb free, Render free,
Vercel hobby) — anything that needs GB-scale model downloads or a GPU
breaks the "deploy on free tier" promise. We support exactly the two
embedding paths that respect that constraint:

  =================================  ========  ==========  ===================================
  EMBEDDING_MODEL value              Backend   Dim         Trade-off
  =================================  ========  ==========  ===================================
  all-MiniLM-L6-v2  (default)        sbert     384         tiny, ~80MB, CPU, offline, no key
  gemini-embedding-001               gemini    3072 (cfg)  ★ free API, multilingual,
                                                            reuses GEMINI_API_KEY, 0 MB install
  text-embedding-004                 gemini    768         legacy free Gemini, simpler
  =================================  ========  ==========  ===================================

Gemini path needs ``GEMINI_API_KEY`` set (same key as the LLM cascade
already uses). Free tier on AI Studio is generous enough for hackathon
volume (~1500 RPD on the embed endpoint as of 2026-05); over that it
falls back to paid pricing or 429s.

Pick one with EMBEDDING_MODEL and the matching backend handles it.
Switching means the vector dim changes (384 → 3072), so the pgvector
column has to be re-ALTERed and existing rows re-embedded. The FAISS
in-memory index detects dim at construction.

Heavier self-hosted models (BGE-M3, Qwen3-8B, NV-Embed) work too —
the SbertBackend is generic — but they need GB of RAM/disk and
defeat the point of free-tier deployment, so we don't promote them.
"""
from __future__ import annotations

import os
from typing import Any

DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Gemini embed models — recognized by name so we can route them through
# the Google SDK instead of trying to load them as a SentenceTransformer.
_GEMINI_MODELS = (
    "gemini-embedding-001",
    "gemini-embedding",
    "text-embedding-004",
    "text-embedding-005",
    "embedding-001",
    "embedding-004",
)


def _default_model_name() -> str:
    return os.getenv("EMBEDDING_MODEL", "").strip() or DEFAULT_EMBEDDING_MODEL


def _is_gemini_model(name: str) -> bool:
    n = name.lower()
    return n.startswith("gemini-") or n.startswith("models/gemini-") or n in _GEMINI_MODELS


class EmbeddingService:
    """Embedding facade: routes to SBERT or Gemini based on model name.

    Singleton-per-model-name across the process so weights / API clients
    are loaded once.
    """

    # Cache (model_name → backend instance) so switching at runtime in
    # tests / multi-tenant contexts reloads cleanly.
    _instances: dict[str, "_Backend"] = {}

    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or _default_model_name()

    @property
    def backend(self) -> "_Backend":
        if self._model_name not in EmbeddingService._instances:
            EmbeddingService._instances[self._model_name] = _build_backend(self._model_name)
        return EmbeddingService._instances[self._model_name]

    def encode(self, texts: list[str]) -> list[list[float]]:
        return self.backend.encode(texts)

    @property
    def dimension(self) -> int:
        return self.backend.dimension

    @property
    def model_name(self) -> str:
        return self._model_name


# ── backend interface + implementations ────────────────────────────


class _Backend:
    """Internal protocol — concrete backends implement encode + dimension."""

    def encode(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @property
    def dimension(self) -> int:
        raise NotImplementedError


def _build_backend(model_name: str) -> _Backend:
    if _is_gemini_model(model_name):
        return _GeminiBackend(model_name)
    return _SbertBackend(model_name)


class _SbertBackend(_Backend):
    """Local sentence-transformers model. Lazy-loaded, normalized output."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        self._model_name = model_name
        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()


class _GeminiBackend(_Backend):
    """Google AI Studio embedding API. Uses the same GEMINI_API_KEY as
    the LLM cascade. Free tier on the embed endpoint is generous enough
    for hackathon traffic; over the rate limit you'll get 429s and the
    caller decides whether to retry or downgrade to SBERT.

    The dim defaults to 3072 (the strongest gemini-embedding-001 setting)
    but can be reduced via EMBEDDING_DIM env for cheaper storage / faster
    similarity. The model supports 768 / 1536 / 3072 natively (Matryoshka
    representation — truncating still gives a meaningful embedding).
    """

    def __init__(self, model_name: str):
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "EMBEDDING_MODEL is a Gemini model but GEMINI_API_KEY is not set. "
                "Either set the key or switch EMBEDDING_MODEL to a local model "
                "like all-MiniLM-L6-v2 or BAAI/bge-m3."
            )
        # Normalize to the format the SDK expects.
        self._model_name = (
            model_name if model_name.startswith("models/") else model_name
        )
        self._client = genai.Client(api_key=api_key)
        # Configurable dim (Matryoshka). Default to 3072 — full-fidelity
        # gemini-embedding-001 — unless the user wants to save storage.
        self._dim = int(os.getenv("EMBEDDING_DIM", "3072") or 3072)

    def encode(self, texts: list[str]) -> list[list[float]]:
        from google.genai import types as genai_types

        # The SDK accepts a list and returns one embedding per input.
        # Output is already L2-normalized for similarity tasks. The
        # OUTPUT_DIMENSIONALITY parameter applies the Matryoshka
        # truncation server-side so we don't pay for full 3072 floats
        # over the wire when we want fewer.
        resp = self._client.models.embed_content(
            model=self._model_name,
            contents=texts,
            config=genai_types.EmbedContentConfig(output_dimensionality=self._dim),
        )
        # `embeddings` is a list of ContentEmbedding objects; .values is
        # the float list. Different SDK versions name it slightly
        # differently — handle both.
        out: list[list[float]] = []
        for item in resp.embeddings:
            values = getattr(item, "values", None) or getattr(item, "embedding", None)
            if values is None and isinstance(item, dict):
                values = item.get("values") or item.get("embedding")
            if values is None:
                raise RuntimeError("Gemini embedding response missing 'values' field")
            out.append(list(values))
        return out

    @property
    def dimension(self) -> int:
        return self._dim
