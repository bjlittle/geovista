# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests of missing positions given to the transforms of points.

A position is missing when its x or y value is masked or NaN
(positions spec §2 decision 1), and a transform carries it through as a row of
NaN, z included, without transforming it (positions spec §2 decision 8).

"""

from __future__ import annotations

import warnings

import numpy as np
import pint
import pytest

from geovista import transform
from geovista.crs import WGS84
from geovista.transform import transform_point, transform_points

#: A registry of its own, as a caller's would be.
UREG = pint.UnitRegistry()

#: An orthographic projection, which cannot reach the far side of the globe.
ORTHO = "+proj=ortho +lat_0=0 +lon_0=0"

#: The x and y values of three positions.
XS = np.array([0.0, 10.0, 20.0])
YS = np.array([0.0, 10.0, 20.0])

#: A longitude beyond the disk of ``ORTHO``, which its transform refuses.
HIDDEN = 170.0

#: The positions present when the second is missing.
PRESENT = [0, 2]

#: Each target CRS, the source's own and a bounded projection.
TARGETS = pytest.mark.parametrize("tgt", [WGS84, ORTHO], ids=["same", "ortho"])


def masked(values, *indices: int):
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


@TARGETS
@pytest.mark.parametrize(
    ("xs", "ys"),
    [
        (masked(XS, 1), YS),
        (XS, masked(YS, 1)),
        (masked(XS, 1), masked(YS, 1)),
        (nan(XS, 1), YS),
        (XS, nan(YS, 1)),
        ([0.0, None, 20.0], YS),
        (UREG.Quantity(masked(XS, 1), "degree"), UREG.Quantity(YS, "degree")),
    ],
    ids=[
        "lon-masked",
        "lat-masked",
        "both-masked",
        "lon-nan",
        "lat-nan",
        "lon-none",
        "quantity",
    ],
)
def test_gives_nan_for_a_missing_position(tgt, xs, ys):
    """Test a missing position gives a row of NaN, the others as alone.

    Holds positions spec §2 decision 1 and positions spec §2 decision 8.

    """
    result = transform_points(WGS84, tgt, xs, ys)
    assert np.all(np.isnan(result[1]))
    expected = transform_points(WGS84, tgt, XS[PRESENT], YS[PRESENT])
    np.testing.assert_allclose(result[PRESENT], expected)


@TARGETS
def test_reads_nomask_as_present(tgt):
    """Test a masked array whose mask is nomask has no missing position."""
    result = transform_points(WGS84, tgt, np.ma.masked_array(XS), YS)
    assert not np.any(np.isnan(result))


def test_leaves_a_missing_position_out_of_the_transform():
    """Test a value under a mask beyond the domain of the CRS raises nothing."""
    xs = np.ma.masked_array([0.0, HIDDEN, 20.0], mask=[False, True, False])
    result = transform_points(WGS84, ORTHO, xs, YS)
    assert np.all(np.isnan(result[1]))
    point = transform_point(WGS84, ORTHO, np.ma.masked_array(HIDDEN, mask=True), 0.0)
    assert np.all(np.isnan(point))


def test_transforms_nothing_when_every_position_is_missing(mocker):
    """Test positions that are all missing give NaN alone, and build no transform."""
    spy = mocker.spy(transform, "_transformer")
    result = transform_points(WGS84, ORTHO, np.full(3, np.nan), YS)
    assert result.shape == (3, 3)
    assert np.all(np.isnan(result))
    spy.assert_not_called()


def test_gives_nan_for_one_missing_position_given_as_numbers():
    """Test one missing position given as numbers gives one row of NaN."""
    result = transform_points(WGS84, ORTHO, np.nan, 10.0)
    assert result.shape == (1, 3)
    assert np.all(np.isnan(result))


@TARGETS
def test_gives_a_grid_nan_where_a_position_is_missing(tgt):
    """Test a grid keeps its shape, with NaN in every component at a missing one."""
    xs = np.array([[0.0, 10.0, 20.0], [30.0, 40.0, 50.0]])
    ys = np.zeros((2, 3))
    zs = np.full((2, 3), 5.0)
    result = transform_points(WGS84, tgt, nan(xs, (1, 2)), ys, zs)
    assert result.shape == (2, 3, 3)
    assert np.all(np.isnan(result[1, 2]))
    expected = transform_points(WGS84, tgt, xs[0, 0], ys[0, 0], zs[0, 0])
    np.testing.assert_allclose(result[0, 0], expected[0])


@pytest.mark.parametrize("name", ["xs", "ys"])
def test_refuses_infinite(name):
    """Test an infinite coordinate is refused, named at its index as given.

    Holds positions spec §2 decision 2.

    """
    coordinates = {"xs": np.zeros((2, 3)), "ys": np.zeros((2, 3))}
    coordinates[name][1, 2] = np.inf
    emsg = rf"'{name}' cannot be infinite, got inf at index \(1, 2\)\."
    with pytest.raises(ValueError, match=emsg):
        transform_points(WGS84, ORTHO, coordinates["xs"], coordinates["ys"])


@pytest.mark.parametrize(
    "x", [np.ma.masked, np.nan, None], ids=["masked", "nan", "none"]
)
def test_transform_point_gives_nan(x):
    """Test a missing point gives NaN in every component, with no warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = transform_point(WGS84, ORTHO, x, 10.0)
    assert np.all(np.isnan(result))


@pytest.mark.parametrize("name", ["x", "y"])
def test_transform_point_refuses_infinite(name):
    """Test an infinite coordinate of a point is refused, naming it.

    Holds positions spec §2 decision 2.

    """
    coordinates = {"x": 10.0, "y": 10.0}
    coordinates[name] = np.inf
    emsg = rf"'{name}' cannot be infinite, got inf\."
    with pytest.raises(ValueError, match=emsg):
        transform_point(WGS84, ORTHO, coordinates["x"], coordinates["y"])
