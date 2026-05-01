from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any


class RAGTool:
    """Thin adapter that lets the researcher pull context from the RAG pipeline
    without taking a hard import dependency on `agentos_rag`. The default
    constructor lazy-imports the pipeline; tests can inject any callable.
    """

    def __init__(
        self,
        query_fn: Callable[[str, int], Awaitable[list[dict[str, Any]]]] | None = None,
    ):
        self._query_fn = query_fn

    async def query(self, question: str, top_k: int = 4) -> list[dict[str, Any]]:
        fn = self._query_fn or self._default_query
        try:
            return await fn(question, top_k)
        except Exception:
            return []

    @staticmethod
    async def _default_query(question: str, top_k: int) -> list[dict[str, Any]]:
        from agentos_rag import RAGPipeline

        pipeline = _get_singleton()
        return await pipeline.query(question, top_k=top_k)


_singleton: object | None = None


def _get_singleton():
    global _singleton
    if _singleton is None:
        from agentos_rag import RAGPipeline

        _singleton = RAGPipeline()
    return _singleton


def default_rag_tool() -> RAGTool:
    return RAGTool()
