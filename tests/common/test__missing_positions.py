# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the test of a missing position in :mod:`geovista.common`.

Holds positions spec §2 decision 1, that a position is missing when either of its
coordinates is masked or NaN, and positions spec §2 decision 2, that an infinite
coordinate is refused, naming its argument.

"""

from __future__ import annotations

import warnings

import numpy as np
import pint
import pytest

from geovista import common
from geovista.common import (
    _missing_and_named,
    _missing_as_nan,
    _missing_pair,
    _missing_positions,
    _refuse_missing_poi,
    _refuse_missing_positions,
)
from geovista.units import _lonlats

UREG = pint.UnitRegistry()

#: The mask of three positions whose second is missing.
SECOND = [False, True, False]

#: Four positions of a shape, some of which are made missing.
LONS = [0.0, 10.0, 20.0, 30.0]
LATS = [0.0, 5.0, 10.0, 15.0]


def missing(xs, ys):
    """Return the missing positions of `xs` and `ys`."""
    return _missing_positions(xs, ys, x_name="xs", y_name="ys")


def test_present():
    """Test that positions given as integers are all present."""
    result = missing([1, 2, 3], [4, 5, 6])
    assert result.dtype == bool
    np.testing.assert_array_equal(result, [False, False, False])


@pytest.mark.parametrize(
    ("xs", "ys"),
    [
        (np.ma.masked_array([1.0, 2.0, 3.0], mask=SECOND), [4.0, 5.0, 6.0]),
        ([1.0, 2.0, 3.0], np.ma.masked_array([4.0, 5.0, 6.0], mask=SECOND)),
        (
            np.ma.masked_array([1.0, 2.0, 3.0], mask=SECOND),
            np.ma.masked_array([4.0, 5.0, 6.0], mask=SECOND),
        ),
        ([1.0, np.nan, 3.0], [4.0, 5.0, 6.0]),
        ([1.0, 2.0, 3.0], [4.0, np.nan, 6.0]),
    ],
    ids=["x-masked", "y-masked", "both-masked", "x-nan", "y-nan"],
)
def test_missing(xs, ys):
    """Test that a masked or NaN coordinate, alone or with the other, is missing."""
    np.testing.assert_array_equal(missing(xs, ys), SECOND)


def test_none_is_missing():
    """Test that a None coordinate is missing, as NumPy reads it as NaN."""
    np.testing.assert_array_equal(missing([1.0, None, 3.0], [4.0, 5.0, 6.0]), SECOND)


def test_nomask():
    """Test that a masked array whose mask is nomask has no missing position."""
    xs = np.ma.masked_array([1.0, 2.0, 3.0])
    assert np.ma.getmask(xs) is np.ma.nomask
    np.testing.assert_array_equal(missing(xs, [4.0, 5.0, 6.0]), [False] * 3)


def test_a_masked_element_of_a_list():
    """Test that a list holding the masked constant keeps it missing.

    NumPy warns that it converts the masked element whenever it reads such a list,
    and keeps its mask. The warning is NumPy's, so it is ignored here.

    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", "Warning: converting a masked", UserWarning)
        result = missing([1.0, np.ma.masked, 3.0], [4, 5, 6])
    np.testing.assert_array_equal(result, SECOND)


@pytest.mark.parametrize("value", [np.ma.masked, np.nan], ids=["masked", "nan"])
def test_scalar(value):
    """Test that a missing scalar coordinate gives a 0-d missing position."""
    result = missing(value, 1.0)
    assert result.shape == ()
    assert bool(result)


@pytest.mark.parametrize("value", [np.inf, -np.inf], ids=["inf", "-inf"])
@pytest.mark.parametrize("name", ["xs", "ys"])
def test_infinite_refused(name, value):
    """Test that an infinite coordinate is refused, naming its argument."""
    coordinates = {"xs": [1.0, 2.0, 3.0], "ys": [4.0, 5.0, 6.0]}
    coordinates[name][1] = value
    emsg = rf"'{name}' cannot be infinite, got {value} at index 1\."
    with pytest.raises(ValueError, match=emsg):
        missing(coordinates["xs"], coordinates["ys"])


def test_infinite_scalar_refused():
    """Test that an infinite scalar coordinate is refused, naming its argument."""
    with pytest.raises(ValueError, match=r"'xs' cannot be infinite, got inf\."):
        missing(np.inf, 1.0)


def test_masked_infinite_is_missing():
    """Test that an infinite value under a mask is missing, and not read."""
    xs = np.ma.masked_array([1.0, np.inf, 3.0], mask=SECOND)
    np.testing.assert_array_equal(missing(xs, [4.0, 5.0, 6.0]), SECOND)


