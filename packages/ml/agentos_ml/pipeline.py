import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error


class MLPipeline:
    def __init__(self, model, test_size: float = 0.2):
        self._model = model
        self._test_size = test_size
        self._is_fitted = False

    def train(self, X: pd.DataFrame | np.ndarray, y: pd.Series | np.ndarray) -> dict:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self._test_size, random_state=42
        )
        self._model.fit(X_train, y_train)
        self._is_fitted = True

        predictions = self._model.predict(X_test)
        return self._evaluate(y_test, predictions)

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        return self._model.predict(X)

    @staticmethod
    def _evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
        is_classification = len(np.unique(y_true)) < 20
        if is_classification:
            return {
                "accuracy": float(accuracy_score(y_true, y_pred)),
                "f1": float(f1_score(y_true, y_pred, average="weighted")),
                "type": "classification",
            }
        return {
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "type": "regression",
        }
