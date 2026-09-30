# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.crs.get_central_meridian`."""

from __future__ import annotations

import cartopy.crs as ccrs
from pyproj import CRS
import pytest

from geovista.crs import WGS84, get_central_meridian

MERIDIAN: float = 180.0

#: Projections carrying the central meridian as an EPSG conversion parameter.
EPSG_PROJECTIONS = [
    # EPSG:8802, longitude of natural origin
    ("Mercator", ccrs.Mercator),
    ("Mollweide", ccrs.Mollweide),
    ("Robinson", ccrs.Robinson),
    ("Sinusoidal", ccrs.Sinusoidal),
    # EPSG:8822, longitude of false origin
    ("AlbersEqualArea", ccrs.AlbersEqualArea),
    ("EquidistantConic", ccrs.EquidistantConic),
    ("LambertConformal", ccrs.LambertConformal),
    # EPSG:8812, longitude of projection centre
    ("ObliqueMercator", ccrs.ObliqueMercator),
    # EPSG:8835, longitude of topocentric origin
    ("NearsidePerspective", ccrs.NearsidePerspective),
]

#: Projections carrying the central meridian outside an EPSG conversion parameter.
NON_EPSG_PROJECTIONS = [
    # PROJ-native method, "lon_0" with no EPSG identifier
    ("Hammer", ccrs.Hammer),
    # datum prime meridian for cartopy >=0.26, EPSG:8802 otherwise
    ("PlateCarree", ccrs.PlateCarree),
]

ALL_PROJECTIONS = EPSG_PROJECTIONS + NON_EPSG_PROJECTIONS


@pytest.mark.parametrize(
    "projection", [p for _, p in ALL_PROJECTIONS], ids=[n for n, _ in ALL_PROJECTIONS]
)
def test_central_meridian(projection):
    """Test that a shifted central meridian is recovered."""
    crs = CRS.from_user_input(projection(central_longitude=MERIDIAN))
    assert get_central_meridian(crs) == MERIDIAN


@pytest.mark.parametrize(
    "projection", [p for _, p in ALL_PROJECTIONS], ids=[n for n, _ in ALL_PROJECTIONS]
)
def test_central_meridian__default(projection):
    """Test that a default projection is never reported as unrecoverable.

    Note that a default central meridian is not necessarily ``0``, as some
    projections carry an opinionated default e.g. :class:`cartopy.crs.
    LambertConformal` is centred on ``-96``.

    """
    crs = CRS.from_user_input(projection())

    # "filterwarnings = error" promotes an unrecoverable central meridian
    # warning to a failure here
    result = get_central_meridian(crs)

    assert result is None or isinstance(result, float)


@pytest.mark.parametrize("meridian", [-180.0, -90.0, -1.5, 1.5, 90.0, 180.0])
def test_central_meridian__roundtrip(meridian):
    """Test that an arbitrary central meridian is recovered verbatim."""
    crs = CRS.from_user_input(ccrs.EquidistantConic(central_longitude=meridian))
    assert get_central_meridian(crs) == meridian


@pytest.mark.parametrize(
    "crs",
    [WGS84, CRS.from_user_input("epsg:4326"), CRS.from_user_input(ccrs.Geodetic())],
    ids=["WGS84", "epsg:4326", "Geodetic"],
)
def test_central_meridian__geographic(crs):
    """Test that a geographic CRS has no central meridian, and never warns."""
    assert get_central_meridian(crs) is None


def test_central_meridian__non_degree_prime_meridian():
    """Test that a prime meridian in a non-degree unit is not misreported.

    ``EPSG:4807`` (NTF Paris) expresses its prime meridian in grad, so its value
    must not be taken for a central meridian in degrees.

    """
    crs = CRS.from_user_input("epsg:4807")
    assert crs.prime_meridian.unit_name == "grad"
    assert get_central_meridian(crs) is None


@pytest.mark.parametrize(
    "crs",
    [
        ccrs.RotatedPole(pole_longitude=0, pole_latitude=45),
        ccrs.RotatedPole(pole_longitude=MERIDIAN, pole_latitude=45),
        ccrs.RotatedGeodetic(MERIDIAN, 45),
    ],
    ids=["RotatedPole", "RotatedPole__shifted", "RotatedGeodetic"],
)
def test_central_meridian__rotated_pole_warns(crs):
    """Test that an unrecoverable central meridian is reported, not swallowed.

    A rotated pole expresses its origin relative to the rotated pole, which is
    not faithfully described by a scalar central meridian. See :issue:`2512`.

    """
    with pytest.warns(UserWarning, match="unable to determine the central meridian"):
        result = get_central_meridian(CRS.from_user_input(crs))

    assert result is None
