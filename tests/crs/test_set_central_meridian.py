# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.crs.set_central_meridian`."""

from __future__ import annotations

import warnings

from pyproj import CRS, Transformer
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
            try:
                return float(value)
            except ValueError:
                # a named prime meridian e.g. "paris" is not a central meridian
                continue

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


@pytest.mark.parametrize("meridian", [0, 10.0, -45.0])
def test_set_central_meridian__non_degree_parameter(meridian):
    """Test that a projection parameter is rewritten in the unit it is read in.

    ``EPSG:29701`` expresses its longitude of projection centre in grad, so a
    meridian in degrees written there verbatim would be reinterpreted as grad.
    PROJ gives the parameter in degrees east of the Paris prime meridian, which it
    applies as 2 degrees 20 minutes 14.025 seconds east of Greenwich.

    """
    result = set_central_meridian(CRS.from_user_input("epsg:29701"), meridian)

    assert result is not None
    assert get_central_meridian(result) == pytest.approx(meridian, abs=1e-12)
    expected = meridian - (2 + 20 / 60 + 14.025 / 3600)
    assert _proj_central_meridian(result) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("meridian", [0, 10.0, -45.0])
def test_set_central_meridian__non_greenwich_prime_meridian(meridian):
    """Test that a meridian east of Greenwich is written east of the prime meridian.

    ``EPSG:31251`` is centred east of Ferro, which is 17 degrees 40 minutes west
    of Greenwich, so its parameter is that much greater. See :issue:`2518`.

    """
    result = set_central_meridian(CRS.from_user_input("epsg:31251"), meridian)

    assert result is not None
    assert get_central_meridian(result) == pytest.approx(meridian, abs=1e-9)
    expected = meridian + 17 + 2 / 3
    assert _proj_central_meridian(result) == pytest.approx(expected, abs=1e-9)


def test_set_central_meridian__no_central_meridian():
    """Test that a CRS with no central meridian is not rewritten."""
    assert set_central_meridian(WGS84, 0) is None


def test_set_central_meridian__non_degree_prime_meridian():
    """Test that a prime meridian in a non-degree unit is not rewritten."""
    assert set_central_meridian(CRS.from_user_input("epsg:4807"), 0) is None


def _applied(crs: CRS) -> float:
    """Return the longitude east of Greenwich that PROJ maps to the origin."""
    to_lonlat = Transformer.from_crs(crs, "+proj=longlat +ellps=WGS84", always_xy=True)
    return to_lonlat.transform(0.0, 0.0)[0]


@pytest.mark.parametrize(
    "crs", ["+proj=robin +lon_0=20 +pm=paris", "+proj=robin +lon_0=28 +pm=ferro"]
)
def test_set_central_meridian__as_proj_applies(crs):
    """Test the central meridian is the one PROJ applies, to the last digits.

    PROJ applies a prime meridian it names from its own table, where Paris is 2
    degrees 20 minutes 14.025 seconds east, but EPSG gives 2.5969213 grad, which is
    3.3e-9 degrees more. A seam cut on one while PROJ applies the other tears a
    global mesh. See :issue:`2518`.

    """
    crs = CRS.from_user_input(crs)

    assert get_central_meridian(crs) == pytest.approx(_applied(crs), abs=1e-12)
    assert _applied(set_central_meridian(crs, 0)) == pytest.approx(0, abs=1e-12)


@pytest.mark.parametrize("code", ["epsg:2963", "epsg:22300"])
def test_set_central_meridian__no_proj_string(code):
    """Test a CRS that PROJ cannot write as a PROJ string is rebased.

    ``EPSG:2963`` is on Lisbon and ``EPSG:22300`` on Paris, so the meridian is
    rebased on a prime meridian taken from the PROJ JSON. See :issue:`2518`.

    """
    result = set_central_meridian(CRS.from_user_input(code), 10.0)

    assert result is not None
    assert get_central_meridian(result) == pytest.approx(10.0, abs=1e-9)
