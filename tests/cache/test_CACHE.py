# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.cache.CACHE`."""

from __future__ import annotations

from pathlib import Path

import pytest

from geovista.cache import CACHE


def test_fetch():
    """Test the download of an asset."""
    asset = Path("pantry/data/lams/london.nc.bz2")
    asset_cache = CACHE.abspath / asset
    asset_cache.unlink(missing_ok=True)
    actual = CACHE.fetch(asset.as_posix())
    assert asset.name == Path(actual).name


@pytest.mark.xfail(reason="flaky HTTP 403", strict=False)
def test_fetch__no_user_agent():
    """Test the download of an asset with no user-agent header."""
    asset = Path("pantry/data/lams/polar.nc.bz2")
    asset_cache = CACHE.abspath / asset
    asset_cache.unlink(missing_ok=True)
    actual = CACHE._fetch(str(asset))
    assert asset.name == Path(actual).name
