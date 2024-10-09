from __future__ import annotations

import pathlib
import typing as T

import pandas as pd


def calc_station_stats(df: pd.DataFrame, column: str = "raw") -> dict[str, T.Any]:
    sr = df[column]
    interval_value_counts = sr.index.to_series().diff().value_counts()
    main_interval_occurences = float(interval_value_counts.iloc[0])
    main_interval = T.cast(pd.Timedelta, interval_value_counts.index[0])
    data = {
        f"{column}_start_date": df.index[0],
        f"{column}_end_date": df.index[-1],
        f"{column}_count": len(sr),
        f"{column}_main_interval": main_interval,
        f"{column}_main_interval_ratio": main_interval_occurences / len(sr),
        f"{column}_min": sr.min(),
        f"{column}_q001": float(sr.quantile(0.001)),
        f"{column}_q01": float(sr.quantile(0.01)),
        f"{column}_q25": float(sr.quantile(0.25)),
        f"{column}_mean": float(sr.mean()),
        f"{column}_median": sr.median(),
        f"{column}_q75": float(sr.quantile(0.75)),
        f"{column}_q99": float(sr.quantile(0.99)),
        f"{column}_q999": float(sr.quantile(0.999)),
        f"{column}_max": sr.max(),
        f"{column}_range": abs(sr.max() - sr.min()),
        f"{column}_std": sr.std(),
        f"{column}_skew": T.cast(float, sr.skew()),
        f"{column}_kurtosis": T.cast(float, sr.kurtosis()),
    }
    return data


def calc_station_stats_from_path(path: pathlib.Path, column: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    calc_station_stats(df=df, column=column)
    return df
