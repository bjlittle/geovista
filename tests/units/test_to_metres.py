# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.units.to_metres`."""

from __future__ import annotations

import re

import netCDF4
import numpy as np
import pint
import pint_cf
import pytest

from geovista.units import to_metres

#: Heights, in the unit under test, from the deepest trench to above the
#: highest summit, with a value no factor can scale exactly by accident.
H = np.array([0.0, 1.0, 1000.0, 8848.86, 29031.7, -10994.0, 1e-9 / 3])


def test_plain_number_is_metres():
    """Test that a plain number is read as metres, and comes back a float."""
    result = to_metres(6378137.0)
    assert result == 6378137.0
    assert type(result) is float


def test_plain_array_is_metres():
    """Test that a plain array is read as metres, as float64."""
    result = to_metres(H)
    assert np.array_equal(result, H)
    assert result.dtype == np.float64


def test_integers_become_float64():
    """Test that integer metres become float64."""
    assert to_metres(np.array([1, 2])).dtype == np.float64


@pytest.mark.parametrize(
    ("units", "factor"),
    [("m", 1.0), ("km", 1000.0), ("ft", 0.3048), ("nautical_mile", 1852.0)],
)
def test_cf_string_is_exact(units, factor):
    """Test that a CF unit string converts to metres exactly."""
    assert np.array_equal(to_metres(H, units), H * factor)


@pytest.mark.parametrize(
    "registry",
    [pint.UnitRegistry(), pint_cf.cf_unitregistry()],
    ids=["pint", "pint-cf"],
)
@pytest.mark.parametrize(
    ("units", "factor"),
    [
        ("meter", 1.0),
        ("kilometer", 1000.0),
        ("foot", 0.3048),
        ("nautical_mile", 1852.0),
    ],
)
def test_quantity_from_any_registry_is_exact(registry, units, factor):
    """Test that a quantity from any registry converts to metres exactly."""
    assert np.array_equal(to_metres(registry.Quantity(H, units)), H * factor)


def test_short_form_is_never_read():
    """Test that a nautical mile is not read as its short form, a nano mile."""
    assert to_metres(pint.UnitRegistry().Quantity(1.0, "nmi")) == 1852.0


@pytest.mark.parametrize(
    "fmt", ["", "~", "P", "~P", "L", "~L", "H", "~H", "C", "~C", "D", "~D"]
)
def test_long_form_whatever_the_display_format(fmt):
    """Test that a registry's display format never changes what is read."""
    registry = pint.UnitRegistry()
    registry.formatter.default_format = fmt
    assert to_metres(registry.Quantity(1.0, "nautical_mile")) == 1852.0


def test_float32_magnitude_becomes_float64():
    """Test that a float32 magnitude is converted as float64."""
    assert to_metres(H.astype(np.float32), "km").dtype == np.float64


def test_numpy_scalar_gives_float():
    """Test that a NumPy scalar comes back a Python float."""
    result = to_metres(np.float64(2.0), "km")
    assert result == 2000.0
    assert type(result) is float


@pytest.mark.parametrize(("units", "expected"), [(None, 1.0), ("km", 1000.0)])
def test_masked_values_become_nan(units, expected):
    """Test that a masked element becomes NaN, never its fill value."""
    result = to_metres(np.ma.masked_array([1.0, 2.0], mask=[False, True]), units)
    assert result[0] == expected
    assert np.isnan(result[1])


def test_non_finite_passes_through():
    """Test that a value that is not finite passes through, for heights to refuse."""
    assert np.isnan(to_metres(np.nan, "km"))
    assert to_metres(np.inf) == np.inf


@pytest.mark.parametrize("units", ["hPa", "degree", "1", "m2", ""])
def test_refuses_another_dimension(units):
    """Test that a unit of another dimension is refused, and named."""
    with pytest.raises(ValueError, match=re.escape(f"{units!r} is not a length")):
        to_metres(1.0, units)


def test_refuses_a_quantity_of_another_dimension():
    """Test that a quantity of another dimension is refused, and named."""
    with pytest.raises(ValueError, match="'hectopascal' is not a length"):
        to_metres(pint.UnitRegistry().Quantity(1000.0, "hPa"))


@pytest.mark.parametrize("units", ["not_a_unit", "m!!", "3 km", "m/0", "1/0 m"])
def test_refuses_an_unreadable_unit(units):
    """Test that a unit pint-cf cannot read is refused, and named."""
    emsg = re.escape(f"{units!r} is not a unit geovista can read")
    with pytest.raises(ValueError, match=emsg):
        to_metres(1.0, units)


def test_refuses_a_unit_only_another_registry_defines():
    """Test that a unit only another registry defines is refused, and named."""
    registry = pint.UnitRegistry()
    registry.define("gvhop = 1.7 * meter")
    with pytest.raises(ValueError, match="'gvhop' is not a unit geovista can read"):
        to_metres(registry.Quantity(1.0, "gvhop"))


def test_refuses_deprecated_cf_placeholder():
    """Test that a deprecated CF placeholder is refused, without a warning."""
    with pytest.raises(ValueError, match="'level' is not a length"):
        to_metres(1.0, "level")


def test_refuses_units_given_twice():
    """Test that a quantity given units as well is refused."""
    with pytest.raises(ValueError, match="not both"):
        to_metres(pint.UnitRegistry().Quantity(1.0, "m"), "km")


class CarriesUnits:
    """Stands in for an xarray DataArray, whose units are an attribute."""

    units = "km"

    def __array__(self, dtype=None, copy=None) -> np.ndarray:
        """Return the values, without their units."""
        return np.array([1.0, 2.0], dtype=dtype)


@pytest.fixture
def variable():
    """Return a netCDF4 variable in kilometres, whose units are an attribute."""
    dataset = netCDF4.Dataset("heights.nc", "w", diskless=True)
    dataset.createDimension("n", 2)
    result = dataset.createVariable("height", "f8", ("n",))
    result.units = "km"
    result[:] = [1.0, 2.0]
    yield result
    dataset.close()


@pytest.mark.parametrize("units", [None, "km"])
def test_refuses_a_value_that_carries_its_own_units(units):
    """Test that a value with a units attribute is refused, not read as metres."""
    with pytest.raises(ValueError, match="carries its own units, 'km'"):
        to_metres(CarriesUnits(), units)


def test_refuses_a_netcdf_variable(variable):
    """Test that a netCDF4 variable, which carries its units, is refused."""
    with pytest.raises(ValueError, match="carries its own units, 'km'"):
        to_metres(variable)
