# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests of missing positions given to a mesh.

A position is missing when its x or y value is masked or NaN
(positions spec §2 decision 1), and a mesh treats every missing point as the
bridge treats a point that `xs` and `ys` mask alike (positions spec §2 decision 7).

"""

from __future__ import annotations

import warnings

import numpy as np
import pint
import pytest

from geovista import bridge
from geovista.bridge import NAME_CELLS, NAME_POINTS, Transform
from geovista.crs import WGS84
from geovista.transform import transform_points

#: A registry of its own, as a caller's would be.
UREG = pint.UnitRegistry()

#: A grid of 3 by 3 points, the corners of 4 quads.
LONS = np.tile([0.0, 10.0, 20.0], (3, 1))
LATS = np.repeat([0.0, 10.0, 20.0], 3).reshape(3, 3)

#: A point that only the fourth quad uses.
CORNER = (2, 2)

#: The 4 quads of the grid, as a connectivity array on its points raveled.
QUADS = [[0, 1, 4, 3], [1, 2, 5, 4], [3, 4, 7, 6], [4, 5, 8, 7]]

#: An orthographic projection, which cannot reach the far side of the globe.
ORTHO = "+proj=ortho +lat_0=0 +lon_0=0"

#: A coordinate in metres that lies far outside the disk of ``ORTHO``.
OFF_DISK = 1e9

#: The warning of one face dropped.
ONE = "defines 1 face that uses a missing point, which is dropped"


def masked(values, *indices: tuple[int, ...] | int):
    """Return `values` as a masked array, masked at each of `indices`."""
    result = np.ma.masked_array(values, dtype=float)
    for index in indices:
        result[index] = np.ma.masked
    return result


def nan(values, *indices: tuple[int, ...] | int):
    """Return `values` as an array, with NaN at each of `indices`."""
    result = np.array(values, dtype=float)
    for index in indices:
        result[index] = np.nan
    return result


def alike(*indices: tuple[int, ...] | int):
    """Return the longitudes and latitudes, masked alike at each of `indices`."""
    return masked(LONS, *indices), masked(LATS, *indices)


def reference(build, *args: object, **kwargs: object):
    """Build the mesh of a point masked alike, which warns of its faces dropped."""
    with pytest.warns(UserWarning, match="uses? a missing point"):
        return build(*args, **kwargs)


def assert_same_mesh(result, expected):
    """Assert that two meshes have the same faces and the same points."""
    np.testing.assert_array_equal(result.faces, expected.faces)
    np.testing.assert_allclose(result.points, expected.points)


@pytest.mark.parametrize(
    ("xs", "ys", "missing"),
    [
        (masked(LONS, CORNER), LATS, [CORNER]),
        (LONS, masked(LATS, CORNER), [CORNER]),
        (nan(LONS, CORNER), LATS, [CORNER]),
        (LONS, nan(LATS, CORNER), [CORNER]),
        (
            UREG.Quantity(masked(LONS, CORNER), "degree"),
            UREG.Quantity(LATS, "degree"),
            [CORNER],
        ),
        (masked(LONS, CORNER), masked(LATS, (0, 0)), [CORNER, (0, 0)]),
    ],
    ids=["lon-masked", "lat-masked", "lon-nan", "lat-nan", "quantity", "masks-differ"],
)
def test_drops_the_faces_of_a_missing_point(xs, ys, missing):
    """Test a face that uses a missing point is dropped, as for one masked alike.

    Holds positions spec §2 decision 7.

    """
    wmsg = (
        ONE
        if len(missing) == 1
        else "defines 2 faces that use a missing point, which are dropped"
    )
    with pytest.warns(UserWarning, match=wmsg):
        result = Transform.from_2d(xs, ys)
    expected = reference(Transform.from_2d, *alike(*missing))
    assert_same_mesh(result, expected)


@pytest.mark.parametrize(
    "build",
    [
        lambda xs, ys: Transform.from_unstructured(
            np.ravel(xs), np.ravel(ys), connectivity=QUADS
        ),
        lambda xs, ys: Transform(xs, ys)(),
    ],
    ids=["from_unstructured", "constructor"],
)
def test_drops_through_every_entry_point(build):
    """Test each way of building a mesh drops the faces of a missing point.

    Holds positions spec §2 decision 7.

    """
    with pytest.warns(UserWarning, match=ONE):
        result = build(nan(LONS, CORNER), LATS)
    expected = reference(build, *alike(CORNER))
    assert_same_mesh(result, expected)


def test_keeps_the_other_vertices_of_a_shape_face():
    """Test a face of a shape keeps its other vertices, as for a point masked alike.

    Holds positions spec §2 decision 7.

    """
    xs = [0.0, 10.0, 20.0, 0.0, 10.0, 20.0, 10.0, 15.0]
    ys = [0.0, 0.0, 0.0, 10.0, 10.0, 10.0, 20.0, 20.0]
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = Transform.from_unstructured(nan(xs, 2), ys, connectivity=(2, 4))
        expected = Transform.from_unstructured(
            masked(xs, 2), masked(ys, 2), connectivity=(2, 4)
        )
    assert [result.get_cell(i).n_points for i in range(result.n_cells)] == [3, 4]
    assert_same_mesh(result, expected)


def test_builds_no_faces_when_every_point_is_missing():
    """Test a mesh whose every point is missing builds with no faces."""
    wmsg = "defines 4 faces that use a missing point, which are dropped"
    with pytest.warns(UserWarning, match=wmsg):
        result = Transform.from_2d(np.full_like(LONS, np.nan), LATS)
    assert result.n_cells == 0
    assert result.n_points == 9


def test_keeps_heights_for_each_point():
    """Test heights given for each point still fit, as the missing point stays."""
    with pytest.warns(UserWarning, match=ONE):
        result = Transform.from_2d(nan(LONS, CORNER), LATS, height=np.arange(9.0))
    assert result.n_cells == 3


def test_cuts_colours_for_each_face():
    """Test colours given for each face keep those of the faces that remain."""
    colours = np.array(
        [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0]], dtype=np.uint8
    )
    with pytest.warns(UserWarning, match=ONE):
        result = Transform.from_2d(nan(LONS, CORNER), LATS, data=colours, rgb=True)
    np.testing.assert_array_equal(result.cell_data[NAME_CELLS], colours[:3])


@pytest.mark.parametrize("missing", ["masked", "nan"])
def test_leaves_a_missing_point_out_of_the_transform(mocker, missing):
    """Test a missing point never reaches the transform, whatever its other value.

    Its y lies off the disk of the projection, which the transform would refuse.

    """
    points = transform_points(src_crs=WGS84, tgt_crs=ORTHO, xs=LONS, ys=LATS)
    xs, ys = points[:, 0].reshape(3, 3), points[:, 1].reshape(3, 3)
    ys[CORNER] = OFF_DISK
    xs = masked(xs, CORNER) if missing == "masked" else nan(xs, CORNER)
    spy = mocker.spy(bridge, "transform_points")

    with pytest.warns(UserWarning, match=ONE):
        result = Transform.from_2d(xs, ys, crs=ORTHO)

    assert result.n_cells == 3
    assert spy.call_args.kwargs["xs"].size == 8


@pytest.mark.parametrize("name", ["xs", "ys"])
def test_refuses_infinite(name):
    """Test an infinite coordinate is refused, named at its index as given."""
    xs, ys = LONS.copy(), LATS.copy()
    (xs if name == "xs" else ys)[CORNER] = np.inf
    emsg = rf"'{name}' cannot be infinite, got inf at index \(2, 2\)\."
    with pytest.raises(ValueError, match=emsg):
        Transform.from_2d(xs, ys)


@pytest.mark.parametrize(
    "xs", [LONS.tolist(), np.ma.masked_array(LONS)], ids=["list", "nomask"]
)
def test_keeps_present_points(xs):
    """Test points that are all present build every face, unwarned."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = Transform.from_2d(xs, LATS)
    assert result.n_cells == 4


