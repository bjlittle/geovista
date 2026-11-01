# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.globe.Globe`."""

from __future__ import annotations

import ast
import copy
import math
import pickle

import numpy as np
import pint
import pytest

import geovista
from geovista.common import RADIUS
from geovista.globe import Globe
from geovista.units import to_metres

#: The WGS84 semi-major axis, in metres.
EARTH = 6378137.0

#: The keyword arguments of a globe.
KEYWORDS = ["radius", "render_radius", "exaggeration", "exaggeration_below"]


def test_the_defaults():
    """Test that the default globe is the WGS84 Earth, drawn at RADIUS."""
    globe = Globe()
    assert globe.radius.to("m").magnitude == EARTH
    assert (globe.render_radius, globe.exaggeration, globe.exaggeration_below) == (
        RADIUS,
        1.0,
        1.0,
    )


@pytest.mark.parametrize(
    "radius",
    [
        6371000,
        6371000.0,
        np.float32(6371000.0),
        pint.UnitRegistry().Quantity(6371, "km"),
        pint.get_application_registry().Quantity(6371000, "m"),
        to_metres(6371, "km"),
    ],
)
def test_a_radius_in_each_form_reads_as_metres(radius):
    """Test that a radius as a number, a quantity or from a unit string is metres.

    Holds crs spec §2 decision 13.
    """
    assert Globe(radius=radius).radius.to("m").magnitude == 6371000.0


@pytest.mark.parametrize("keyword", KEYWORDS)
@pytest.mark.parametrize("value", [0, -1.0, math.inf, math.nan])
def test_a_value_not_finite_and_positive_is_refused(keyword, value):
    """Test that each value must be finite and positive."""
    with pytest.raises(ValueError, match=f"{keyword} must be finite and positive"):
        Globe(**{keyword: value})


@pytest.mark.parametrize("keyword", KEYWORDS)
@pytest.mark.parametrize("value", [True, "6371 km", "20"])
def test_a_value_of_the_wrong_type_is_refused(keyword, value):
    """Test that a bool or a string is refused, rather than read as a number."""
    with pytest.raises(TypeError, match=keyword):
        Globe(**{keyword: value})


def test_a_radius_is_one_length():
    """Test that an array is refused as a radius."""
    with pytest.raises(TypeError, match="radius"):
        Globe(radius=np.array([1.0, 2.0]))


def test_a_radius_quantity_is_one_length():
    """Test that a quantity holding an array is refused as a radius."""
    with pytest.raises(TypeError, match="radius"):
        Globe(radius=pint.UnitRegistry().Quantity(np.array([1.0, 2.0]), "km"))


@pytest.mark.parametrize("keyword", KEYWORDS[1:])
def test_a_ratio_is_a_plain_number(keyword):
    """Test that a quantity is refused as a render radius or a factor."""
    with pytest.raises(TypeError, match=keyword):
        Globe(**{keyword: pint.UnitRegistry().Quantity(2, "m")})


def test_exaggeration_alone_sets_both_factors():
    """Test that the exaggeration is the factor below too, by default."""
    globe = Globe(exaggeration=20)
    assert (globe.exaggeration, globe.exaggeration_below) == (20.0, 20.0)


def test_exaggeration_below_sets_the_factor_below_alone():
    """Test that the factor below leaves the factor above at 1."""
    globe = Globe(exaggeration_below=100)
    assert (globe.exaggeration, globe.exaggeration_below) == (1.0, 100.0)


def test_an_int_factor_reads_back_as_a_float():
    """Test that an int factor is kept as a float."""
    globe = Globe(exaggeration=20, exaggeration_below=100)
    assert type(globe.exaggeration) is float
    assert type(globe.exaggeration_below) is float


def test_a_factor_below_one_is_accepted():
    """Test that a factor below 1, which flattens heights, is accepted."""
    assert Globe(exaggeration=0.5).exaggeration == 0.5


@pytest.mark.parametrize("render_radius", [1.0, EARTH])
def test_the_scale(render_radius):
    """Test that the scale is the render radius over the radius."""
    assert Globe(render_radius=render_radius).scale == render_radius / EARTH


def test_equal_values_make_equal_globes():
    """Test that globes of equal values are equal, and hash equally."""
    one = Globe(
        radius=6371000, render_radius=2, exaggeration=20, exaggeration_below=100
    )
    two = Globe(
        radius=pint.UnitRegistry().Quantity(6371, "km"),
        render_radius=2.0,
        exaggeration=20.0,
        exaggeration_below=100.0,
    )
    assert one == two
    assert hash(one) == hash(two)
    assert one != Globe(radius=6371000, render_radius=2, exaggeration=20)
    assert Globe() != object()


def test_a_globe_cannot_be_changed():
    """Test that a globe is immutable."""
    with pytest.raises(AttributeError):
        Globe().render_radius = 2.0
    with pytest.raises(AttributeError):
        Globe()._radius = 2.0


def test_a_globe_copies_and_pickles():
    """Test that a copy or an unpickled globe equals the original."""
    globe = Globe(
        radius=6371000, render_radius=2, exaggeration=20, exaggeration_below=100
    )
    assert copy.copy(globe) == globe
    assert copy.deepcopy(globe) == globe
    assert pickle.loads(pickle.dumps(globe)) == globe  # noqa: S301


def test_a_copy_names_each_value(monkeypatch):
    """Test that the order of a globe's values does not decide what a copy gets."""
    values = Globe._values
    monkeypatch.setattr(Globe, "_values", lambda self: tuple(reversed(values(self))))
    globe = Globe(
        radius=6371000, render_radius=2, exaggeration=20, exaggeration_below=100
    )
    assert repr(copy.copy(globe)) == repr(globe)
    assert repr(copy.deepcopy(globe)) == repr(globe)
    assert repr(pickle.loads(pickle.dumps(globe))) == repr(globe)  # noqa: S301


def test_the_repr_rebuilds_the_globe():
    """Test that the repr is the call that builds the globe."""
    globe = Globe(
        radius=6371000, render_radius=2, exaggeration=20, exaggeration_below=100
    )
    call = ast.parse(repr(globe), mode="eval").body
    assert isinstance(call, ast.Call)
    assert ast.unparse(call.func) == "Globe"
    kwargs = {k.arg: ast.literal_eval(k.value) for k in call.keywords}
    assert Globe(**kwargs) == globe
    assert repr(Globe()) == (
        "Globe(radius=6378137.0, render_radius=1.0, exaggeration=1.0, "
        "exaggeration_below=1.0)"
    )


def test_the_radius_adds_to_a_quantity_of_the_application_registry():
    """Test that the radius is a quantity of pint's application registry."""
    other = pint.get_application_registry().Quantity(1, "km")
    assert (Globe().radius + other).to("m").magnitude == 6379137.0


def test_exported_at_the_top_level():
    """Test that the globe is exported by geovista."""
    assert geovista.Globe is Globe
