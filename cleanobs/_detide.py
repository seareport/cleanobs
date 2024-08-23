import json
import os
import pathlib
import typing as T

import numpy as np
import pandas as pd
import utide

from ._settings import get_settings

Constituents = dict[str, T.Any]


def nd_format(dct: Constituents) -> Constituents:
    for key, value in dct.items():
        if isinstance(value, dict):
            dct[key] = nd_format(value)  # Recurse into nested dictionaries
        elif isinstance(value, list):
            dct[key] = np.array(value)  # Convert list to numpy
        else:
            continue
    return dct


def list_format(dct: Constituents) -> Constituents:
    for key, value in dct.items():
        if isinstance(value, dict):
            list_format(value)  # Recurse into nested dictionaries
        elif isinstance(value, np.ndarray):
            dct[key] = value.tolist()  # Convert NumPy array to list
        else:
            continue
    return dct


def calc_constituents(ts: pd.Series, **kwargs: T.Any) -> dict[str, T.Any]:
    constituents = utide.solve(ts.index, ts, lat=ts.attrs["lat"], **kwargs)
    del constituents["weights"]
    return constituents


def load_constituents(unique_id: str) -> Constituents:
    path = pathlib.Path(f"{get_settings().constituents_dir}/{unique_id.lower()}.json")
    constituents = nd_format(json.loads(path.read_text()))
    return constituents


def load_constituents_from_path(path: os.PathLike[str] | str) -> Constituents:
    constituents = nd_format(json.loads(pathlib.Path(path).read_text()))
    return constituents


def dump_constituents(
    unique_id: str,
    constituents: Constituents,
    path: str | os.PathLike[str] | None = None,
) -> None:
    if path is None:
        path = f"{get_settings().constituents_dir}/{unique_id.lower()}.json"
    constituents.pop("weights", None)
    pathlib.Path(path).write_text(json.dumps(list_format(constituents), indent=2))


def calc_surge(df: pd.DataFrame, const: dict[str, T.Any], prefix: str = "utide", **kwargs: T.Any):
    if "verbose" not in kwargs:
        kwargs["verbose"] = False
    # utide throws warnings if datetime aware timestamps are being used.
    # Let's ensure that we are on UTC and drop the timezone
    assert str(df.index.tz) == "UTC"
    df.index = df.index.tz_convert(None)
    reconstructed = utide.reconstruct(df.index, const, **kwargs)
    tide_df = pd.DataFrame({"tide": reconstructed["h"]}, index=reconstructed["t_in"])
    df = df.assign(**{prefix: tide_df.reindex(df.index).tide})
    df = df.assign(**{f"{prefix}_surge": df.clean - df[prefix]})
    return df
