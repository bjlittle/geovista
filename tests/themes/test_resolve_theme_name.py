# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.themes.resolve_theme_name`."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from geovista.themes import GeoVistaDocumentTheme, GeoVistaTheme, resolve_theme_name

if TYPE_CHECKING:
    from pyvista.plotting.themes import Theme

themes: list[Theme] = [GeoVistaDocumentTheme, GeoVistaTheme]
theme_names: list[str] = [theme().name for theme in themes]


def test_unregistered_theme():
    """Test unregistered theme name."""
    assert resolve_theme_name("shame") is None


@pytest.mark.parametrize(
    ("dotted", "name"),
    [
        ("geovista.themes:GeoVistaDocumentTheme", "geovista_document"),
        ("geovista.themes:GeoVistaTheme", "geovista"),
        ("pyvista.plotting.themes:DocumentTheme", "document"),
    ],
)
def test_dotted_path(dotted, name):
    """Test dotted path resolution."""
    theme = resolve_theme_name(dotted)
    assert theme is not None
    assert theme.name == name


@pytest.mark.parametrize("name", theme_names)
def test_registered_theme(name):
    """Test registered theme name."""
    theme = resolve_theme_name(name)
    assert theme is not None
    assert theme.name == name


def test_bad_dotted_path__spec():
    """Test bad dotted path specification."""
    with pytest.raises(ValueError, match="Invalid theme spec"):
        _ = resolve_theme_name("geovista.themes:")


def test_bad_dotted_path__import():
    """Test bad dotted path import."""
    with pytest.raises(ValueError, match="Cannot import"):
        _ = resolve_theme_name("wibble:Shame")
