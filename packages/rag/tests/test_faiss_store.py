"""Tests FAISS in-memory store: upsert, search, filters, delete-rebuild.

Critical: previously delete() built an empty index and lost surviving rows.
This file pins that behavior.
"""
import pytest

faiss = pytest.importorskip("faiss")
from agentos_rag.vectorstore.faiss_store import FAISSStore


def _vec(seed: int, dim: int = 4) -> list[float]:
    return [float((seed + i) % 7) for i in range(dim)]


@pytest.mark.asyncio
async def test_upsert_and_search():
    store = FAISSStore(dimension=4)
    docs = [
        {"id": "1", "content": "alpha", "metadata": {"tag": "a"}},
        {"id": "2", "content": "beta",  "metadata": {"tag": "b"}},
    ]
    await store.upsert(docs, [_vec(1), _vec(2)])

    results = await store.search(_vec(1), top_k=2)
    assert len(results) == 2
    assert results[0].document_id == "1"


@pytest.mark.asyncio
async def test_search_with_filters():
    store = FAISSStore(dimension=4)
    docs = [
        {"id": "1", "content": "x", "metadata": {"tag": "a"}},
        {"id": "2", "content": "y", "metadata": {"tag": "b"}},
        {"id": "3", "content": "z", "metadata": {"tag": "a"}},
    ]
    await store.upsert(docs, [_vec(1), _vec(2), _vec(3)])

    results = await store.search(_vec(1), top_k=5, filters={"tag": "a"})
    ids = sorted(r.document_id for r in results)
    assert ids == ["1", "3"]


@pytest.mark.asyncio
async def test_delete_preserves_remaining():
    """Regression test: delete() previously dropped all docs by building
    an empty index. Survivors must remain searchable."""
    store = FAISSStore(dimension=4)
    docs = [
        {"id": "1", "content": "a", "metadata": {}},
        {"id": "2", "content": "b", "metadata": {}},
        {"id": "3", "content": "c", "metadata": {}},
    ]
    await store.upsert(docs, [_vec(1), _vec(2), _vec(3)])

    await store.delete(["2"])

    assert len(store) == 2
    results = await store.search(_vec(1), top_k=5)
    surviving = sorted(r.document_id for r in results)
    assert surviving == ["1", "3"]


@pytest.mark.asyncio
async def test_search_on_empty_store():
    store = FAISSStore(dimension=4)
    assert await store.search(_vec(1), top_k=5) == []


@pytest.mark.asyncio
async def test_filter_with_list_values():
    store = FAISSStore(dimension=4)
    docs = [
        {"id": "1", "content": "x", "metadata": {"lang": "en"}},
        {"id": "2", "content": "y", "metadata": {"lang": "es"}},
        {"id": "3", "content": "z", "metadata": {"lang": "fr"}},
    ]
    await store.upsert(docs, [_vec(1), _vec(2), _vec(3)])

    results = await store.search(_vec(1), top_k=5, filters={"lang": ["en", "es"]})
    ids = sorted(r.document_id for r in results)
    assert ids == ["1", "2"]
