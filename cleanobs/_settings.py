from __future__ import annotations

import functools
import os
import pathlib

import pydantic
import pydantic_core
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

_ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(validate_default=True)

    data_dir: pathlib.Path = pathlib.Path(_ROOT_DIR) / "data"

    @pydantic.computed_field
    @property
    def raw_dir(self) -> pathlib.Path:
        return self.data_dir / "raw"

    @pydantic.computed_field
    @property
    def trans_dir(self) -> pathlib.Path:
        return self.data_dir / "trans"

    @pydantic.computed_field
    @property
    def era5_dir(self) -> pathlib.Path:
        return self.data_dir / "era5"

    @pydantic.computed_field
    @property
    def constituents_dir(self) -> pathlib.Path:
        return self.data_dir / "const"


def get_settings():
    settings = Settings()
    if "PYTEST_CURRENT_TEST" in os.environ:
        os.environ["data_dir"] = str(_ROOT_DIR / "tests/data")
        settings.__init__()
    return settings
