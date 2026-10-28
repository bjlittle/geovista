# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.units.as_quantity`."""

from __future__ import annotations

import pint

from geovista.units import as_quantity


def test_a_length_in_metres_in_the_application_registry():
    """Test that a length is a quantity in metres that adds to pint's own."""
    quantity = as_quantity(6378137.0)
    assert format(quantity.units, "D") == "meter"
    assert quantity.magnitude == 6378137.0
    other = pint.get_application_registry().Quantity(1, "km")
    assert (quantity + other).to("m").magnitude == 6379137.0


def test_the_magnitude_is_a_float():
    """Test that an int length gives a float magnitude."""
    assert type(as_quantity(1).magnitude) is float


def test_honours_the_application_registry_set():
    """Test that the registry is read at each call, not when first imported."""
    previous = pint.get_application_registry().get()
    registry = pint.UnitRegistry()
    pint.set_application_registry(registry)
    try:
        assert (as_quantity(1.0) + registry.Quantity(1, "m")).magnitude == 2.0
    finally:
        pint.set_application_registry(previous)
