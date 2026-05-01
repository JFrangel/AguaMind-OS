from agentos_rag.chunking import chunk_documents


def test_short_doc_yields_one_chunk():
    chunks = chunk_documents([{"id": "d1", "content": "This is a short doc.", "metadata": {}}])
    assert len(chunks) == 1
    assert chunks[0]["content"] == "This is a short doc."
    assert chunks[0]["metadata"]["source_id"] == "d1"
    assert chunks[0]["metadata"]["chunk_index"] == 0


def test_long_doc_splits_with_overlap():
    long_text = " ".join([f"word{i}" for i in range(2000)])
    chunks = chunk_documents(
        [{"id": "d1", "content": long_text, "metadata": {}}],
        chunk_size=500,
        overlap=50,
        sentence_aware=False,
    )
    assert len(chunks) >= 4
    # Chunks must overlap by at least the configured amount.
    first_words = chunks[0]["content"].split()[-50:]
    second_words = chunks[1]["content"].split()[:50]
    assert first_words == second_words


def test_sentence_aware_keeps_boundaries():
    text = (
        "First sentence. Second sentence here. "
        "Third sentence is a bit longer. Fourth sentence! "
        "Fifth question? Sixth statement."
    )
    chunks = chunk_documents(
        [{"id": "d1", "content": text, "metadata": {}}],
        chunk_size=8,
        overlap=0,
    )
    # Every chunk should start with a capital letter (sentence boundary respected).
    for chunk in chunks:
        first_alpha = next((c for c in chunk["content"] if c.isalpha()), None)
        assert first_alpha is None or first_alpha.isupper()


def test_metadata_propagates():
    chunks = chunk_documents(
        [
            {
                "id": "doc-7",
                "content": "Text content.",
                "metadata": {"author": "alice", "lang": "en"},
            }
        ]
    )
    assert chunks[0]["metadata"]["author"] == "alice"
    assert chunks[0]["metadata"]["lang"] == "en"
    assert chunks[0]["metadata"]["source_id"] == "doc-7"
