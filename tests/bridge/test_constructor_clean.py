# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests of the meshes that the constructor of a transform cleans."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.bridge import NAME_CELLS, NAME_POINTS, Transform

#: The corners of a square, and a second point on its last corner.
XS = [0.0, 10.0, 10.0, 0.0, 0.0]
YS = [0.0, 0.0, 10.0, 10.0, 10.0]


def cells(mesh):
    """Return the type and the point indices of each cell of the mesh, in order."""
    return [
        (cell.type, tuple(cell.point_ids))
        for cell in (mesh.get_cell(i) for i in range(mesh.n_cells))
    ]


@pytest.mark.parametrize(
    ("connectivity", "data", "name"),
    [
        ([[0, 1, 2, 3], [0, 1, 1, 1]], [10.0, 20.0], NAME_CELLS),
        ([[0, 1, 2, 4]], [1.0, 2.0, 3.0, 4.0, 5.0], NAME_POINTS),
    ],
    ids=["face-made-a-line", "point-merged"],
)
def test_cleans_once_the_data_is_attached(connectivity, data, name):
    """Test the constructor cleans a mesh after attaching its data.

    So it builds what from_unstructured builds. Cleaning makes a face of one
    repeated point a line, which comes before the quad, and merges a point with
    the one it lies on.

    """
    expected = Transform.from_unstructured(
        XS, YS, connectivity=connectivity, data=data, clean=True
    )
    result = Transform(XS, YS, connectivity=connectivity, clean=True)(data=data)
    assert cells(result) == cells(expected)
    np.testing.assert_allclose(result.points, expected.points)
    np.testing.assert_array_equal(result[name], expected[name])
