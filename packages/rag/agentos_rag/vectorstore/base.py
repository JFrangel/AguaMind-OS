from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    content: str
    metadata: dict
    score: float
    document_id: str


class BaseVectorStore(ABC):
    @abstractmethod
    async def upsert(self, documents: list[dict], embeddings: list[list[float]]) -> None: ...

    @abstractmethod
    async def search(
        self, query_embedding: list[float], top_k: int = 5, filters: dict | None = None
    ) -> list[SearchResult]: ...

    @abstractmethod
    async def delete(self, document_ids: list[str]) -> None: ...
