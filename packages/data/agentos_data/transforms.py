import pandas as pd


def pivot_summary(df: pd.DataFrame, index: str, columns: str, values: str, aggfunc: str = "sum") -> pd.DataFrame:
    return pd.pivot_table(df, index=index, columns=columns, values=values, aggfunc=aggfunc)


def group_aggregate(df: pd.DataFrame, group_by: list[str], agg: dict[str, str]) -> pd.DataFrame:
    return df.groupby(group_by).agg(agg).reset_index()


def filter_outliers(df: pd.DataFrame, column: str, n_std: float = 3.0) -> pd.DataFrame:
    mean, std = df[column].mean(), df[column].std()
    return df[(df[column] >= mean - n_std * std) & (df[column] <= mean + n_std * std)]


def to_timeseries(df: pd.DataFrame, date_column: str, freq: str = "D") -> pd.DataFrame:
    result = df.copy()
    result[date_column] = pd.to_datetime(result[date_column])
    result = result.set_index(date_column).sort_index()
    return result.asfreq(freq)
