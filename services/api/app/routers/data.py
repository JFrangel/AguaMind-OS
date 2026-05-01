from fastapi import APIRouter, File, Query, Request, UploadFile

from agentos_data import frames
from agentos_files import FileAdapterFactory, UnsupportedFormatError

router = APIRouter()


@router.post("/upload")
async def upload_data(
    request: Request,
    file: UploadFile = File(...),
    index: bool = Query(
        False,
        description=(
            "If true, also ingest the file into the shared RAG pipeline so "
            "subsequent agent runs can use it as context. Without this flag the "
            "endpoint only returns a summary and the file is forgotten."
        ),
    ),
    source: str | None = Query(
        None,
        description=(
            "Optional metadata tag stored alongside the chunks. Useful for "
            "filtering with `/rag/search?filters[source]=...` later."
        ),
    ),
):
    """Universal upload — accepts CSV/XLSX/JSON/PDF/DOCX/HTML/MD/TXT/etc.

    Returns text + tabular preview + metadata. When `?index=true` is set,
    the same content is also chunked + embedded into the shared RAG store
    (the one the chat agent queries when `use_rag=true`), so the file
    becomes part of the agent's working knowledge instead of being a
    one-shot summary.
    """
    content = await file.read()
    try:
        doc = FileAdapterFactory.normalize(content, filename=file.filename)
    except UnsupportedFormatError as e:
        return {"data": None, "error": str(e), "meta": None}

    summary: dict | None = None
    if doc.tabular:
        try:
            import pandas as pd

            df = pd.DataFrame(doc.tabular)
            summary = frames.summary(df)
        except Exception:
            summary = None

    chunks_created: int | None = None
    if index:
        # Pull the shared pipeline from app.state so the chunks land in the
        # same FAISS/pgvector index the agents query at runtime.
        pipeline = getattr(request.app.state, "rag_pipeline", None)
        if pipeline is not None:
            documents = [
                {
                    "id": file.filename or "uploaded",
                    "content": doc.text,
                    "metadata": {
                        "filename": file.filename,
                        "size": len(content),
                        "source": source or "data-upload",
                        **doc.metadata,
                    },
                }
            ]
            chunks_created = await pipeline.ingest(documents)

    return {
        "data": {
            "text_preview": doc.text[:2000],
            "tabular_preview": (doc.tabular or [])[:20],
            "summary": summary,
            "metadata": doc.metadata,
            "indexed": index,
            "chunks_created": chunks_created,
        },
        "error": None,
    }


@router.post("/analyze")
async def analyze_data(
    request: Request,
    file: UploadFile = File(...),
    index: bool = Query(False, description="Also push the file into the RAG store."),
    source: str | None = Query(None),
):
    content = await file.read()
    try:
        doc = FileAdapterFactory.normalize(content, filename=file.filename)
    except UnsupportedFormatError as e:
        return {"data": None, "error": str(e)}

    chunks_created: int | None = None
    if index:
        pipeline = getattr(request.app.state, "rag_pipeline", None)
        if pipeline is not None:
            chunks_created = await pipeline.ingest(
                [
                    {
                        "id": file.filename or "uploaded",
                        "content": doc.text,
                        "metadata": {
                            "filename": file.filename,
                            "source": source or "data-analyze",
                            **doc.metadata,
                        },
                    }
                ]
            )

    if not doc.tabular:
        return {
            "data": {
                "metadata": doc.metadata,
                "text_chars": len(doc.text),
                "indexed": index,
                "chunks_created": chunks_created,
            },
            "error": None,
            "meta": {"note": "non-tabular document; only text was extracted"},
        }

    import pandas as pd

    df = pd.DataFrame(doc.tabular)
    return {
        "data": {
            **frames.summary(df),
            "indexed": index,
            "chunks_created": chunks_created,
        },
        "error": None,
    }
