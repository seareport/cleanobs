from __future__ import annotations

import os

import numpy as np
import pandas as pd

from ._models import Transformation
from ._settings import get_settings


_RAW_TYPE_CONVERSIONS = {
    "raw_main_interval": pd.Timedelta,
    "raw_start_date": pd.Timestamp,
    "raw_end_date": pd.Timestamp,
}


def to_parquet(df: pd.DataFrame, path: os.PathLike[str] | str) -> None:
    df = df.copy()
    for key in _RAW_TYPE_CONVERSIONS:
        if key in df.attrs:
            df.attrs[key] = str(df.attrs[key])
    df.to_parquet(
        path=path,
        engine="pyarrow",
        compression="zstd",
        compression_level=1,
        index=True,
        write_page_index=True,
        write_page_checksum=True,
    )


def load_raw_from_path(path: str | os.PathLike[str]) -> pd.DataFrame:
    df = pd.read_parquet(path)
    for key, type_ in _RAW_TYPE_CONVERSIONS.items():
        if key in df.attrs:
            df.attrs[key] = type_(df.attrs[key])
    return df


def load_raw(
    unique_id: str,
) -> pd.DataFrame:
    path = f"{get_settings().raw_dir}/{unique_id}.parquet"
    df = load_raw_from_path(path)
    return df


def load_era5(
    unique_id: str,
) -> pd.DataFrame:
    if unique_id.count("-") == 2:
        # The unique id is something like: `ioc-waka-rad`.
        # Nevertheless, the `sensor is not part of the ERA5 id so drop it
        era5_id = unique_id.rsplit('-', 1)[0]
    else:
        era5_id = unique_id
    path = f"{get_settings().era5_dir}/{era5_id}.parquet"
    df = pd.read_parquet(path)
    df = df.assign(
        wind_dir=((180 + 180 / np.pi * np.arctan2(df.u10, df.v10)) % 360),
        wind_mag=np.sqrt(df.u10**2 + df.v10**2),
    )
    return df


def load_trans_from_path(path: str | os.PathLike[str]) -> Transformation:
    with open(path) as fd:
        contents = fd.read()
    model = Transformation.model_validate_json(contents)
    return model


def load_trans(
    unique_id,
) -> Transformation:
    path = f"{get_settings().trans_dir}/{unique_id}.json"
    try:
        trans = load_trans_from_path(path)
    except FileNotFoundError:
        df = load_raw(unique_id)
        provider, provider_id, sensor = unique_id.split("-")
        trans = Transformation(
            provider=provider,
            provider_id=provider_id,
            sensor=sensor,
            start=df.index[0],
            end=df.index[-1],
        )
    return trans


def dump_trans(
    trans: Transformation,
    path: os.PathLike[str] | None = None,
) -> None:
    if path is None:
        path = f"{get_settings().trans_dir}/{trans.provider.lower()}-{trans.provider_id}-{trans.sensor}.json"
    with open(path, "w") as fd:
        fd.write(trans.model_dump_json(indent=2, round_trip=True))
        fd.write("\n")


def transform(df: pd.DataFrame, trans: Transformation | None = None) -> pd.DataFrame:
    nan = float("nan")
    df = df.copy()
    df = df.assign(clean=df.raw, timestamps=nan, date_ranges=nan, tsunamis=nan)
    if trans is None:
        attrs = df.attrs
        trans = load_trans(f"{attrs['provider']}-{attrs['provider_id']}-{attrs['sensor']}".lower())
    df = df[trans.start:trans.end]  # type: ignore[misc]  # https://stackoverflow.com/questions/70763542/pandas-dataframe-mypy-error-slice-index-must-be-an-integer-or-none
    if trans.timestamps and df.index.isin(trans.timestamps).any():
        index = df.index[df.index.isin(trans.timestamps)]
        df.loc[index, "timestamps"] = df.loc[index, "raw"]
        df.loc[index, "clean"] = nan
    for date_range in trans.date_ranges:
        df.loc[date_range.start:date_range.end, "date_ranges"] = df.loc[date_range.start:date_range.end, "raw"]
        df.loc[date_range.start:date_range.end, "clean"] = nan
    for date_range in trans.tsunamis:
        df.loc[date_range.start:date_range.end, "tsunamis"] = df.loc[date_range.start:date_range.end, "raw"]
        df.loc[date_range.start:date_range.end, "clean"] = nan
    return df
