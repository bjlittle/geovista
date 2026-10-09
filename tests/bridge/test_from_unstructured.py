# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.Transform.from_unstructured`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.bridge import Transform
from geovista.crs import WGS84
from geovista.transform import transform_points

#: A planar CRS, whose coordinates are metres.
PLANAR = "+proj=eqc"

#: Two quads, side by side, as (2, 4) longitudes and latitudes.
LONS = [[0.0, 10.0, 10.0, 0.0], [20.0, 30.0, 30.0, 20.0]]
LATS = [[0.0, 0.0, 10.0, 10.0], [0.0, 0.0, 10.0, 10.0]]

#: The last point of the second quad masked.
MASK = [[False, False, False, False], [False, False, False, True]]


def _points(crs: str) -> tuple[np.ndarray, np.ndarray]:
    """Return the two quads' points in the given CRS."""
    xyz = transform_points(
        src_crs=WGS84, tgt_crs=crs, xs=np.array(LONS), ys=np.array(LATS)
    )
    return xyz[..., 0], xyz[..., 1]


@pytest.mark.parametrize("crs", [WGS84, PLANAR], ids=["wgs84", "planar"])
def test_masked_points_leave_their_faces(crs):
    """Points masked alike in x and y are dropped from the faces they belong to.

    Regressed by #1977, which sent every point through ``transform_points``
    and read the mask from what came back, which never has one. A masked point
    then stayed in its face, with its underlying value as its coordinate.

    """
    xs, ys = _points(crs)
    xs, ys = np.ma.masked_array(xs, mask=MASK), np.ma.masked_array(ys, mask=MASK)

    mesh = Transform.from_unstructured(xs, ys, crs=crs)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3, 3, 4, 5, 6])


@pytest.mark.parametrize("masked", ["xs", "ys"])
def test_points_masked_on_one_axis_stay(masked):
    """A mask on only one of x and y is not a mask on the point."""
    xs, ys = np.array(LONS), np.array(LATS)
    if masked == "xs":
        xs = np.ma.masked_array(xs, mask=MASK)
    else:
        ys = np.ma.masked_array(ys, mask=MASK)

    mesh = Transform.from_unstructured(xs, ys)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3, 4, 4, 5, 6, 7])
