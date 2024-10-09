from __future__ import annotations

import cleanobs as C


def test_settings():
    settings = C.get_settings()
    assert settings.raw_dir.is_dir()
    assert settings.trans_dir.is_dir()
    assert settings.era5_dir.is_dir()
    assert settings.constituents_dir.is_dir()
