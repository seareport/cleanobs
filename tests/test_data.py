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
    assert trans.start == pd.Timestamp("2012-01", tz="utc")
    assert trans.end == pd.Timestamp("2012-12", tz="utc")


def test_trans_dump_load_roundtrip(tmp_path):
    orig_trans = C.Transformation(
        provider="provider",
        provider_id="provider_id",
        sensor="sensor",
        start=pd.Timestamp("2012-01", tz="utc"),
        end=pd.Timestamp("2012-12", tz="utc"),
        timestamps=[
            pd.Timestamp("2012-03", tz="utc"),
        ],
        date_ranges=[
            {
                "start": pd.Timestamp("2012-05", tz="utc"),
                "end": pd.Timestamp("2012-07", tz="utc"),
            },
        ],
        tsunamis=[
            {
                "start": pd.Timestamp("2012-09", tz="utc"),
                "end": pd.Timestamp("2012-10", tz="utc"),
            },
        ],
    )
    path = tmp_path / "trans.json"
    C.dump_trans(orig_trans, path)
    loaded_trans = C.load_trans_from_path(path)
    assert loaded_trans.model_dump() == orig_trans.model_dump()
