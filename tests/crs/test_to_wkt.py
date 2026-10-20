# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.crs.to_wkt`."""

from __future__ import annotations

from pyproj import CRS
import pytest

from geovista.common import GV_FIELD_CRS
from geovista.crs import WGS84, from_wkt, to_wkt


def test(sphere):
    """Test OGC WKT serialization of CRS on mesh."""
    crs = WGS84
    to_wkt(sphere, crs)
    assert GV_FIELD_CRS in sphere.field_data
    wkt = WGS84.to_wkt()
    assert sphere.field_data[GV_FIELD_CRS] == wkt
    assert from_wkt(sphere) == WGS84


@pytest.mark.parametrize("code", ["EPSG:3857", "EPSG:27700", "EPSG:32630"])
def test_non_ascii(sphere, code):
    """Test a CRS whose OGC WKT holds non-ASCII text. See :issue:`2595`."""
    crs = CRS.from_user_input(code)
    assert not crs.to_wkt().isascii()
    to_wkt(sphere, crs)
    assert str(sphere.field_data[GV_FIELD_CRS][0]).isascii()
    result = from_wkt(sphere)
    assert result is not None
    assert result == crs
    # pyproj's own round trip of the text, which differs for EPSG:3857
    assert result.to_wkt() == CRS.from_wkt(crs.to_wkt()).to_wkt()


def test_backslash(sphere):
    """Test a CRS whose OGC WKT holds a backslash round trips exactly."""
    crs = CRS.from_wkt(WGS84.to_wkt().replace('"WGS 84"', r'"WGS\u00b0 84"', 1))
    to_wkt(sphere, crs)
    result = from_wkt(sphere)
    assert result is not None
    assert result.name == r"WGS\u00b0 84"
    assert result.to_wkt() == CRS.from_wkt(crs.to_wkt()).to_wkt()
