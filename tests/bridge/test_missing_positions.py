# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests of missing positions given to a point cloud.

A position is missing when its x or y value is masked or NaN
(positions spec §2 decision 1), and :meth:`geovista.bridge.Transform.from_points`
drops it, with its entry in every array given for each point
(positions spec §2 decision 6).

"""

from __future__ import annotations

import warnings

import cartopy.crs as ccrs
import numpy as np
import pint
import pytest

from geovista import bridge
from geovista.bridge import NAME_POINTS, NAME_VECTORS, Transform
from geovista.common import GV_POINT_HEIGHT

UREG = pint.UnitRegistry()

#: The positions of a point cloud, one of which is made missing.
LONS = [0.0, 10.0, 20.0, 30.0]
LATS = [0.0, 5.0, 10.0, 15.0]

#: The points kept when the second is missing.
KEPT = [0, 2, 3]

#: The warning of one point of four dropped, for the coordinates named.
DROPPED = (
    r"geovista dropped 1 of 4 points from the point cloud, where {named} masked "
    r"or NaN\."
)


def masked(values, index):
    """Return `values` as a masked array, masked at `index`."""
    result = np.ma.masked_array(values, dtype=float)
    result[index] = np.ma.masked
    return result


def nan(values, index):
    """Return `values` as an array, with NaN at `index`."""
    result = np.array(values, dtype=float)
    result[index] = np.nan
    return result


def kept(values):
    """Return the entries of `values` at :data:`KEPT`."""
    return np.asarray(values)[KEPT]


def assert_same_cloud(result, expected):
    """Assert two clouds have the same points and the same point arrays."""
    assert result.n_points == expected.n_points
    np.testing.assert_allclose(result.points, expected.points)
    assert sorted(result.point_data.keys()) == sorted(expected.point_data.keys())
    for name in expected.point_data:
        np.testing.assert_allclose(result[name], expected[name])


@pytest.mark.parametrize(
    ("xs", "ys", "named"),
    [
        (masked(LONS, 1), LATS, "'xs' is"),
        (LONS, masked(LATS, 1), "'ys' is"),
        (nan(LONS, 1), LATS, "'xs' is"),
        (LONS, nan(LATS, 1), "'ys' is"),
        ([0.0, None, 20.0, 30.0], LATS, "'xs' is"),
        (masked(LONS, 1), nan(LATS, 1), "'xs' and 'ys' are"),
        (
            UREG.Quantity(masked(LONS, 1), "degree"),
            UREG.Quantity(np.array(LATS), "degree"),
            "'xs' is",
        ),
    ],
    ids=["x-masked", "y-masked", "x-nan", "y-nan", "x-none", "both", "quantity"],
)
def test_drops_a_missing_point(xs, ys, named):
    """Test a missing point is dropped, with a warning naming its coordinates.

    Holds positions spec §2 decision 6.

    """
    with pytest.warns(UserWarning, match=DROPPED.format(named=named)):
        result = Transform.from_points(xs, ys)
    assert_same_cloud(result, Transform.from_points(kept(LONS), kept(LATS)))


def test_warns_once_counting():
    """Test the points dropped are counted in one warning.

    Holds positions spec §2 decision 6.

    """
    emsg = (
        r"dropped 2 of 4 points from the point cloud, where 'xs' and 'ys' are "
        r"masked or NaN\."
    )
    with pytest.warns(UserWarning, match=emsg) as record:
        result = Transform.from_points(masked(LONS, 0), nan(LATS, 3))
    assert len(record) == 1
    # the warning names the line that called from_points
    assert record[0].filename == __file__
    expected = Transform.from_points(LONS[1:3], LATS[1:3])
    assert_same_cloud(result, expected)


def test_cuts_data():
    """Test the data of a missing point is dropped with it.

    Holds positions spec §2 decision 6.

    """
    data = [1.0, 2.0, 3.0, 4.0]
    with pytest.warns(UserWarning, match=DROPPED.format(named="'xs' is")):
        result = Transform.from_points(masked(LONS, 1), LATS, data=data)
    expected = Transform.from_points(kept(LONS), kept(LATS), data=kept(data))
    assert_same_cloud(result, expected)
    np.testing.assert_allclose(result[NAME_POINTS], [1.0, 3.0, 4.0])


def test_cuts_vectors():
    """Test the vector at a missing point is dropped with it.

    Holds positions spec §2 decision 6.

    """
    vectors = ([1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0], [9.0, 8.0, 7.0, 6.0])
    with pytest.warns(UserWarning, match=DROPPED.format(named="'ys' is")):
        result = Transform.from_points(LONS, nan(LATS, 1), vectors=vectors)
    expected = Transform.from_points(
        kept(LONS), kept(LATS), vectors=tuple(kept(c) for c in vectors)
    )
    assert_same_cloud(result, expected)
    assert result[NAME_VECTORS].shape == (3, 3)


@pytest.mark.parametrize("kind", ["height", "depth"])
def test_cuts_heights(kind):
    """Test the height of a missing point is dropped with it.

    Holds positions spec §2 decision 6.

    """
    heights = [100.0, 200.0, 300.0, 400.0]
    with pytest.warns(UserWarning, match=DROPPED.format(named="'xs' is")):
        result = Transform.from_points(masked(LONS, 1), LATS, **{kind: heights})
    expected = Transform.from_points(kept(LONS), kept(LATS), **{kind: kept(heights)})
    assert_same_cloud(result, expected)


def test_cuts_a_zlevel_array():
    """Test the z-level of a missing point is dropped with it.

    Holds positions spec §2 decision 6.

    """
    zlevel = [1, 2, 3, 4]
    with pytest.warns(UserWarning, match=DROPPED.format(named="'xs' is")):
        result = Transform.from_points(masked(LONS, 1), LATS, zlevel=zlevel)
    expected = Transform.from_points(kept(LONS), kept(LATS), zlevel=kept(zlevel))
    assert_same_cloud(result, expected)


@pytest.mark.parametrize(
    "kwargs", [{"height": 100.0}, {"zlevel": 2}], ids=["height", "zlevel"]
)
def test_keeps_a_value_given_once(kwargs):
    """Test a value given once for every point applies to the points kept.

    Holds positions spec §2 decision 6.

    """
    with pytest.warns(UserWarning, match=DROPPED.format(named="'xs' is")):
        result = Transform.from_points(masked(LONS, 1), LATS, **kwargs)
    expected = Transform.from_points(kept(LONS), kept(LATS), **kwargs)
    assert_same_cloud(result, expected)


def test_cuts_arrays_in_the_shape_of_xs():
    """Test points in a grid drop their data in the same order.

    Holds positions spec §2 decision 6.

    """
    xs = np.ma.masked_array([[0.0, 10.0], [20.0, 30.0]], mask=[[0, 1], [0, 0]])
    ys = np.array([[0.0, 5.0], [10.0, 15.0]])
    data = np.array([[1.0, 2.0], [3.0, 4.0]])
    with pytest.warns(UserWarning, match=DROPPED.format(named="'xs' is")):
        result = Transform.from_points(xs, ys, data=data)
    expected = Transform.from_points(kept(LONS), kept(LATS), data=[1.0, 3.0, 4.0])
    assert_same_cloud(result, expected)


def test_cuts_a_zlevel_that_broadcasts():
    """Test a z-level that broadcasts against the points drops their levels.

    Holds positions spec §2 decision 6.

    """
    xs = np.array([[0.0, 10.0, 20.0], [30.0, 40.0, 50.0]])
    ys = np.array([[0.0, 5.0, 10.0], [15.0, 20.0, 25.0]])
    ys[1, 0] = np.nan
    emsg = (
        r"geovista dropped 1 of 6 points from the point cloud, where 'ys' is masked "
        r"or NaN\."
    )
    with pytest.warns(UserWarning, match=emsg):
        result = Transform.from_points(xs, ys, zlevel=[[1], [2]])
    expected = Transform.from_points(
        [0.0, 10.0, 20.0, 40.0, 50.0],
        [0.0, 5.0, 10.0, 20.0, 25.0],
        zlevel=[1, 1, 1, 2, 2],
    )
    assert_same_cloud(result, expected)


def test_cuts_vectors_in_another_crs():
    """Test vectors in another CRS are oriented at the points kept.

    Holds positions spec §2 decision 6.

    """
    vectors = ([10.0, 20.0, 30.0, 40.0], [20.0, -17.0, 0.0, 33.0])
    vectors_crs = ccrs.RotatedGeodetic(130.0, 65.0).to_wkt()
    with pytest.warns(UserWarning, match=DROPPED.format(named="'xs' is")):
        result = Transform.from_points(
            masked(LONS, 1), LATS, vectors=vectors, vectors_crs=vectors_crs
        )
    expected = Transform.from_points(
        kept(LONS),
        kept(LATS),
        vectors=tuple(kept(c) for c in vectors),
        vectors_crs=vectors_crs,
    )
    assert_same_cloud(result, expected)


def test_drops_before_transforming(mocker):
    """Test a missing point is dropped before the others are transformed.

    Its value under the mask lies outside the domain of the CRS, and is never read,
    so only the points kept reach the transform. Holds positions spec §2 decision 6.

    """
    xs = masked([0.0, 1e40, 2e5, 3e5], 1)
    ys = [0.0, 1e5, 2e5, 3e5]
    spy = mocker.spy(bridge, "transform_points")
    with pytest.warns(UserWarning, match=DROPPED.format(named="'xs' is")):
        result = Transform.from_points(xs, ys, crs="+proj=eqc")
    assert spy.call_count == 1
    np.testing.assert_array_equal(spy.call_args.kwargs["xs"], kept(xs.data))
    expected = Transform.from_points(kept(xs.data), kept(ys), crs="+proj=eqc")
    assert_same_cloud(result, expected)
    assert np.all(np.isfinite(result.points))


@pytest.mark.parametrize("clean", [False, True])
def test_a_cloud_of_only_missing_points(clean):
    """Test a cloud whose every point is missing is built with no points.

    Cleaning it keeps its arrays. Holds positions spec §2 decision 6.

    """
    xs = np.ma.masked_array([0.0, 10.0, 20.0], mask=True)
    emsg = (
        r"geovista dropped every point of the point cloud \(3\), where 'xs' is "
        r"masked or NaN, so it has no points\."
    )
    with pytest.warns(UserWarning, match=emsg):
        result = Transform.from_points(
            xs,
            [0.0, 5.0, 10.0],
            data=[1.0, 2.0, 3.0],
            height=[1.0, 2.0, 3.0],
            clean=clean,
        )
    assert result.n_points == 0
    assert set(result.point_data) == {NAME_POINTS, GV_POINT_HEIGHT}
    for name in result.point_data:
        assert result[name].size == 0


@pytest.mark.parametrize("clean", [False, True])
def test_a_cloud_of_only_missing_points_keeps_its_vectors(clean):
    """Test a cloud whose every point is missing keeps its vectors, with no values.

    Cleaning it keeps them too. Holds positions spec §2 decision 6.

    """
    emsg = r"geovista dropped every point of the point cloud \(2\)"
    with pytest.warns(UserWarning, match=emsg):
        result = Transform.from_points(
            [np.nan, np.nan],
            [0.0, 10.0],
            vectors=([1.0, 2.0], [3.0, 4.0]),
            clean=clean,
        )
    assert result.n_points == 0
    assert result.active_vectors_name == NAME_VECTORS
    assert result[NAME_VECTORS].shape == (0, 3)


def test_refuses_data_of_another_count():
    """Test data that is not one value for each point given is refused, as before.

    Data short by the points dropped is not paired with the points kept.

    """
    emsg = r"Require mesh data with either '4' points or '4' cells, got '3' values\."
    with pytest.raises(ValueError, match=emsg):
        Transform.from_points(nan(LONS, 1), LATS, data=[1.0, 2.0, 3.0])


def test_refuses_a_zlevel_of_another_shape():
    """Test a z-level that does not broadcast to the points given is refused, as before.

    A z-level short by the points dropped is not paired with the points kept.

    """
    emsg = (
        r"Cannot broadcast zlevel with shape \(3,\) to longitude/latitude shape "
        r"\(4,\)\."
    )
    with pytest.raises(ValueError, match=emsg):
        Transform.from_points(nan(LONS, 1), LATS, zlevel=[1, 2, 3])


def test_refuses_coordinates_of_another_size():
    """Test coordinates of different sizes are refused as before, with no drop.

    The points are paired only when the two have one size, so the transform
    refuses them, and no point is dropped or warned of.

    """
    emsg = r"'xs' and 'ys' require same length, got 4 and 3 respectively\."
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(ValueError, match=emsg):
            Transform.from_points(nan(LONS, 1), LATS[:3])


def test_refuses_infinite():
    """Test an infinite coordinate is refused, naming it.

    Holds positions spec §2 decision 2.

    """
    emsg = r"'xs' cannot be infinite, got inf at index 1\."
    with pytest.raises(ValueError, match=emsg):
        Transform.from_points([0.0, np.inf, 20.0, 30.0], LATS)


@pytest.mark.parametrize("xs", [LONS, np.ma.masked_array(LONS)], ids=["list", "nomask"])
def test_keeps_present_points(xs):
    """Test a cloud whose points are all present keeps them, without a warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = Transform.from_points(xs, LATS)
    assert result.n_points == 4
    np.testing.assert_allclose(result.points, Transform.from_points(LONS, LATS).points)


@pytest.mark.parametrize("missing", [False, True], ids=["none-missing", "one-missing"])
def test_refuses_a_zlevel_with_vectors_in_the_shape_given(missing):
    """Test a zlevel array given with vectors is refused in the shape given.

    It is refused before any point is dropped, so with no warning, which settles
    positions spec §8 item 4.

    """
    xs = np.array([[0.0, 10.0, 20.0], [30.0, 40.0, 50.0]])
    ys = np.array([[0.0, 5.0, 10.0], [15.0, 20.0, 25.0]])
    if missing:
        ys[1, 0] = np.nan
    vectors = (np.ones((2, 3)), np.ones((2, 3)))
    emsg = r"'zlevel' may not be multiple, has shape \(2, 1\)\."
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(ValueError, match=emsg):
            Transform.from_points(xs, ys, zlevel=[[1], [2]], vectors=vectors)
