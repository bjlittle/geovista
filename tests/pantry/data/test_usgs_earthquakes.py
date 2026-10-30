# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.pantry.data.usgs_earthquakes`."""

from __future__ import annotations

import pytest

from geovista.pantry.data import usgs_earthquakes


@pytest.fixture
def fresh():
    """Load the sample afresh, rather than from the cache of an earlier test."""
    usgs_earthquakes.cache_clear()
    yield usgs_earthquakes
    usgs_earthquakes.cache_clear()


def test_sample(fresh):
    """Test the sample reads its points, keeping each of magnitude 2.5 or more.

    Any warning the read raises fails this test, as the suite makes warnings
    errors, so it also guards the parquet engine against deprecation.

    """
    sample = fresh()

    assert sample.lons.shape == sample.lats.shape == sample.zlevel.shape
    assert sample.data.shape == sample.lons.shape
    assert sample.lons.size > 0
    assert (sample.data >= 2.5).all()


@pytest.mark.parametrize("missing", ["pandas", "pyarrow"])
def test_missing_dependency(fresh, mocker, missing):
    """Test each optional dependency the sample needs is named when it is absent."""
    from importlib.util import find_spec  # noqa: PLC0415

    _ = mocker.patch(
        "geovista.pantry.data.find_spec",
        side_effect=lambda name: None if name == missing else find_spec(name),
    )
    emsg = "Optional dependencies 'pandas' and 'pyarrow' are required"

    with pytest.raises(ImportError, match=emsg):
        _ = fresh()
