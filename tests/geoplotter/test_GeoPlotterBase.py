# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.geoplotter.GeoPlotterBase`."""

from __future__ import annotations

import pytest
import pyvista as pv

from geovista.geoplotter import GeoPlotter, GeoPlotterBase
from geovista.globe import Globe


def test_runtime_base_is_object():
    """The plotter base mypy sees never reaches runtime (typing spec §3.5)."""
    assert GeoPlotterBase.__bases__ == (object,)


def test_geoplotter_mro():
    """GeoPlotter still finds its own methods before pyvista's."""
    mro = GeoPlotter.__mro__

    assert mro.index(GeoPlotterBase) < mro.index(pv.Plotter)


def test_the_default_globe():
    """Test a scene is drawn on the default globe unless given another."""
    assert GeoPlotter().globe == Globe()


def test_a_given_globe():
    """Test a scene reports the globe it is given."""
    globe = Globe(render_radius=2, exaggeration=20)
    assert GeoPlotter(globe=globe).globe is globe


def test_the_globe_cannot_be_set():
    """Test the globe of a scene cannot be replaced."""
    p = GeoPlotter()
    with pytest.raises(AttributeError):
        p.globe = Globe(render_radius=2)  # type: ignore[misc]


def test_a_number_is_not_a_globe():
    """Test a number given as the globe is refused."""
    with pytest.raises(TypeError, match=r"geovista\.Globe"):
        GeoPlotter(globe=2)
