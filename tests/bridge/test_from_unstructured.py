# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.Transform.from_unstructured`."""

from __future__ import annotations

import numpy as np
from pyproj.exceptions import ProjError
import pytest

from geovista.bridge import Transform
from geovista.crs import WGS84
from geovista.transform import transform_points

#: A planar CRS, whose coordinates are metres.
PLANAR = "+proj=eqc"

#: An orthographic projection, which cannot reach the far side of the globe.
ORTHO = "+proj=ortho +lat_0=0 +lon_0=0"

#: A coordinate in metres that lies far outside the disk of ``ORTHO``.
OFF_DISK = 1e9

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


@pytest.mark.parametrize("connectivity", [None, (2, 4)], ids=["shape", "tuple"])
@pytest.mark.parametrize("crs", [WGS84, PLANAR], ids=["wgs84", "planar"])
def test_masked_points_leave_their_faces(crs, connectivity):
    """Points masked alike in x and y are dropped from the faces they belong to.

    So they are whether the connectivity is taken from the shape of the points
    or given as a tuple. Regressed by #1977, which sent every point through
    ``transform_points`` and read the mask from what came back, which never has
    one. A masked point then stayed in its face, with its underlying value as
    its coordinate.

    """
    xs, ys = _points(crs)
    xs, ys = np.ma.masked_array(xs, mask=MASK), np.ma.masked_array(ys, mask=MASK)

    mesh = Transform.from_unstructured(xs, ys, connectivity=connectivity, crs=crs)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3, 3, 4, 5, 6])


@pytest.mark.parametrize("connectivity", [None, (2, 4)], ids=["shape", "tuple"])
def test_masked_point_outside_the_domain(connectivity):
    """A masked point that a bounded projection cannot reach is no error.

    Its coordinates mean nothing, so a fill value outside the domain is
    ordinary. Every point went through ``transform_points``, which checks for
    errors, before the mask was used (#2603).

    """
    xs, ys = _points(ORTHO)
    xs[1, 3] = ys[1, 3] = OFF_DISK
    xs, ys = np.ma.masked_array(xs, mask=MASK), np.ma.masked_array(ys, mask=MASK)

    mesh = Transform.from_unstructured(xs, ys, connectivity=connectivity, crs=ORTHO)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3, 3, 4, 5, 6])


@pytest.mark.parametrize(
    "connectivity", [None, [[1, 2, 3], [4, 5, 6]]], ids=["shape", "array"]
)
@pytest.mark.parametrize(
    "crs", [WGS84, PLANAR, ORTHO], ids=["wgs84", "planar", "ortho"]
)
def test_masked_points_do_not_stretch_the_bounds(crs, connectivity):
    """The bounds of the mesh are those of the points that are not masked.

    A masked point that belongs to no face still stays in the mesh. Here the
    first and last points are masked, over values that lie far to the south-west
    of the two quads, and the connectivity array uses neither of them.

    """
    mask = np.array(MASK)
    mask[0, 0] = True
    xs, ys = _points(crs)
    far = transform_points(src_crs=WGS84, tgt_crs=crs, xs=-80.0, ys=-60.0)
    xs[mask], ys[mask] = far[0, 0], far[0, 1]
    xs, ys = np.ma.masked_array(xs, mask=mask), np.ma.masked_array(ys, mask=mask)

    # the array leaves out the first point, so it cannot be told from one-based
    mesh = Transform.from_unstructured(
        xs, ys, connectivity=connectivity, start_index=0, crs=crs
    )

    # x spans cos(10)cos(30) to cos(10), y spans 0 to sin(30), z spans 0 to sin(10)
    expected = [0.8528685, 0.9848078, 0.0, 0.5, 0.0, 0.1736482]
    np.testing.assert_allclose(mesh.bounds, expected, atol=1e-6)


def test_unmasked_point_outside_the_domain_raises():
    """A mask elsewhere does not excuse a point the projection cannot reach."""
    xs, ys = _points(ORTHO)
    xs[1, 2] = ys[1, 2] = OFF_DISK
    xs, ys = np.ma.masked_array(xs, mask=MASK), np.ma.masked_array(ys, mask=MASK)

    with pytest.raises(ProjError, match="outside of projection domain"):
        _ = Transform.from_unstructured(xs, ys, crs=ORTHO)


