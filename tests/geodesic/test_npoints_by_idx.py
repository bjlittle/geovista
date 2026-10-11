# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.geodesic.npoints_by_idx`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.geodesic import npoints_by_idx

#: Three points along a geodesic, as longitudes and latitudes.
LONS, LATS = [-10.0, 0.0, 10.0], [20.0, 25.0, 30.0]


def test_npts_none_is_the_default():
    """An npts of None is the GEODESIC_NPTS default its docstring promises."""
    expected = npoints_by_idx(LONS, LATS, start_idx=0, end_idx=1)

    result = npoints_by_idx(LONS, LATS, start_idx=0, end_idx=1, npts=None)

    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize("convert", [tuple, np.array], ids=["tuple", "array"])
def test_lists(convert):
    """Lists are the points given in any other array_like (typing spec §3.3)."""
    expected = npoints_by_idx(
        convert(LONS), convert(LATS), start_idx=0, end_idx=2, npts=5
    )

    result = npoints_by_idx(LONS, LATS, start_idx=0, end_idx=2, npts=5)

    np.testing.assert_array_equal(result, expected)