@pytest.mark.parametrize(
    ("xs", "ys"), [(nan(LONS, CORNER), LATS), alike(CORNER)], ids=["nan", "alike"]
)
def test_constructor_cuts_data_for_each_face(xs, ys):
    """Test the constructor keeps the data of the faces that remain.

    Holds positions spec §2 decision 7.

    """
    with pytest.warns(UserWarning, match=ONE):
        transform = Transform(xs, ys)
    result = transform(data=[1.0, 2.0, 3.0, 4.0])
    np.testing.assert_array_equal(result.cell_data[NAME_CELLS], [1.0, 2.0, 3.0])


def test_constructor_keeps_data_for_each_point():
    """Test data given for each point still fits, as the missing point stays."""
    with pytest.warns(UserWarning, match=ONE):
        transform = Transform(nan(LONS, CORNER), LATS)
    result = transform(data=np.arange(9.0))
    np.testing.assert_array_equal(result.point_data[NAME_POINTS], np.arange(9.0))


def test_constructor_refuses_data_of_another_count():
    """Test data neither for each point nor for each face is refused, as before."""
    with pytest.warns(UserWarning, match=ONE):
        transform = Transform(nan(LONS, CORNER), LATS)
    emsg = r"Require mesh data with either '9' points or '3' cells, got '5' values\."
    with pytest.raises(ValueError, match=emsg):
        transform(data=np.arange(5.0))
