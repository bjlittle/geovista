# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.themes.restore_plot_theme`."""

from __future__ import annotations

from geovista.themes import restore_plot_theme


def test_empty_cache(mocker):
    """Test an empty theme cache."""
    mocker.patch("geovista.themes._cached_themes", [])
    theme = restore_plot_theme()
    assert theme is None


def test_restore(mocker):
    """Test theme restoration."""
    mock_theme = mocker.sentinel.mock_theme
    mock_cached_themes = mocker.MagicMock(pop=mocker.MagicMock(return_value=mock_theme))
    cached_themes = mocker.patch("geovista.themes._cached_themes", mock_cached_themes)
    mock_set_plot_theme = mocker.patch("pyvista.set_plot_theme")
    theme = restore_plot_theme()
    assert theme is mock_theme
    assert cached_themes.pop.call_count == 1
    assert mock_set_plot_theme.call_count == 1
    assert mock_set_plot_theme.call_args.args[0] is mock_theme
