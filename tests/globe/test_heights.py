# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for reading heights, and refusing them, in :mod:`geovista.globe`."""

from __future__ import annotations

import numpy as np
import pint
import pytest

from geovista.globe import _for_points, _heights, _refuse_zlevel


def test_metres_by_default():
    """A plain height is in metres."""
    assert _heights(100, None, None) == 100.0
    np.testing.assert_array_equal(_heights([1, 2], None, None), [1.0, 2.0])


@pytest.mark.parametrize(
    ("value", "units", "metres"),
    [(1000, "ft", 304.8), (2, "km", 2000.0), (5, "m", 5.0)],
)
def test_vertical_units(value, units, metres):
    """A plain height is in the unit that vertical_units names."""
    assert _heights(value, None, units) == pytest.approx(metres)


def test_a_quantity_from_any_registry():
    """A quantity from a registry of the caller's own carries its unit."""
    feet = pint.UnitRegistry().Quantity(1000, "foot")
    assert _heights(feet, None, None) == pytest.approx(304.8)


def test_depth_is_negated():
    """A depth is negated once, and a negative depth is above sea level."""
    assert _heights(None, 4000, None) == -4000.0
    assert _heights(None, -10, None) == 10.0
    assert _heights(None, 1000, "ft") == pytest.approx(-304.8)


def test_masked_and_nan_are_missing():
    """A masked height and a NaN are both missing, read as NaN."""
    masked = np.ma.masked_array([1.0, 2.0, 3.0], mask=[0, 1, 0])
    np.testing.assert_array_equal(_heights(masked, None, None), [1.0, np.nan, 3.0])
    np.testing.assert_array_equal(_heights([np.nan, 1.0], None, None), [np.nan, 1.0])


def test_integers_read_as_float64():
    """Heights of integers, as bathymetry often comes, are float64 and exact."""
    result = _heights(np.array([-4000, 0, 120], dtype=np.int16), None, None)
    assert result.dtype == np.float64
    np.testing.assert_array_equal(result, [-4000.0, 0.0, 120.0])


def test_none_given():
    """No height and no depth give no heights."""
    assert _heights(None, None, None) is None


def test_height_with_depth():
    """A height and a depth are never given together."""
    with pytest.raises(ValueError, match=r"height.*depth"):
        _heights(1, 2, None)


@pytest.mark.parametrize("value", [np.inf, -np.inf])
def test_infinite(value):
    """An infinite height is refused, as a scalar or in an array."""
    with pytest.raises(ValueError, match="infinite"):
        _heights(value, None, None)
    with pytest.raises(ValueError, match=r"infinite.*index 1"):
        _heights([0.0, value], None, None)


def test_not_a_length():
    """A height in a unit that is not a length is refused, naming the unit."""
    with pytest.raises(ValueError, match="'hPa' is not a length"):
        _heights(1000, None, "hPa")


def test_vertical_units_with_a_quantity():
    """A quantity carries its own unit, so vertical_units is refused with one."""
    feet = pint.UnitRegistry().Quantity(1000, "foot")
    with pytest.raises(ValueError, match="vertical_units"):
        _heights(feet, None, "m")


def test_vertical_units_alone():
    """vertical_units names the unit of a height, so is refused with none."""
    with pytest.raises(ValueError, match="vertical_units"):
        _heights(None, None, "m")


@pytest.mark.parametrize("crs", ["EPSG:4979"])
def test_an_ellipsoidal_height(crs):
    """Heights above the ellipsoid are refused, as heights are above sea level."""
    with pytest.raises(ValueError, match="Ellipsoidal height"):
        _heights(1, None, None, crs=crs)


def test_no_heights_with_an_ellipsoidal_height():
    """A CRS with an ellipsoidal height is accepted when no height is given."""
    assert _heights(None, None, None, crs="EPSG:4979") is None


@pytest.mark.parametrize("crs", ["EPSG:9705", "EPSG:4326+3855"])
def test_a_gravity_related_height(crs):
    """A CRS whose height is gravity-related is accepted with heights."""
    assert _heights(1, None, None, crs=crs) == 1.0


def test_a_scalar_for_every_point():
    """A scalar gives every point that height."""
    np.testing.assert_array_equal(_for_points(5.0, 4, 1), [5.0] * 4)


def test_one_value_for_the_whole_mesh():
    """An array of one value is one height for the whole mesh."""
    np.testing.assert_array_equal(_for_points(np.array([5.0]), 4, 1), [5.0] * 4)


def test_one_for_each_point():
    """An array of one height for each point is read in C order."""
    result = _for_points(np.array([[1.0, 2.0], [3.0, 4.0]]), 4, 1)
    assert result.dtype == np.float64
    np.testing.assert_array_equal(result, [1.0, 2.0, 3.0, 4.0])


def test_cells_are_refused():
    """A height for each cell is refused, naming the issue that would add it."""
    with pytest.raises(ValueError, match="2728"):
        _for_points(np.arange(12.0), 20, 12)


def test_points_win_over_cells():
    """An array that fits both the points and the cells is read as points."""
    np.testing.assert_array_equal(
        _for_points(np.arange(4.0), 4, 4), [0.0, 1.0, 2.0, 3.0]
    )


def test_the_wrong_size_is_refused():
    """An array fitting neither the points nor the whole mesh is refused."""
    with pytest.raises(ValueError, match=r"20 points.*7"):
        _for_points(np.arange(7.0), 20, 12)


@pytest.mark.parametrize(
    "zlevel", [None, 0, 0.0, np.zeros(3)], ids=["none", "0", "0.0", "zeros"]
)
def test_zero_counts_as_none(zlevel):
    """A z-level of 0 is no z-level."""
    _refuse_zlevel(zlevel)


@pytest.mark.parametrize("zlevel", [2, [0, 1]], ids=["scalar", "array"])
def test_a_zlevel_is_refused(zlevel):
    """A z-level other than 0 is refused with heights, naming it."""
    with pytest.raises(ValueError, match=rf"z-level.*{zlevel}".replace("[", r"\[")):
        _refuse_zlevel(zlevel)


class _Variable:
    """A variable that carries its units as an attribute, as xarray and netCDF4 do."""

    units = "m"

    def __init__(self, values: list[float]) -> None:
        self.values = np.asarray(values)

    def __array__(self, dtype=None, copy=None) -> np.ndarray:
        return self.values if dtype is None else self.values.astype(dtype)


@pytest.mark.parametrize(
    ("height", "depth"), [(_Variable([1.0]), None), (None, _Variable([1.0]))]
)
def test_a_value_with_units_names_vertical_units(height, depth):
    """A value that carries its own units is refused, naming vertical_units."""
    with pytest.raises(ValueError, match=r"carries its own units.*vertical_units='m'"):
        _heights(height, depth, None)
