import pandas as pd

import cleanobs as C


def test_load_raw_from_path():
    df = C.load_raw_from_path("tests/data/raw/ioc-waka-rad.parquet")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 50_000, len(df)
    assert len(df) < 100_000, len(df)


def test_load_raw():
    df = C.load_raw("ioc-waka-rad")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 50_000, len(df)
    assert len(df) < 100_000, len(df)


def test_load_trans():
    trans = C.load_trans("ioc-waka-rad")
    assert isinstance(trans, C.Transformation)


def test_load_trans_not_existing():
    trans = C.load_trans("provider-provider_id-sensor")
    assert isinstance(trans, C.Transformation)
    assert trans.provider == "provider"
    assert trans.provider_id == "provider_id"
    assert trans.sensor == "sensor"
