# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :mod:`geovista.theme`."""

from __future__ import annotations

import importlib

import pytest
import pyvista as pv

import geovista
from geovista import GEOVISTA_IMAGE_TESTING


@pytest.mark.skipif(GEOVISTA_IMAGE_TESTING, reason="geovista image testing")
def test_default():
    """Test no trap for adding an empty mesh to plotter with default theme."""
    assert pv.global_theme.name != "geovista"
    empty = pv.PolyData()
    p = geovista.GeoPlotter()
    _ = p.add_mesh(empty)


@pytest.mark.skipif(GEOVISTA_IMAGE_TESTING, reason="geovista image testing")
def test_theme():
    """Test trap for adding an empty mesh to plotter with geovista theme."""
    original = pv.global_theme
    assert original.name != "geovista"
    # the nature of this test will change when our theme
    # is not an import side-effect, tsk!
    _ = importlib.import_module("geovista.theme")
    theme = pv.global_theme
    assert theme.name == "geovista"
    assert theme.allow_empty_mesh
    empty = pv.PolyData()
    p = geovista.GeoPlotter()
    _ = p.add_mesh(empty)
    # reload the original theme
    pv.global_theme.load_theme(original)
    assert pv.global_theme.name == original.name
