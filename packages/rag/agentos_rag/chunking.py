import re
import uuid

# Splits on sentence-ending punctuation followed by whitespace + capital letter,
# or paragraph breaks. Keeps the punctuation with the preceding sentence.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ])|\n\n+")


def chunk_documents(
    documents: list[dict],
    chunk_size: int = 500,
    overlap: int = 50,
    *,
    sentence_aware: bool = True,
) -> list[dict]:
    """Chunk documents respecting sentence boundaries when possible.

    `sentence_aware=True` (default) packs whole sentences into chunks until
    `chunk_size` words is reached. Falls back to word-window splitting for
    sentences longer than chunk_size or when disabled.
    """
    chunks: list[dict] = []
    for doc in documents:
        text = doc.get("content", "")
        metadata = doc.get("metadata", {})
        source_id = doc.get("id", "")

        pieces = (
            _split_by_sentences(text, chunk_size, overlap)
            if sentence_aware
            else _split_by_words(text, chunk_size, overlap)
        )
        for idx, chunk_text in enumerate(pieces):
            chunks.append(
                {
                    "id": str(uuid.uuid4()),
                    "content": chunk_text,
                    "metadata": {
                        **metadata,
                        "source_id": source_id,
                        "chunk_index": idx,
                    },
                }
            )
    return chunks


def _split_by_sentences(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []

    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
    if not sentences:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        sentence_words = sentence.split()
        sentence_len = len(sentence_words)

        # Sentence longer than chunk_size on its own → fall back to word-window.
        if sentence_len > chunk_size:
            if current:
                chunks.append(" ".join(current))
                current = []
                current_len = 0
            chunks.extend(_split_by_words(sentence, chunk_size, overlap))
            continue

        if current_len + sentence_len > chunk_size and current:
            chunks.append(" ".join(current))
            # Build overlap from the tail of the just-emitted chunk.
            tail = " ".join(current).split()[-overlap:] if overlap else []
            current = [" ".join(tail)] if tail else []
            current_len = len(tail)

        current.append(sentence)
        current_len += sentence_len

    if current:
        chunks.append(" ".join(current).strip())
    return chunks


def _split_by_words(text: str, chunk_size: int, overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    if len(words) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    step = max(1, chunk_size - overlap)
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start += step
    return chunks
