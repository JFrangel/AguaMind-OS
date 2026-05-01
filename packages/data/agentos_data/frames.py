from pathlib import Path

import pandas as pd


def load(path: str | Path, **kwargs) -> pd.DataFrame:
    path = Path(path)
    if path.suffix == ".csv":
        return pd.read_csv(path, **kwargs)
    if path.suffix in (".xlsx", ".xls"):
        return pd.read_excel(path, **kwargs)
    if path.suffix == ".json":
        return pd.read_json(path, **kwargs)
    if path.suffix == ".parquet":
        return pd.read_parquet(path, **kwargs)
    raise ValueError(f"Unsupported format: {path.suffix}")


def load_from_bytes(data: bytes, format: str, **kwargs) -> pd.DataFrame:
    import io

    buffer = io.BytesIO(data)
    if format == "csv":
        return pd.read_csv(buffer, **kwargs)
    if format in ("xlsx", "xls"):
        return pd.read_excel(buffer, **kwargs)
    if format == "json":
        return pd.read_json(buffer, **kwargs)
    raise ValueError(f"Unsupported format: {format}")


def summary(df: pd.DataFrame) -> dict:
    return {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": df.isnull().sum().to_dict(),
        "describe": df.describe().to_dict(),
    }
