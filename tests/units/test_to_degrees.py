# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.units.to_degrees`."""

from __future__ import annotations

import re

import numpy as np
import pint
import pint_cf
import pytest

from geovista.units import to_degrees


def test_plain_number_is_degrees():
    """Test that a plain number is read as degrees, and comes back a float."""
    result = to_degrees(45.0)
    assert result == 45.0
    assert type(result) is float


@pytest.mark.parametrize(
    "units", ["degree", "degrees", "degrees_north", "degrees_east"]
)
def test_cf_degrees(units):
    """Test that each CF spelling of a degree reads as a degree."""
    assert to_degrees(45.0, units) == 45.0


def test_radians():
    """Test that radians convert to degrees."""
    assert to_degrees(np.pi, "radian") == 180.0


def test_arcseconds():
    """Test that arcseconds convert to degrees."""
    assert to_degrees(3600.0, "arcsecond") == pytest.approx(1.0, rel=1e-12)


@pytest.mark.parametrize(
    "registry",
    [pint.UnitRegistry(), pint_cf.cf_unitregistry()],
    ids=["pint", "pint-cf"],
)
def test_quantity_from_any_registry(registry):
    """Test that a quantity from any registry converts to degrees."""
    result = to_degrees(registry.Quantity(np.array([0.0, np.pi / 2]), "radian"))
    assert result == pytest.approx([0.0, 90.0], rel=1e-12)


def test_turns_from_another_registry():
    """Test that a unit pint-cf spells differently, a turn, still converts."""
    result = to_degrees(pint.UnitRegistry().Quantity(0.5, "turn"))
    assert result == pytest.approx(180.0, rel=1e-12)


@pytest.mark.parametrize("units", ["1", "percent", "", "m/m"])
def test_refuses_a_dimensionless_angle(units):
    """Test that a dimensionless unit is refused, never read as radians."""
    with pytest.raises(ValueError, match=re.escape(f"{units!r} is dimensionless")):
        to_degrees(1.0, units)


def test_refuses_a_dimensionless_quantity_as_an_angle():
    """Test that a dimensionless quantity from another registry is refused."""
    with pytest.raises(ValueError, match="'dimensionless' is dimensionless"):
        to_degrees(pint.UnitRegistry().Quantity(1.0, "dimensionless"))


@pytest.mark.parametrize("units", ["m", "hPa"])
def test_refuses_another_dimension(units):
    """Test that a unit of another dimension is refused, and named."""
    with pytest.raises(ValueError, match=re.escape(f"{units!r} is not an angle")):
        to_degrees(1.0, units)
