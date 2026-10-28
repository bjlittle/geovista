# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.globe._resolve`."""

from __future__ import annotations

import numpy as np
import pint
import pytest

from geovista.globe import Globe, _resolve


def test_none_is_the_default_globe():
    """No globe resolves to the default one."""
    assert _resolve(None) == Globe()


def test_a_globe_is_itself():
    """A globe resolves to itself."""
    globe = Globe(render_radius=2)
    assert _resolve(globe) is globe


@pytest.mark.parametrize(
    "value", [2, 2.0, np.float64(2.0), "2", pint.UnitRegistry().Quantity(2, "m")]
)
def test_a_number_is_not_a_globe(value):
    """A number, as a radius was given, is refused, naming the call to make."""
    with pytest.raises(TypeError, match=r"globe must be a geovista\.Globe") as info:
        _resolve(value)
    assert "Globe(render_radius=" in str(info.value)
