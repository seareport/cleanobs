from __future__ import annotations

import datetime
import pathlib
import typing as T
import zoneinfo
from collections.abc import Iterable
from collections.abc import Sequence

import pandas as pd
import pydantic
from sortedcontainers_pydantic import SortedSet

from ._settings import get_settings


def ensure_utc(dt: datetime.datetime) -> datetime.datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
    else:
        dt = dt.astimezone(tz=zoneinfo.ZoneInfo("UTC"))
    return dt


UTC = T.Annotated[datetime.datetime, pydantic.BeforeValidator(pd.Timestamp), pydantic.AfterValidator(ensure_utc)]


_model_config = pydantic.ConfigDict(
    validate_assignment=True,
    arbitrary_types_allowed=True,
    extra="forbid",
    frozen=True,
    revalidate_instances="always",
)


class DateRange(pydantic.BaseModel):
    model_config = _model_config

    start: UTC
    end: UTC

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.start, self.end) < (other.start, other.end)

    @classmethod
    def from_tuple(cls, tpl):
        assert isinstance(tpl, Sequence), f"not a Sequence: {type(tpl)}"
        assert len(tpl) == 2, f"wrong length: {len(tpl)} != 2"
        instance = cls(start=tpl[0], end=tpl[1])
        return instance

    @pydantic.model_validator(mode="after")
    def _check_start_before_end(self):
        assert self.start < self.end, "end date before start date"
        return self


class Transformation(pydantic.BaseModel):
    model_config = _model_config

    provider: str
    provider_id: str
    sensor: str
    notes: str = ""
    skip: bool = True
    wip: bool = True
    start: UTC
    end: UTC
    date_ranges: SortedSet[DateRange] = SortedSet()
    timestamps: SortedSet[UTC] = SortedSet()
    tsunamis: SortedSet[DateRange] = SortedSet()

    _ta_date_range = pydantic.TypeAdapter(DateRange)
    _ta_timestamps = pydantic.TypeAdapter(Iterable[UTC])
    _ta_tsunami = pydantic.TypeAdapter(DateRange)

    def add_date_range(self, start: UTC, end: UTC) -> None:
        validated = self._ta_date_range.validate_python({"start": start, "end":end})
        self.date_ranges.add(validated)

    def add_timestamps(self, timestamps: Iterable[UTC]) -> None:
        validated = self._ta_timestamps.validate_python(timestamps)
        self.timestamps.update(validated)

    def add_tsunami(self, start: UTC, end: UTC) -> None:
        validated = self._ta_tsunami.validate_python({"start": start, "end":end})
        self.tsunamis.add(validated)

    @pydantic.computed_field
    @property
    def path(self) -> pathlib.Path:
        return pathlib.Path(
            f"{get_settings().trans_dir}/{self.provider}-{self.provider_id}-{self.sensor}.json"
        )
