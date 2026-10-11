# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.geoplotter.GeoPlotterBase`."""

from __future__ import annotations

import pyvista as pv

from geovista.geoplotter import GeoPlotter, GeoPlotterBase


def test_runtime_base_is_object():
    """The plotter base mypy sees never reaches runtime (typing spec §3.5)."""
    assert GeoPlotterBase.__bases__ == (object,)


def test_geoplotter_mro():
    """GeoPlotter still finds its own methods before pyvista's."""
    mro = GeoPlotter.__mro__

    assert mro.index(GeoPlotterBase) < mro.index(pv.Plotter)