@pytest.mark.parametrize("crs", [WGS84, ORTHO], ids=["wgs84", "ortho"])
def test_every_point_masked(crs):
    """With every point masked there is nothing to transform, and no face."""
    xs = np.ma.masked_array(np.full((2, 4), OFF_DISK), mask=True)
    ys = np.ma.masked_array(np.full((2, 4), OFF_DISK), mask=True)

    wmsg = "defines 2 faces with fewer than three vertices, which are dropped"
    with pytest.warns(UserWarning, match=wmsg):
        mesh = Transform.from_unstructured(xs, ys, crs=crs)

    assert mesh.n_cells == 0


@pytest.mark.parametrize("base", [0, 1], ids=["zero-based", "one-based"])
def test_unused_masked_point_outside_the_domain(base):
    """A masked point that no face of a connectivity array uses is no error.

    Nothing depends on its coordinates, but every point of a connectivity array
    went through ``transform_points``, which checks for errors (#2625).

    """
    xs, ys = _points(ORTHO)
    xs[1, 3] = ys[1, 3] = OFF_DISK
    xs, ys = np.ma.masked_array(xs, mask=MASK), np.ma.masked_array(ys, mask=MASK)
    connectivity = np.array([[0, 1, 2], [4, 5, 6]]) + base

    mesh = Transform.from_unstructured(xs, ys, connectivity=connectivity, crs=ORTHO)

    np.testing.assert_array_equal(mesh.faces, [3, 0, 1, 2, 3, 4, 5, 6])


def test_masked_connectivity_does_not_use_a_masked_point():
    """A masked index is no use of the point, so a mask on both is no error."""
    xs, ys = _points(ORTHO)
    xs[1, 3] = ys[1, 3] = OFF_DISK
    xs, ys = np.ma.masked_array(xs, mask=MASK), np.ma.masked_array(ys, mask=MASK)
    connectivity = np.ma.masked_array(np.arange(8).reshape(2, 4), mask=MASK)

    mesh = Transform.from_unstructured(xs, ys, connectivity=connectivity, crs=ORTHO)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3, 3, 4, 5, 6])


def test_face_with_too_few_points_that_uses_a_masked_point():
    """A face with both faults is dropped once, for its masked point.

    Masked connectivity leaves the second face with two points, and one of them
    is masked over a value the projection cannot reach.

    """
    mask = np.zeros((2, 4), dtype=bool)
    mask[1, 1] = True
    xs, ys = _points(ORTHO)
    xs[mask], ys[mask] = OFF_DISK, OFF_DISK
    xs, ys = np.ma.masked_array(xs, mask=mask), np.ma.masked_array(ys, mask=mask)
    connectivity = np.ma.masked_array(
        np.arange(8).reshape(2, 4), mask=[[0, 0, 0, 0], [0, 0, 1, 1]]
    )

    wmsg = "defines 1 face that uses a masked point, which is dropped"
    with pytest.warns(UserWarning, match=wmsg):
        mesh = Transform.from_unstructured(xs, ys, connectivity=connectivity, crs=ORTHO)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3])


def test_face_that_uses_a_masked_point_outside_the_domain():
    """A face that uses a masked point is dropped before the point can raise.

    The last point is masked over a value the projection cannot reach, as is
    the fourth, which no face uses.

    """
    mask = np.array(MASK)
    mask[0, 3] = True
    xs, ys = _points(ORTHO)
    xs[mask], ys[mask] = OFF_DISK, OFF_DISK
    xs, ys = np.ma.masked_array(xs, mask=mask), np.ma.masked_array(ys, mask=mask)
    connectivity = [[0, 1, 2], [4, 5, 7]]

    wmsg = "defines 1 face that uses a masked point, which is dropped"
    with pytest.warns(UserWarning, match=wmsg):
        mesh = Transform.from_unstructured(xs, ys, connectivity=connectivity, crs=ORTHO)

    np.testing.assert_array_equal(mesh.faces, [3, 0, 1, 2])


def test_face_that_uses_a_masked_point_is_dropped():
    """A face of a connectivity array that uses a masked point is dropped.

    The point has no position, so the face would have a vertex with none. Before,
    the face was built from the value under the mask (#2621).

    """
    xs, ys = np.ma.masked_array(LONS, mask=MASK), np.ma.masked_array(LATS, mask=MASK)
    connectivity = np.arange(8).reshape(2, 4)

    wmsg = "defines 1 face that uses a masked point, which is dropped"
    with pytest.warns(UserWarning, match=wmsg):
        mesh = Transform.from_unstructured(xs, ys, connectivity=connectivity)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3])