def test_a_masked_quantity():
    """Test that a quantity of a masked array keeps its mask once read."""
    lons = UREG.Quantity(np.ma.masked_array([1.0, 2.0, 3.0], mask=SECOND), "degree")
    lats = UREG.Quantity([4.0, 5.0, 6.0], "degree")
    result = _missing_positions(*_lonlats(lons, lats), x_name="lons", y_name="lats")
    np.testing.assert_array_equal(result, SECOND)


def test_shapes_that_do_not_pair():
    """Test that coordinates that do not broadcast are refused, naming both."""
    emsg = r"Cannot pair 'xs' of shape \(3,\) with 'ys' of shape \(2,\)\."
    with pytest.raises(ValueError, match=emsg):
        missing([1.0, 2.0, 3.0], [4.0, 5.0])


@pytest.mark.parametrize(
    ("xs", "ys", "expected", "names"),
    [
        (
            np.ma.masked_array([1.0, 2.0, 3.0], mask=SECOND),
            [4.0, 5.0, 6.0],
            SECOND,
            ["xs"],
        ),
        ([1.0, 2.0, 3.0], [4.0, np.nan, 6.0], SECOND, ["ys"]),
        (
            np.ma.masked_array([1.0, 2.0, 3.0], mask=SECOND),
            [4.0, np.nan, 6.0],
            SECOND,
            ["xs", "ys"],
        ),
        ([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [False] * 3, []),
    ],
    ids=["x", "y", "both", "present"],
)
def test_missing_and_named(xs, ys, expected, names):
    """Test that the missing positions come with the coordinates that make them so."""
    result, named = _missing_and_named(xs, ys, x_name="xs", y_name="ys")
    np.testing.assert_array_equal(result, expected)
    assert named == names


@pytest.mark.parametrize(
    ("x", "y", "named"),
    [
        (np.ma.masked, 52.0, "'x' is"),
        (np.nan, 52.0, "'x' is"),
        (30.0, np.ma.masked, "'y' is"),
        (30.0, np.nan, "'y' is"),
        (np.nan, np.ma.masked, "'x' and 'y' are"),
    ],
    ids=["x-masked", "x-nan", "y-masked", "y-nan", "both"],
)
def test_refuse_missing_poi(x, y, named):
    """Test that a missing point-of-interest is refused, naming its coordinates."""
    emsg = rf"The point-of-interest is missing, as {named} masked or NaN\."
    with pytest.raises(ValueError, match=emsg):
        _refuse_missing_poi(x, y, x_name="x", y_name="y")


def test_refuse_missing_poi_passes_a_present_one():
    """Test that a present point-of-interest is not refused."""
    assert _refuse_missing_poi(30.0, 52.0, x_name="x", y_name="y") is None


def refuse(lons, lats):
    """Refuse the positions of a geodesic line given by `lons` and `lats`."""
    return _refuse_missing_positions(
        lons, lats, x_name="lons", y_name="lats", shape="geodesic line"
    )


@pytest.mark.parametrize(
    ("lons", "lats", "emsg"),
    [
        (
            np.ma.masked_array(LONS, mask=[0, 1, 0, 0]),
            LATS,
            (
                r"A geodesic line needs every position given, but 1 of 4 is missing, "
                r"as 'lons' is masked or NaN\."
            ),
        ),
        (
            LONS,
            [0.0, 5.0, np.nan, np.nan],
            r"but 2 of 4 are missing, as 'lats' is masked or NaN\.",
        ),
        (
            np.ma.masked_array(LONS, mask=[0, 1, 0, 0]),
            [0.0, np.nan, 10.0, 15.0],
            r"but 1 of 4 is missing, as 'lons' and 'lats' are masked or NaN\.",
        ),
        (
            np.ma.masked_array(LONS, mask=[1, 0, 0, 0]),
            [0.0, 5.0, 10.0, np.nan],
            r"but 2 of 4 are missing, as 'lons' and 'lats' are",
        ),
    ],
    ids=["lons-one", "lats-two", "both-one", "both-two"],
)
def test_refuse_missing_positions(lons, lats, emsg):
    """Test that a shape with a missing position is refused, counting and naming.

    Holds positions spec §2 decision 5.

    """
    with pytest.raises(ValueError, match=emsg):
        refuse(lons, lats)


@pytest.mark.parametrize(
    "lons", [LONS, np.ma.masked_array(LONS)], ids=["list", "nomask"]
)
def test_refuse_missing_positions_passes_present_ones(lons):
    """Test that a shape whose positions are all present is not refused."""
    assert refuse(lons, LATS) is None


def test_refuse_missing_positions_refuses_infinite():
    """Test that a shape with an infinite coordinate is refused, naming it.

    Holds positions spec §2 decision 2.

    """
    emsg = r"'lats' cannot be infinite, got inf at index 2\."
    with pytest.raises(ValueError, match=emsg):
        refuse(LONS, [0.0, 5.0, np.inf, 15.0])


def test_refuse_missing_positions_names_shapes_that_do_not_pair():
    """Test that coordinates of one size but different shapes are refused, named."""
    emsg = r"Cannot pair 'lons' of shape \(2, 2\) with 'lats' of shape \(4,\)\."
    with pytest.raises(ValueError, match=emsg):
        refuse(np.zeros((2, 2)), np.zeros(4))


@pytest.mark.parametrize("name", ["xs", "ys"])
def test_infinite_in_a_grid(name):
    """Test that an infinite coordinate in a grid is placed by each dimension."""
    coordinates = {"xs": np.zeros((2, 2)), "ys": np.zeros((2, 2))}
    coordinates[name] = np.array([[0.0, 1.0], [2.0, np.inf]])
    emsg = rf"'{name}' cannot be infinite, got inf at index \(1, 1\)\."
    with pytest.raises(ValueError, match=emsg):
        missing(coordinates["xs"], coordinates["ys"])


def test_missing_as_nan_pairs_the_coordinates():
    """Test that a missing position is NaN in both coordinates."""
    xs = [0.0, np.nan, 20.0]
    ys = np.ma.masked_array([0.0, 10.0, 20.0], mask=[False, False, True])
    x, y = _missing_as_nan(xs, ys, x_name="lons", y_name="lats")
    np.testing.assert_array_equal(x, [0.0, np.nan, np.nan])
    np.testing.assert_array_equal(y, [0.0, np.nan, np.nan])


def test_missing_as_nan_leaves_the_arrays_given_alone():
    """Test that the coordinates given are copied, never written to."""
    xs = np.array([0.0, np.nan, 20.0])
    ys = np.array([0.0, 10.0, 20.0])
    x, y = _missing_as_nan(xs, ys, x_name="lons", y_name="lats")
    assert not np.any(np.isnan(ys))
    assert x is not xs
    assert y is not ys


def test_missing_as_nan_leaves_shapes_that_differ_unpaired():
    """Test that coordinates of different shapes are each read alone."""
    xs = [0.0, np.nan, 20.0]
    ys = [0.0, 10.0]
    x, y = _missing_as_nan(xs, ys, x_name="lons", y_name="lats")
    np.testing.assert_array_equal(x, [0.0, np.nan, 20.0])
    np.testing.assert_array_equal(y, ys)


def test_missing_as_nan_refuses_infinite():
    """Test that an infinite coordinate is refused, naming it."""
    emsg = r"'lons' cannot be infinite, got inf at index 1\."
    with pytest.raises(ValueError, match=emsg):
        _missing_as_nan([0.0, np.inf], [0.0, 1.0], x_name="lons", y_name="lats")


#: The names one position is read with, as npoints reads its start.
PAIR_NAMES = {"x_name": "start_lon", "y_name": "start_lat"}


@pytest.mark.parametrize(
    ("x", "y"),
    [
        (10.0, 20.0),
        (10, 20),
        (np.float64(10.0), np.float32(20.0)),
        (np.nan, 20.0),
        (10.0, np.nan),
        (None, 20.0),
        (10.0, np.ma.masked),
    ],
    ids=["floats", "ints", "numpy", "x-nan", "y-nan", "x-none", "y-masked"],
)
def test_missing_pair_agrees_with_missing_as_nan(x, y):
    """Test one position reads as the general helper reads it, as floats."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = _missing_pair(x, y, **PAIR_NAMES)
        expected = tuple(float(v) for v in _missing_as_nan(x, y, **PAIR_NAMES))
    assert all(type(value) is float for value in result)
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize("value", [np.inf, -np.inf], ids=["inf", "-inf"])
@pytest.mark.parametrize("name", ["start_lon", "start_lat"])
def test_missing_pair_refuses_infinite(name, value):
    """Test an infinite coordinate of one position is refused, naming it."""
    coordinates = {"start_lon": 10.0, "start_lat": 20.0, name: value}
    emsg = rf"'{name}' cannot be infinite, got {value}\."
    with pytest.raises(ValueError, match=emsg):
        _missing_pair(coordinates["start_lon"], coordinates["start_lat"], **PAIR_NAMES)


def test_missing_pair_reads_numpy_scalars_without_masked_arrays(mocker):
    """Test two plain numbers are read without the general helper."""
    spy = mocker.spy(common, "_missing_as_nan")
    result = _missing_pair(np.float64(10.0), np.float64(20.0), **PAIR_NAMES)
    assert result == (10.0, 20.0)
    spy.assert_not_called()


def test_missing_pair_reads_a_masked_value_as_before(mocker):
    """Test a masked value goes to the general helper, and gives NaN unwarned."""
    spy = mocker.spy(common, "_missing_as_nan")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = _missing_pair(np.ma.masked, 20.0, **PAIR_NAMES)
    assert np.all(np.isnan(result))
    spy.assert_called_once()
