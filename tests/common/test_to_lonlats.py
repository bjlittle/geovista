# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.to_lonlats`, and its private float form."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.common import _to_lonlats, to_lonlats
from geovista.globe import Globe

#: A render radius of 1, and the Earth's radius.
RADII = [1.0, 6378137.0]


@pytest.mark.parametrize(
    ("points", "emsg"),
    [
        ([[[0]]], r"Require a 2D array .* got a 3D array"),
        ([[0, 1]], r"Require a 2D array .* got a 2D array with shape \(1, 2\)"),
    ],
)
def test_xyz_shape_fail(points, emsg):
    """Test trap of non-compliant cartesian points array shape."""
    with pytest.raises(ValueError, match=emsg):
        _ = to_lonlats(points)


@pytest.mark.parametrize("radius", [(1, 2), np.arange(10).reshape(5, 2)])
def test_radius_shape_fail(manydegrees, radius):
    """Test trap of non-compliant radius array shape."""
    emsg = "Require a 1D array of radii"
    with pytest.raises(ValueError, match=emsg):
        _ = _to_lonlats(manydegrees.xyz, radius=radius)


@pytest.mark.parametrize("stacked", [True, False])
def test_to_degrees(manydegrees, stacked):
    """Test conversion from XYZ cartesian points to geographic degrees."""
    lonlats = to_lonlats(manydegrees.xyz, stacked=stacked)
    expected = manydegrees.expected if stacked else np.array(manydegrees.expected).T
    np.testing.assert_array_almost_equal(lonlats, expected)


@pytest.mark.parametrize("stacked", [True, False])
def test_to_radians(manyradians, stacked):
    """Test conversion from XYZ cartesian points to geographic radians."""
    lonlats = to_lonlats(manyradians.xyz, radians=True, stacked=stacked)
    expected = manyradians.expected if stacked else np.array(manyradians.expected).T
    np.testing.assert_array_almost_equal(lonlats, expected)


@pytest.mark.parametrize("radius", np.linspace(1.0, 0.99999))
def test_latitude_pole_arcsin_domain(radius):
    """Test tolerance of (z / r) to latitude arcsin domain."""
    poles = [(0.0, 0.0, 1.0), (0.0, 0.0, -1.0)]
    expected = [90.0, -90.0]
    lonlat = to_lonlats(poles, globe=Globe(render_radius=float(radius)), stacked=False)
    np.testing.assert_array_almost_equal(lonlat[1], expected)


def test_radius(manydegrees):
    """Test radii vector rather than scalar radius."""
    xyz = np.asanyarray(manydegrees.xyz)
    radii = np.ones(xyz.shape[0])
    lonlats = _to_lonlats(xyz, radius=radii)
    np.testing.assert_array_almost_equal(lonlats, manydegrees.expected)


def test_nested_lists(manydegrees):
    """Nested lists are the points given as an array (typing spec §3.3)."""
    points = np.asarray(manydegrees.xyz, dtype=float)

    np.testing.assert_array_equal(to_lonlats(points.tolist()), to_lonlats(points))


@pytest.mark.parametrize("radius", RADII)
def test_the_globe_sets_the_radius(manydegrees, radius):
    """Test points at the render radius of the globe given read back."""
    points = np.asarray(manydegrees.xyz, dtype=float) * radius
    lonlats = to_lonlats(points, globe=Globe(render_radius=radius))
    np.testing.assert_array_almost_equal(lonlats, manydegrees.expected)


def test_a_number_is_not_a_globe(manydegrees):
    """Test a number given as the globe is refused."""
    with pytest.raises(TypeError, match=r"globe must be a geovista\.Globe"):
        _ = to_lonlats(manydegrees.xyz, globe=2.0)


def test_radius_is_gone(manydegrees):
    """Test the radius keyword is refused."""
    with pytest.raises(TypeError, match="radius"):
        _ = to_lonlats(manydegrees.xyz, radius=2.0)
