from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

from agentos_data import frames
from agentos_ml.anomaly import AnomalyDetector

router = APIRouter()


class AnomalyRequest(BaseModel):
    method: str = "isolation_forest"
    contamination: float = 0.1


@router.post("/anomalies")
async def detect_anomalies(file: UploadFile = File(...), method: str = "isolation_forest", contamination: float = 0.1):
    content = await file.read()
    ext = file.filename.rsplit(".", 1)[-1] if file.filename else "csv"
    df = frames.load_from_bytes(content, ext)

    numeric_df = df.select_dtypes(include=["number"]).dropna()
    detector = AnomalyDetector(method=method, contamination=contamination)
    results = detector.fit_predict(numeric_df)

    anomaly_count = sum(1 for r in results if r["is_anomaly"])
    return {
        "data": {
            "total_rows": len(results),
            "anomalies_found": anomaly_count,
            "results": results[:100],
        },
        "error": None,
    }
