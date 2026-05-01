from fastapi import APIRouter, File, Request, UploadFile
from pydantic import BaseModel

from agentos_files import FileAdapterFactory, UnsupportedFormatError
from agentos_rag import RAGPipeline

router = APIRouter()


def _pipeline(request: Request) -> RAGPipeline:
    """Single shared instance from app.state — same one the agents use, so
    documents ingested via /rag/ingest are visible to the researcher node.
    """
    return request.app.state.rag_pipeline


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: dict | None = None


class IngestTextRequest(BaseModel):
    documents: list[dict]
    metadata_defaults: dict | None = None


@router.post("/search")
async def search(body: SearchRequest, request: Request):
    pipeline = _pipeline(request)
    results = await pipeline.query(body.query, top_k=body.top_k, filters=body.filters)
    return {"data": results, "error": None, "meta": {"top_k": body.top_k, "count": len(results)}}


@router.post("/ingest")
async def ingest(request: Request, file: UploadFile = File(...)):
    """Ingest any supported file (PDF/DOCX/HTML/CSV/XLSX/JSON/MD/TXT/...).

    The FileAdapterFactory normalizes to text + metadata before chunking, so
    the RAG store always sees clean text regardless of the input format.
    """
    content = await file.read()
    try:
        doc = FileAdapterFactory.normalize(content, filename=file.filename)
    except UnsupportedFormatError as e:
        return {"data": None, "error": str(e)}

    documents = [
        {
            "id": file.filename or "unknown",
            "content": doc.text,
            "metadata": {
                "filename": file.filename,
                "size": len(content),
                **doc.metadata,
            },
        }
    ]
    pipeline = _pipeline(request)
    count = await pipeline.ingest(documents)
    return {
        "data": {"chunks_created": count, "adapter": doc.metadata.get("adapter")},
        "error": None,
    }


@router.post("/ingest-text")
async def ingest_text(body: IngestTextRequest, request: Request):
    """Ingest pre-formatted documents (id, content, metadata).

    Useful for programmatic ingestion from another service that already
    has structured data — skip the file-upload roundtrip. When metadata
    defaults are provided we instantiate a one-shot pipeline so the
    defaults don't leak into subsequent uploads, but the underlying
    vector store is still the shared one via the same factory backend.
    """
    pipeline = _pipeline(request)
    if body.metadata_defaults:
        pipeline = RAGPipeline(metadata_defaults=body.metadata_defaults)
    count = await pipeline.ingest(body.documents)
    return {"data": {"chunks_created": count}, "error": None}


@router.delete("/source/{source_id}")
async def delete_source(source_id: str, request: Request):
    pipeline = _pipeline(request)
    deleted = await pipeline.delete_by_source(source_id)
    return {"data": {"deleted": deleted}, "error": None}
