from fastapi import APIRouter, File, UploadFile

from agentos_data import frames
from agentos_files import FileAdapterFactory, UnsupportedFormatError

router = APIRouter()


@router.post("/upload")
async def upload_data(file: UploadFile = File(...)):
    """Universal upload — accepts CSV/XLSX/JSON/PDF/DOCX/HTML/MD/TXT/etc.

    Returns text + tabular preview + metadata. Tabular fields exist when the
    source had structured rows; for unstructured documents only `text` and
    `metadata` are populated.
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

    return {
        "data": {
            "text_preview": doc.text[:2000],
            "tabular_preview": (doc.tabular or [])[:20],
            "summary": summary,
            "metadata": doc.metadata,
        },
        "error": None,
    }


@router.post("/analyze")
async def analyze_data(file: UploadFile = File(...)):
    content = await file.read()
    try:
        doc = FileAdapterFactory.normalize(content, filename=file.filename)
    except UnsupportedFormatError as e:
        return {"data": None, "error": str(e)}

    if not doc.tabular:
        return {
            "data": {"metadata": doc.metadata, "text_chars": len(doc.text)},
            "error": None,
            "meta": {"note": "non-tabular document; only text was extracted"},
        }

    import pandas as pd

    df = pd.DataFrame(doc.tabular)
    return {"data": frames.summary(df), "error": None}
