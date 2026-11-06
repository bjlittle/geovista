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

from geovista.common import _missing_positions, _refuse_missing_poi
from geovista.units import _lonlats

UREG = pint.UnitRegistry()

#: The mask of three positions whose second is missing.
SECOND = [False, True, False]


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
