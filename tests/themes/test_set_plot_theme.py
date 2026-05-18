# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.themes.set_plot_theme`."""

from __future__ import annotations

import os

import pytest
from pyvista.plotting.themes import ParaViewTheme, Theme

from geovista.themes import GeoVistaDocumentTheme, GeoVistaTheme, set_plot_theme


class UnregisteredTheme(Theme):
    """Unregistered theme for testing."""


def test_bootstrap__set_pyvista_plot_theme(mocker):
    """Test bootstrap option with environment variable."""
    mocker.patch.dict(os.environ, {"PYVISTA_PLOT_THEME": "geovista"}, clear=False)
    mock_pyvista_set_plot_theme = mocker.patch("pyvista.set_plot_theme")
    theme = mocker.sentinel.theme
    assert os.environ.get("PYVISTA_PLOT_THEME") == "geovista"
    assert set_plot_theme(theme, bootstrap=True) is False
    assert mock_pyvista_set_plot_theme.call_count == 0


def test_bootstrap__unset_pyvista_plot_theme(mocker):
    """Test bootstrap option without environment variable."""
    mocker.patch("geovista.themes.gvc.GEOVISTA_DISABLE_PLOT_THEME", new=False)
    mocker.patch("geovista.themes.gvc.GEOVISTA_IMAGE_TESTING", new=False)
    mock_pyvista_set_plot_theme = mocker.patch("pyvista.set_plot_theme")
    theme = UnregisteredTheme()
    snapshot = mocker.sentinel.snapshot
    mocker.patch("pyvista.global_theme", snapshot)
    cached_themes = mocker.patch("geovista.themes._cached_themes")
    assert os.environ.get("PYVISTA_PLOT_THEME") is None
    assert set_plot_theme(theme, bootstrap=True) is True
    assert mock_pyvista_set_plot_theme.call_count == 1
    assert mock_pyvista_set_plot_theme.call_args.args[0] is theme
    assert cached_themes.append.call_count == 1
    assert cached_themes.append.call_args.args[0] is snapshot


def test_disable_plot_theme(mocker):
    """Test disabling the plot theme."""
    mocker.patch("geovista.themes.gvc.GEOVISTA_DISABLE_PLOT_THEME", new=True)
    mocker.patch("geovista.themes.gvc.GEOVISTA_IMAGE_TESTING", new=False)
    mock_pyvista_set_plot_theme = mocker.patch("pyvista.set_plot_theme")
    theme = UnregisteredTheme()
    cached_themes = mocker.patch("geovista.themes._cached_themes")
    assert set_plot_theme(theme) is False
    assert mock_pyvista_set_plot_theme.call_count == 0
    assert cached_themes.append.call_count == 0


def test_image_testing(mocker):
    """Test image testing."""
    mocker.patch("geovista.themes.gvc.GEOVISTA_IMAGE_TESTING", new=True)
    mocker.patch("geovista.themes.gvc.GEOVISTA_DISABLE_PLOT_THEME", new=False)
    mock_pyvista_set_plot_theme = mocker.patch("pyvista.set_plot_theme")
    theme = UnregisteredTheme()
    cached_themes = mocker.patch("geovista.themes._cached_themes")
    assert set_plot_theme(theme) is False
    assert mock_pyvista_set_plot_theme.call_count == 0
    assert cached_themes.append.call_count == 0


def test_theme_name__unregistered(mocker):
    """Test trap for unregistered theme name."""
    mocker.patch("geovista.themes.gvc.GEOVISTA_DISABLE_PLOT_THEME", new=False)
    mocker.patch("geovista.themes.gvc.GEOVISTA_IMAGE_TESTING", new=False)
    unregistered = "mock_theme"
    with pytest.raises(ValueError, match=f'Theme "{unregistered}" not found'):
        _ = set_plot_theme(unregistered)


def test_theme_name__registered(mocker):
    """Test setting a registered theme by name."""
    mocker.patch("geovista.themes.gvc.GEOVISTA_DISABLE_PLOT_THEME", new=False)
    mocker.patch("geovista.themes.gvc.GEOVISTA_IMAGE_TESTING", new=False)
    theme = "geovista"
    snapshot = mocker.sentinel.snapshot
    mocker.patch("pyvista.global_theme", snapshot)
    cached_themes = mocker.patch("geovista.themes._cached_themes")
    mock_pyvista_set_plot_theme = mocker.patch("pyvista.set_plot_theme")
    assert set_plot_theme(theme) is True
    assert mock_pyvista_set_plot_theme.call_count == 1
    assert mock_pyvista_set_plot_theme.call_args.args[0].name == theme
    assert cached_themes.append.call_count == 1
    assert cached_themes.append.call_args.args[0] == snapshot


@pytest.mark.parametrize(
    "theme",
    [UnregisteredTheme(), GeoVistaDocumentTheme(), GeoVistaTheme(), ParaViewTheme()],
)
def test_theme_instance(mocker, theme):
    """Test setting a theme instance, regardless of registration."""
    mocker.patch("geovista.themes.gvc.GEOVISTA_DISABLE_PLOT_THEME", new=False)
    mocker.patch("geovista.themes.gvc.GEOVISTA_IMAGE_TESTING", new=False)
    snapshot = mocker.sentinel.snapshot
    mocker.patch("pyvista.global_theme", snapshot)
    cached_themes = mocker.patch("geovista.themes._cached_themes")
    mock_pyvista_set_plot_theme = mocker.patch("pyvista.set_plot_theme")
    assert set_plot_theme(theme) is True
    assert mock_pyvista_set_plot_theme.call_count == 1
    assert mock_pyvista_set_plot_theme.call_args.args[0] is theme
    assert cached_themes.append.call_count == 1
    assert cached_themes.append.call_args.args[0] is snapshot


def test_bad_theme_type(mocker):
    """Test trap for bad theme type."""
    mocker.patch("geovista.themes.gvc.GEOVISTA_DISABLE_PLOT_THEME", new=False)
    mocker.patch("geovista.themes.gvc.GEOVISTA_IMAGE_TESTING", new=False)
    bad_theme = 42
    with pytest.raises(TypeError, match="Expected a theme type of"):
        _ = set_plot_theme(bad_theme)
