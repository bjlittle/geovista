# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.crs.planar`."""

from __future__ import annotations

from pyproj import CRS
import pytest

from geovista.crs import WGS84, planar

CRSS: list[str] = [
    "+proj=eqc",
    "+proj=latlong",
    "+proj=moll",
    "+proj=robin",
    "epsg:32662",
    "epsg:3857",
]


def test_wgs84():
    """Test that the only non-planar scene is WGS84."""
    assert not planar(WGS84)


@pytest.mark.parametrize("crs", [WGS84, "epsg:4326", 4326, "WGS 84"])
def test_wgs84__equivalent(crs):
    """Test that CRS equivalent to WGS84 are also not planar."""
    assert not planar(CRS.from_user_input(crs))


@pytest.mark.parametrize("crs", CRSS)
def test_planar(crs):
    """Test that a projected CRS renders a flat plane."""
    assert planar(CRS.from_user_input(crs))


def test_latlong__is_planar():
    """Test the cartopy >=0.26 ``PlateCarree`` identity.

    ``+proj=latlong`` is geographic rather than projected, so ``is_projected``
    reports ``False`` for it. The scene is nonetheless rendered flat, which is
    precisely the distinction :func:`geovista.crs.planar` draws.

    """
    crs = CRS.from_user_input("+proj=latlong")
    assert not crs.is_projected
    assert planar(crs)