def test_every_face_uses_a_masked_point():
    """With a masked point in every face, the mesh keeps its points and no face."""
    mask = np.array(MASK)
    mask[0, 0] = True
    xs, ys = np.ma.masked_array(LONS, mask=mask), np.ma.masked_array(LATS, mask=mask)
    connectivity = np.arange(8).reshape(2, 4)

    wmsg = "defines 2 faces that use a masked point, which are dropped"
    with pytest.warns(UserWarning, match=wmsg):
        mesh = Transform.from_unstructured(xs, ys, connectivity=connectivity)

    assert mesh.n_cells == 0
    assert mesh.n_points == 8


def test_cell_data_follows_the_faces_that_remain():
    """Data with a value for each face given keeps those of the faces that remain."""
    mask = np.array(MASK)[::-1]
    xs, ys = np.ma.masked_array(LONS, mask=mask), np.ma.masked_array(LATS, mask=mask)
    connectivity = np.arange(8).reshape(2, 4)

    with pytest.warns(UserWarning, match="uses a masked point"):
        mesh = Transform.from_unstructured(
            xs, ys, connectivity=connectivity, data=[10.0, 20.0], name="cells"
        )

    np.testing.assert_array_equal(mesh.cell_data["cells"], [20.0])


def test_rgb_cell_data_follows_the_faces_that_remain():
    """A colour for each face given keeps those of the faces that remain."""
    xs, ys = np.ma.masked_array(LONS, mask=MASK), np.ma.masked_array(LATS, mask=MASK)
    connectivity = np.arange(8).reshape(2, 4)
    data = np.array([[10, 20, 30], [40, 50, 60]], dtype=np.uint8)

    with pytest.warns(UserWarning, match="uses a masked point"):
        mesh = Transform.from_unstructured(
            xs, ys, connectivity=connectivity, data=data, name="cells", rgb=True
        )

    np.testing.assert_array_equal(mesh.cell_data["cells"], [[10, 20, 30]])


@pytest.mark.parametrize("channels", [3, 4], ids=["rgb", "rgba"])
def test_rgb_cell_data_when_every_face_is_dropped(channels):
    """No colour is attached when no face is left to carry one.

    The mesh is still built. PyVista holds no empty array of colours, so the
    cell data that plain values would leave empty is left out.

    """
    mask = np.array(MASK)
    mask[0, 0] = True
    xs, ys = np.ma.masked_array(LONS, mask=mask), np.ma.masked_array(LATS, mask=mask)
    connectivity = np.arange(8).reshape(2, 4)
    data = np.ones((2, channels), dtype=np.uint8)

    with pytest.warns(UserWarning, match="use a masked point"):
        mesh = Transform.from_unstructured(
            xs, ys, connectivity=connectivity, data=data, name="cells", rgb=True
        )

    assert mesh.n_cells == 0
    assert "cells" not in mesh.cell_data


def test_cell_data_follows_faces_with_enough_points():
    """A face dropped for having too few points takes its value with it."""
    connectivity = np.ma.masked_array(
        [[0, 1, 2, 3], [1, 4, 5, 0]], mask=[[0, 0, 0, 0], [0, 0, 1, 1]]
    )
    xs = [0.0, 10.0, 10.0, 0.0, 20.0, 20.0]
    ys = [0.0, 0.0, 10.0, 10.0, 0.0, 10.0]

    with pytest.warns(UserWarning, match="fewer than three vertices"):
        mesh = Transform.from_unstructured(
            xs, ys, connectivity=connectivity, data=[10.0, 20.0], name="cells"
        )

    np.testing.assert_array_equal(mesh.cell_data["cells"], [10.0])


def test_data_that_fits_the_points_stays_on_the_points():
    """Data is point data when it fits both the points and the faces given.

    Five points make five triangles, and the two that use the masked last point
    are dropped.

    """
    mask = [False, False, False, False, True]
    xs = np.ma.masked_array([0.0, 10.0, 10.0, 0.0, 20.0], mask=mask)
    ys = np.ma.masked_array([0.0, 0.0, 10.0, 10.0, 5.0], mask=mask)
    connectivity = [[0, 1, 2], [0, 2, 3], [0, 1, 3], [1, 4, 2], [1, 2, 4]]
    data = [1.0, 2.0, 3.0, 4.0, 5.0]

    with pytest.warns(UserWarning, match="defines 2 faces that use a masked point"):
        mesh = Transform.from_unstructured(
            xs, ys, connectivity=connectivity, start_index=0, data=data, name="values"
        )

    assert mesh.n_cells == 3
    np.testing.assert_array_equal(mesh.point_data["values"], data)


