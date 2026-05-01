import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor


class AnomalyDetector:
    def __init__(self, method: str = "isolation_forest", contamination: float = 0.1):
        self._method = method
        self._contamination = contamination
        self._model = self._create_model()

    def _create_model(self):
        if self._method == "isolation_forest":
            return IsolationForest(contamination=self._contamination, random_state=42)
        if self._method == "lof":
            return LocalOutlierFactor(contamination=self._contamination, novelty=True)
        raise ValueError(f"Unknown method: {self._method}")

    def fit(self, data: pd.DataFrame | np.ndarray) -> "AnomalyDetector":
        self._model.fit(data)
        return self

    def predict(self, data: pd.DataFrame | np.ndarray) -> list[dict]:
        predictions = self._model.predict(data)
        scores = self._model.decision_function(data)

        results = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            results.append({
                "index": i,
                "score": float(score),
                "is_anomaly": pred == -1,
            })
        return results

    def fit_predict(self, data: pd.DataFrame | np.ndarray) -> list[dict]:
        self.fit(data)
        return self.predict(data)
