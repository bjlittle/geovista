# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.Transform.from_1d`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.bridge import Transform

#: The bounds of three faces along an axis, as (N+1,) edges and as (N, 2) pairs.
EDGES = [0.0, 10.0, 20.0, 30.0]
PAIRS = [[0.0, 10.0], [10.0, 20.0], [20.0, 30.0]]

#: The bounds of two faces along the other axis.
OTHER = [0.0, 10.0, 20.0]

#: The bounds, those of them to mask, and how many that is.
MASKED = {
    "edges-first": (EDGES, [0], 1),
    "edges-interior": (EDGES, [1], 1),
    "edges-last": (EDGES, [3], 1),
    "pairs-first": (PAIRS, [(0, 0)], 1),
    "pairs-one-copy": (PAIRS, [(0, 1)], 1),
    "pairs-both-copies": (PAIRS, [(0, 1), (1, 0)], 2),
    "pairs-last": (PAIRS, [(2, 1)], 1),
}


@pytest.mark.parametrize("axis", ["x", "y"])
@pytest.mark.parametrize(
    ("bounds", "masked", "count"), MASKED.values(), ids=MASKED.keys()
)
def test_masked_bound_raises(axis, bounds, masked, count):
    """A masked bound is a gap in a contiguous axis, so it raises.

    That holds for an interior bound of (N, 2) pairs with only one of its two
    copies masked. Before, a masked bound was used as its fill value, or became
    a NaN point (#2627).

    """
    mask = np.zeros(np.shape(bounds), dtype=bool)
    for index in masked:
        mask[index] = True
    bounds = np.ma.masked_array(bounds, mask=mask)
    xs, ys = (bounds, OTHER) if axis == "x" else (OTHER, bounds)

    emsg = f"{axis}-axis array with no masked bounds, got '{count}'"
    with pytest.raises(ValueError, match=emsg):
        _ = Transform.from_1d(xs, ys)


@pytest.mark.parametrize("bounds", [EDGES, PAIRS], ids=["edges", "pairs"])
def test_masked_array_with_no_bound_masked(bounds):
    """A masked array that masks none of its bounds builds as an array does."""
    expected = Transform.from_1d(bounds, OTHER)
    xs = np.ma.masked_array(bounds, mask=np.zeros(np.shape(bounds), dtype=bool))
    ys = np.ma.masked_array(OTHER, mask=np.zeros(3, dtype=bool))

    mesh = Transform.from_1d(xs, ys)

    np.testing.assert_array_equal(mesh.points, expected.points)
    np.testing.assert_array_equal(mesh.faces, expected.faces)
