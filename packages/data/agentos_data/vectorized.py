import numpy as np
import pandas as pd


def normalize(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    cols = columns or df.select_dtypes(include=[np.number]).columns.tolist()
    result = df.copy()
    for col in cols:
        min_val, max_val = result[col].min(), result[col].max()
        if max_val - min_val > 0:
            result[col] = (result[col] - min_val) / (max_val - min_val)
    return result


def standardize(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    cols = columns or df.select_dtypes(include=[np.number]).columns.tolist()
    result = df.copy()
    for col in cols:
        mean, std = result[col].mean(), result[col].std()
        if std > 0:
            result[col] = (result[col] - mean) / std
    return result


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def moving_average(series: pd.Series, window: int = 7) -> pd.Series:
    return series.rolling(window=window, min_periods=1).mean()
