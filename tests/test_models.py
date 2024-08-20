import datetime
import zoneinfo

import pandas as pd
import pydantic
import pytest
from sortedcontainers_pydantic import SortedSet

from cleanobs import DateRange
from cleanobs import Transformation
from cleanobs import UTC


def test_UTC():
    ta = pydantic.TypeAdapter(UTC)
    expected = datetime.datetime(2010, 1, 1, tzinfo=zoneinfo.ZoneInfo("UTC"))
    assert ta.validate_python("2010") == expected
    assert ta.validate_python("2010-01") == expected
    assert ta.validate_python("2010-01-01") == expected
    assert ta.validate_python(pd.Timestamp("2010-01-01")) == expected


@pytest.mark.parametrize(
    "start,end",
    [
        pytest.param("2010", "2011", id="YYYY"),
        pytest.param("2010-01-01", "2011-01-01", id="YYYY-MM-DD"),
        pytest.param(pd.Timestamp("2010"), pd.Timestamp("2011"), id="pd.Timestamp naive"),
        pytest.param(pd.Timestamp("2010", tz="UTC"), pd.Timestamp("2011", tz="UTC"), id="pd.Timestamp timezone-aware"),
    ],
)
def test_DateRange_from_tuple(start, end):
    expected = DateRange(start=pd.Timestamp("2010", tz="UTC"), end=pd.Timestamp("2011", tz="UTC"))
    instance = DateRange.from_tuple((start, end))
    assert instance == expected


@pytest.mark.parametrize(
    "empty",
    [
        pytest.param([], id="list"),
        pytest.param((), id="tuple"),
        pytest.param(set(), id="set"),
    ],
)
def test_transformation_empty(empty):
    t = Transformation(
        provider="provider",
        provider_id="provider_id",
        sensor="na",
        start=pd.Timestamp("2023"),
        end=pd.Timestamp("2024"),
        timestamps=empty,
        tsunamis=empty,
        date_ranges=empty,
    )
    assert len(t.date_ranges) == 0
    assert isinstance(t.date_ranges, SortedSet)
    assert len(t.timestamps) == 0
    assert isinstance(t.timestamps, SortedSet)
    assert len(t.tsunamis) == 0
    assert isinstance(t.tsunamis, SortedSet)


@pytest.mark.parametrize(
    "timestamps",
    [
        pytest.param(["2024"], id="YYYY"),
        pytest.param(["2024-01"], id="YYYY-MM"),
        pytest.param(["2024-01-01"], id="YYYY-MM-DD"),
        pytest.param(["2024", "2025"], id="multiple"),
    ],
)
def test_transformation_timestamps(timestamps):
    # single item
    expected = SortedSet([pd.Timestamp("2024", tz="UTC")])
    t = Transformation(
        provider="provider",
        provider_id="provider_id",
        sensor="na",
        start=pd.Timestamp("2023"),
        end=pd.Timestamp("2024"),
        timestamps=timestamps,
    )
    assert len(t.timestamps) == len(timestamps)
    assert expected.issubset(t.timestamps)


def test_transformation_tsunamis():
    expected = SortedSet([DateRange.from_tuple(("2024-01-01", "2024-01-03"))])
    t = Transformation(
        provider="provider",
        provider_id="provider_id",
        sensor="na",
        start=pd.Timestamp("2023"),
        end=pd.Timestamp("2024"),
        tsunamis=[DateRange.from_tuple(("2024-01-01", "2024-01-03"))],
    )
    assert len(t.tsunamis) == 1
    assert expected.issubset(t.tsunamis)


def test_transformation_date_ranges():
    expected = SortedSet([DateRange.from_tuple(("2024-01-01", "2024-01-03"))])
    t = Transformation(
        provider="provider",
        provider_id="provider_id",
        sensor="na",
        start=pd.Timestamp("2023"),
        end=pd.Timestamp("2024"),
        date_ranges=[DateRange.from_tuple(("2024-01-01", "2024-01-03"))],
    )
    assert len(t.date_ranges) == 1
    assert expected.issubset(t.date_ranges)


def test_transformation_add_timestamps():
    t = Transformation(
        provider="provider",
        provider_id="provider_id",
        sensor="na",
        start=pd.Timestamp("2023"),
        end=pd.Timestamp("2024"),
    )
    assert len(t.timestamps) == 0
    t.add_timestamps(["2023"])
    assert len(t.timestamps) == 1
    t.add_timestamps(["2023"])
    assert len(t.timestamps) == 1
    t.add_timestamps(["2024"])
    assert len(t.timestamps) == 2
    t.add_timestamps(["2025", "2026"])
    assert len(t.timestamps) == 4


def test_transformation_add_tsunamis():
    t = Transformation(
        provider="provider",
        provider_id="provider_id",
        sensor="na",
        start=pd.Timestamp("2023"),
        end=pd.Timestamp("2024"),
    )
    assert len(t.tsunamis) == 0
    t.add_tsunami("2023", "2024")
    assert len(t.tsunamis) == 1
    t.add_tsunami("2023", "2024")
    assert len(t.tsunamis) == 1
    t.add_tsunami("2013", "2014")
    assert len(t.tsunamis) == 2


def test_transformation_add_date_ranges():
    t = Transformation(
        provider="provider",
        provider_id="provider_id",
        sensor="na",
        start=pd.Timestamp("2023"),
        end=pd.Timestamp("2024"),
    )
    assert len(t.date_ranges) == 0
    t.add_date_range("2023", "2024")
    assert len(t.date_ranges) == 1
    t.add_date_range("2023", "2024")
    assert len(t.date_ranges) == 1
    t.add_date_range("2013", "2014")
    assert len(t.date_ranges) == 2
