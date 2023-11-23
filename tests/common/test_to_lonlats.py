# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.to_lonlats`."""
from __future__ import annotations

import numpy as np
import pytest

from geovista.common import to_lonlats


@pytest.mark.parametrize(
    ("points", "emsg"),
    [
        ([[[0]]], r"Require a 2-D array .* got a 3-D array"),
        ([[0, 1]], r"Require a 2-D array .* got a 2-D array with shape \(1, 2\)"),
    ],
)
def test_xyz_shape_fail(points, emsg):
    """Test trap of non-compliant cartesian points array shape."""
    with pytest.raises(ValueError, match=emsg):
        _ = to_lonlats(points)


@pytest.mark.parametrize("radius", [(1, 2), np.arange(10).reshape(5, 2)])
def test_radius_shape_fail(manydegrees, radius):
    """Test trap of non-compliant radius array shape."""
    emsg = "Require a 1-D array of radii"
    with pytest.raises(ValueError, match=emsg):
        _ = to_lonlats(manydegrees.xyz, radius=radius)


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
    lonlat = to_lonlats(poles, radius=float(radius), stacked=False)
    np.testing.assert_array_almost_equal(lonlat[1], expected)


def test_radius(manydegrees):
    """Test radii vector rather than scalar radius."""
    xyz = np.asanyarray(manydegrees.xyz)
    radii = np.ones(xyz.shape[0])
    lonlats = to_lonlats(xyz, radius=radii)
    np.testing.assert_array_almost_equal(lonlats, manydegrees.expected)
