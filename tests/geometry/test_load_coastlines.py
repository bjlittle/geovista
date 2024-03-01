# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-test for :func:`geovista.geometry.load_coastlines`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.common import (
    COASTLINES_RESOLUTION,
    GV_FIELD_CRS,
    GV_FIELD_RADIUS,
    GV_FIELD_RESOLUTION,
    RADIUS,
    ZLEVEL_SCALE,
    distance,
)
from geovista.geometry import load_coastlines as load


def test_defaults(wgs84_wkt):
    """Test expected defaults are honoured."""
    result = load()
    assert result[GV_FIELD_RADIUS] == RADIUS
    assert result[GV_FIELD_RESOLUTION] == COASTLINES_RESOLUTION
    assert result[GV_FIELD_CRS] == wgs84_wkt


def test_resolution_metadata(resolution):
    """Test field data contains the correct resolution metadata."""
    result = load(resolution=resolution)
    assert result[GV_FIELD_RESOLUTION][0] == resolution


def test_crs_metadata(resolution, wgs84_wkt):
    """Test field data contains the correct crs metadata."""
    result = load(resolution=resolution)
    assert result[GV_FIELD_CRS] == wgs84_wkt


def test_lines(resolution):
    """Test coastline mesh consists of lines."""
    result = load(resolution=resolution)
    assert result.n_cells == result.n_lines


@pytest.mark.parametrize("radius", np.linspace(0.5, 1.5, num=5))
def test_radius(resolution, radius):
    """Test coastline z-control with radius."""
    result = load(resolution=resolution, radius=radius)
    actual = distance(result)
    assert np.isclose(actual, radius)


@pytest.mark.parametrize("zlevel", range(-5, 6))
def test_zlevel(resolution, zlevel):
    """Test coastline z-control with zlevel."""
    result = load(resolution=resolution, zlevel=zlevel)
    actual = distance(result)
    expected = RADIUS + RADIUS * zlevel * ZLEVEL_SCALE
    assert np.isclose(actual, expected)


@pytest.mark.parametrize("zlevel", [0, 1])
@pytest.mark.parametrize("zscale", np.linspace(-1, 1, num=5))
def test_zscale(resolution, zlevel, zscale):
    """Test coastline z-control with zscale with no zlevel."""
    result = load(resolution=resolution, zlevel=zlevel, zscale=zscale)
    actual = distance(result)
    expected = RADIUS + RADIUS * zlevel * zscale
    assert np.isclose(actual, expected)
