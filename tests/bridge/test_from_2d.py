# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.Transform.from_2d`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.bridge import Transform

#: An orthographic projection, which cannot reach the far side of the globe.
ORTHO = "+proj=ortho +lat_0=0 +lon_0=0"

#: A coordinate in metres that lies far outside the disk of ``ORTHO``.
OFF_DISK = 1e9

#: The faces of a (4, 4) grid that do not touch its middle node, row by row.
AROUND_THE_MIDDLE = [0, 1, 2, 3, 4, 7, 8, 11, 12, 13, 14, 15]


def _nodes(step: float = 10.0) -> tuple[np.ma.MaskedArray, np.ma.MaskedArray]:
    """Return the (5, 5) nodes of a (4, 4) grid of quads, the middle node masked."""
    xs, ys = np.meshgrid(np.arange(5) * step, np.arange(5) * step)
    mask = np.zeros((5, 5), dtype=bool)
    mask[2, 2] = True
    return np.ma.masked_array(xs, mask=mask), np.ma.masked_array(ys, mask=mask)


def test_faces_with_a_masked_node_are_dropped():
    """The four faces that share a masked node are dropped, with a warning.

    The node has no position, so each of them would have a vertex with none.
    Before, they were built from the value under the mask (#2621).

    """
    xs, ys = _nodes()

    wmsg = "defines 4 faces that use a masked point, which are dropped"
    with pytest.warns(UserWarning, match=wmsg):
        mesh = Transform.from_2d(xs, ys)

    assert mesh.n_cells == 12
    assert mesh.n_points == 25


def test_face_with_a_masked_corner_is_dropped():
    """A face whose own corner is masked is dropped from (M, N, 4) points."""
    lons = np.array([[0.0, 10.0, 10.0, 0.0], [10.0, 20.0, 20.0, 10.0]])
    lats = np.array([[0.0, 0.0, 10.0, 10.0], [0.0, 0.0, 10.0, 10.0]])
    mask = np.zeros((1, 2, 4), dtype=bool)
    mask[0, 1, 2] = True
    xs = np.ma.masked_array(lons.reshape(1, 2, 4), mask=mask)
    ys = np.ma.masked_array(lats.reshape(1, 2, 4), mask=mask)

    wmsg = "defines 1 face that uses a masked point, which is dropped"
    with pytest.warns(UserWarning, match=wmsg):
        mesh = Transform.from_2d(xs, ys)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3])


def test_masked_node_outside_the_domain():
    """A masked node that a bounded projection cannot reach is no error."""
    xs, ys = _nodes(step=1e5)
    xs[2, 2] = ys[2, 2] = OFF_DISK
    xs[2, 2] = ys[2, 2] = np.ma.masked

    with pytest.warns(UserWarning, match="use a masked point"):
        mesh = Transform.from_2d(xs, ys, crs=ORTHO)

    assert mesh.n_cells == 12


def test_cell_data_follows_the_faces_that_remain():
    """Data with a value for each face of the grid keeps those that remain."""
    xs, ys = _nodes()
    data = np.arange(16.0).reshape(4, 4)

    with pytest.warns(UserWarning, match="use a masked point"):
        mesh = Transform.from_2d(xs, ys, data=data, name="cells")

    np.testing.assert_array_equal(mesh.cell_data["cells"], AROUND_THE_MIDDLE)


def test_point_data_stays_on_every_node():
    """Data with a value for each node is still point data, as no node is dropped."""
    xs, ys = _nodes()
    data = np.arange(25.0)

    with pytest.warns(UserWarning, match="use a masked point"):
        mesh = Transform.from_2d(xs, ys, data=data, name="nodes")

    np.testing.assert_array_equal(mesh.point_data["nodes"], data)
