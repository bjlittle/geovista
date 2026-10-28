# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.to_lonlat`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.common import to_lonlat
from geovista.globe import Globe

#: A render radius of 1, and the Earth's radius.
RADII = [1.0, 6378137.0]


@pytest.mark.parametrize(
    ("point", "emsg"),
    [
        (0, r"Require a 1D array .* got a 0D array"),
        ([0], r"Require a 1D array .* got a 1D array with shape \(1,\)"),
        ([0, 1], r"Require a 1D array .* got a 1D array with shape \(2,\)"),
    ],
)
def test_shape_fail(point, emsg):
    """Test trap of non-compliant cartesian point array shape."""
    with pytest.raises(ValueError, match=emsg):
        _ = to_lonlat(point)


def test_to_degrees(degrees):
    """Test conversion from XYZ cartesian point to geographical degrees."""
    lonlat = to_lonlat(degrees.xyz)
    np.testing.assert_array_almost_equal(lonlat, degrees.expected)


def test_to_radians(radians):
    """Test conversion from XYZ cartesian point to geographical radians."""
    lonlat = to_lonlat(radians.xyz, radians=True)
    np.testing.assert_array_almost_equal(lonlat, radians.expected)


def test_list(degrees):
    """A point given as a list is the point given as an array (typing spec §3.3)."""
    point = np.asarray(degrees.xyz, dtype=float)

    np.testing.assert_array_equal(to_lonlat(point.tolist()), to_lonlat(point))


@pytest.mark.parametrize("radius", RADII)
def test_the_globe_sets_the_radius(degrees, radius):
    """Test a point at the render radius of the globe given reads back."""
    point = np.asarray(degrees.xyz, dtype=float) * radius
    lonlat = to_lonlat(point, globe=Globe(render_radius=radius))
    np.testing.assert_array_almost_equal(lonlat, degrees.expected)


def test_a_number_is_not_a_globe(degrees):
    """Test a number given as the globe is refused."""
    with pytest.raises(TypeError, match=r"globe must be a geovista\.Globe"):
        _ = to_lonlat(degrees.xyz, globe=2.0)


def test_radius_is_gone(degrees):
    """Test the radius keyword is refused."""
    with pytest.raises(TypeError, match="radius"):
        _ = to_lonlat(degrees.xyz, radius=2.0)
