# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.pantry.fetch_raster`."""

from __future__ import annotations

import pytest

from geovista.pantry import fetch_raster


def test_fetch_raster():
    """Test retrieval of raster asset."""
    expected = "bahamas_rgb.tif"
    actual = fetch_raster(expected)
    assert actual.name == expected
    assert actual.exists()


def test_fetch_raster_fail():
    """Test retrieval of non-existent raster asset."""
    fname = "bad.tif"
    emsg = f"File 'raster/{fname}.bz2' is not in the registry."
    with pytest.raises(ValueError, match=emsg):
        _ = fetch_raster(fname)
