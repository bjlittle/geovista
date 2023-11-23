# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.to_lonlat`."""
from __future__ import annotations

import numpy as np
import pytest

from geovista.common import to_lonlat


@pytest.mark.parametrize(
    ("point", "emsg"),
    [
        (0, r"Require a 1-D array .* got a 0-D array"),
        ([0], r"Require a 1-D array .* got a 1-D array with shape \(1,\)"),
        ([0, 1], r"Require a 1-D array .* got a 1-D array with shape \(2,\)"),
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
