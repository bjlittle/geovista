# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.geodesic.npoints`."""

from __future__ import annotations

import numpy as np

from geovista.geodesic import npoints

#: The start and end points of a geodesic line.
START_LON, START_LAT, END_LON, END_LAT = -10.0, 20.0, 10.0, 30.0


def test_npts_none_is_the_default():
    """An npts of None is the GEODESIC_NPTS default its docstring promises."""
    expected = npoints(START_LON, START_LAT, END_LON, END_LAT)

    result = npoints(START_LON, START_LAT, END_LON, END_LAT, npts=None)

    np.testing.assert_array_equal(result, expected)


def test_radians_none_is_degrees():
    """A radians of None reads the points as degrees, as False does."""
    expected = npoints(START_LON, START_LAT, END_LON, END_LAT, npts=5)

    result = npoints(START_LON, START_LAT, END_LON, END_LAT, npts=5, radians=None)

    np.testing.assert_array_equal(result, expected)