@pytest.mark.parametrize("masked", ["xs", "ys", "differently"])
def test_points_masked_on_one_axis_stay(masked):
    """Points stay unless `xs` and `ys` carry the same mask.

    The masks are compared whole, so a point masked in both stays when the masks
    differ elsewhere, as point 7 does here with point 6 masked in `xs` alone.

    """
    xs, ys = np.array(LONS), np.array(LATS)
    if masked == "xs":
        xs = np.ma.masked_array(xs, mask=MASK)
    elif masked == "ys":
        ys = np.ma.masked_array(ys, mask=MASK)
    else:
        xs = np.ma.masked_array(xs, mask=[[0, 0, 0, 0], [0, 0, 1, 1]])
        ys = np.ma.masked_array(ys, mask=MASK)

    mesh = Transform.from_unstructured(xs, ys)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3, 4, 4, 5, 6, 7])


def test_masked_connectivity():
    """Masked connectivity builds faces of different sizes."""
    connectivity = np.ma.masked_array(
        [[0, 1, 2, 3], [1, 4, 5, 0]], mask=[[0, 0, 0, 0], [0, 0, 0, 1]]
    )
    xs = [0.0, 10.0, 10.0, 0.0, 20.0, 20.0]
    ys = [0.0, 0.0, 10.0, 10.0, 0.0, 10.0]

    mesh = Transform.from_unstructured(xs, ys, connectivity=connectivity)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3, 3, 1, 4, 5])


def test_masked_connectivity_drops_faces_of_two_points():
    """A face left with fewer than three points is dropped, with a warning."""
    connectivity = np.ma.masked_array(
        [[0, 1, 2, 3], [1, 4, 5, 0]], mask=[[0, 0, 0, 0], [0, 0, 1, 1]]
    )
    xs = [0.0, 10.0, 10.0, 0.0, 20.0, 20.0]
    ys = [0.0, 0.0, 10.0, 10.0, 0.0, 10.0]

    wmsg = "defines 1 face with fewer than three vertices, which is dropped"
    with pytest.warns(UserWarning, match=wmsg):
        mesh = Transform.from_unstructured(xs, ys, connectivity=connectivity)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3])


def test_masked_connectivity_drops_faces_of_any_too_few_points():
    """Faces left with one point, or none, are dropped and counted together."""
    connectivity = np.ma.masked_array(
        [[0, 1, 2, 3], [1, 4, 5, 0], [2, 5, 4, 1], [3, 2, 1, 0]],
        mask=[[0, 0, 0, 0], [0, 0, 1, 1], [0, 1, 1, 1], [1, 1, 1, 1]],
    )
    xs = [0.0, 10.0, 10.0, 0.0, 20.0, 20.0]
    ys = [0.0, 0.0, 10.0, 10.0, 0.0, 10.0]

    wmsg = "defines 3 faces with fewer than three vertices, which are dropped"
    with pytest.warns(UserWarning, match=wmsg):
        mesh = Transform.from_unstructured(xs, ys, connectivity=connectivity)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3])


def test_start_index_is_found():
    """One-based connectivity is found from its smallest index."""
    xs = [0.0, 10.0, 10.0, 0.0]
    ys = [0.0, 0.0, 10.0, 10.0]

    mesh = Transform.from_unstructured(xs, ys, connectivity=[[1, 2, 3, 4]])

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3])


def test_fully_masked_connectivity():
    """A connectivity with every index masked has no start index to find."""
    connectivity = np.ma.masked_array([[0, 1, 2]], mask=True)

    with pytest.raises(ValueError, match=r"closed interval \[0, 1\], got '--'"):
        _ = Transform.from_unstructured(
            [0.0, 10.0, 10.0], [0.0, 0.0, 10.0], connectivity=connectivity
        )


def test_masked_connectivity_must_be_2d():
    """Masked connectivity is held to two dimensions before any face is built."""
    connectivity = np.ma.masked_array([[[0, 1, 2, 3]]], mask=[[[0, 0, 0, 1]]])

    with pytest.raises(ValueError, match="got 3D connectivity array"):
        _ = Transform.from_unstructured(
            [0.0, 10.0, 10.0, 0.0], [0.0, 0.0, 10.0, 10.0], connectivity=connectivity
        )
