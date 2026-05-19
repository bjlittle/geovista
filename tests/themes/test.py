# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :mod:`geovista.themes`."""

from __future__ import annotations

import pytest
import pyvista as pv
from pyvista.plotting.themes import Theme

import geovista as gv
from geovista.themes import GeoVistaDocumentTheme, GeoVistaTheme

registered: set[str] = {theme.name for theme in pv.registered_themes()}
themes: list[Theme] = [GeoVistaDocumentTheme, GeoVistaTheme]
theme_names: list[str] = [theme().name for theme in themes]


@pytest.mark.parametrize(
    ("cls", "name"),
    [*zip(themes, theme_names, strict=True)],
)
def test_name(cls, name):
    """Test the theme name."""
    theme = cls()
    assert theme.name == name


@pytest.mark.parametrize("cls", themes)
def test_inherit(cls):
    """Test the theme inherits from ``pyvista`` base class."""
    theme = cls()
    assert isinstance(theme, Theme)


def test_default_theme():
    """Test no trap for adding an empty mesh to plotter with default theme."""
    assert pv.global_theme.name == "geovista"
    empty = pv.PolyData()
    p = gv.GeoPlotter()
    _ = p.add_mesh(empty)


@pytest.mark.parametrize("cls", themes)
def test_allow_empty_mesh(cls):
    """Test no trap for adding an empty mesh to plotter with theme."""
    theme = cls()
    empty = pv.PolyData()
    p = gv.GeoPlotter(theme=theme)
    assert p.theme.name == theme.name
    _ = p.add_mesh(empty)


@pytest.mark.parametrize("name", theme_names)
def test_allow_empty_mesh__by_name(name):
    """Test no trap for adding an empty mesh to plotter with theme."""
    empty = pv.PolyData()
    p = gv.GeoPlotter(theme=name)
    assert p.theme.name == name
    _ = p.add_mesh(empty)


@pytest.mark.parametrize("name", theme_names)
def test_registered(name):
    """Test the theme is discoverable and auto-registered."""
    assert name in registered
