# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.crs.set_central_meridian`."""

from __future__ import annotations

import warnings

from pyproj import CRS
import pytest

from geovista.crs import WGS84, get_central_meridian, set_central_meridian

from .test_get_central_meridian import ALL_PROJECTIONS, MERIDIAN


def _proj_central_meridian(crs) -> float:
    """Read the central meridian from the PROJ definition of the `crs`."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        proj = crs.to_dict()

    # "lon_0" for most projected CRSs, "lonc" for an oblique mercator, and "pm"
    # where the datum prime meridian carries the shift e.g. cartopy >=0.26
    # PlateCarree
    for key in ("lon_0", "lonc", "pm"):
        if value := proj.get(key):
            return float(value)

    return 0.0


@pytest.mark.parametrize(
    "projection", [p for _, p in ALL_PROJECTIONS], ids=[n for n, _ in ALL_PROJECTIONS]
)
def test_set_central_meridian(projection):
    """Test that the central meridian is replaced wherever it is carried.

    Asserted against the PROJ definition rather than :func:`get_central_meridian`
    alone, since both read the same JSON serialization and would agree even if
    the replacement never reached PROJ.

    """
    crs = CRS.from_user_input(projection(central_longitude=MERIDIAN))
    result = set_central_meridian(crs, 0)

    assert result is not None
    assert not get_central_meridian(result)
    # "pm" is dropped entirely rather than set to 0 when it is the carrier
    assert not _proj_central_meridian(result)
    # the CRS is immutable, so the original must be untouched
    assert get_central_meridian(crs) == MERIDIAN
    assert _proj_central_meridian(crs) == MERIDIAN


@pytest.mark.parametrize(
    "projection", [p for _, p in ALL_PROJECTIONS], ids=[n for n, _ in ALL_PROJECTIONS]
)
def test_set_central_meridian__get_set_invariant(projection):
    """Test that a recovered central meridian can always be replaced.

    :func:`geovista.transform.transform_mesh` assigns the result of
    :func:`set_central_meridian` directly to its target CRS whenever
    :func:`get_central_meridian` reports a shift, so a recoverable central
    meridian that cannot be replaced would yield a ``None`` target CRS.

    """
    crs = CRS.from_user_input(projection(central_longitude=MERIDIAN))

    if get_central_meridian(crs):
        assert set_central_meridian(crs, 0) is not None


def test_set_central_meridian__no_central_meridian():
    """Test that a CRS with no central meridian is not rewritten."""
    assert set_central_meridian(WGS84, 0) is None


def test_set_central_meridian__non_degree_prime_meridian():
    """Test that a prime meridian in a non-degree unit is not rewritten."""
    assert set_central_meridian(CRS.from_user_input("epsg:4807"), 0) is None
