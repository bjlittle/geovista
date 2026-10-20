# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.crs.to_wkt`."""

from __future__ import annotations

from pyproj import CRS
import pytest
import pyvista as pv

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


def test_ascii_unmarked(sphere):
    """Test WKT that escaping leaves unchanged is stored as it is, unmarked."""
    to_wkt(sphere, WGS84)
    assert sphere.field_data[GV_FIELD_CRS].tolist() == [WGS84.to_wkt()]


@pytest.mark.parametrize(
    "crs",
    [
        CRS.from_user_input("EPSG:3857"),
        CRS.from_wkt(WGS84.to_wkt().replace('"WGS 84"', r'"WGS\u00b0 84"', 1)),
    ],
    ids=["non-ascii", "backslash"],
)
def test_escaped_marked(sphere, crs):
    """Test escaped WKT is stored with a second element naming the encoding."""
    to_wkt(sphere, crs)
    stored = sphere.field_data[GV_FIELD_CRS].tolist()
    assert stored == [crs.to_wkt().encode("unicode_escape").decode(), "unicode_escape"]


@pytest.mark.parametrize("code", ["EPSG:3857", "EPSG:4326"])
def test_saved(sphere, tmp_path, code):
    """Test the CRS survives saving the mesh to disk and reading it back."""
    crs = CRS.from_user_input(code)
    to_wkt(sphere, crs)
    fname = tmp_path / "mesh.vtp"
    sphere.save(fname)
    result = from_wkt(pv.read(fname))
    assert result is not None
    assert result.to_wkt() == CRS.from_wkt(crs.to_wkt()).to_wkt()
