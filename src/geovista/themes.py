# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Configures a custom pyvista theme for geovista.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

import contextlib
from enum import Enum

from pyvista.plotting import themes as pv_themes

from . import GEOVISTA_IMAGE_TESTING


class GeoVistaTheme(pv_themes.Theme):
    """A PyVista theme optimised for typical GeoVista operations.

    Notes
    -----
    .. versionadded:: 0.5.0

    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "geovista"
        self.background = (1.0, 1.0, 1.0)
        self.color = "lightgray"
        self.cmap = "balance"
        self.edge_color = "gray"
        self.font.color = (0.0, 0.0, 0.0)
        self.outline_color = (0.0, 0.0, 0.0)
        self.title = "GeoVista"


class NATIVE_THEMES(Enum):  # noqa: N801 (Python recommends UPPER_CASE for Enums)
    """Global built-in themes available to GeoVista.

    Notes
    -----
    .. versionadded:: 0.5.0

    """

    # This class is public, unlike the PyVista equivalent, to improve
    #  the documentation of valid themes.
    geovista = GeoVistaTheme


def set_plot_theme(theme: str | pv_themes.Theme) -> None:
    """Set the plotting parameters to a predefined theme.

    Calls :func:`pyvista.set_plot_theme`, with a widened set of options
    to include themes defined in :mod:`geovista.themes`.

    Parameters
    ----------
    theme : str or pyvista.themes.Theme
        The theme to apply. All inputs documented in
        :func:`pyvista.set_plot_theme` are accepted, as well as those
        documented in :data:`NATIVE_THEMES` (e.g. ``NATIVE_THEMES.foo`` OR
        ``"foo"`` work the same).

    Warnings
    --------
    To use a theme from :func:`pyvista.set_plot_theme` that has a name clash
    with a theme from :data:`NATIVE_THEMES`: either use a
    :class:`pyvista.plotting.themes.Theme` instance (see PyVista's
    :external+pyvista:doc:`api/plotting/theme`), or use
    :func:`pyvista.set_plot_theme` directly.

    Notes
    -----
    .. versionadded:: 0.5.0

    Examples
    --------
    >>> from geovista import themes

    The following are all equivalent:

    >>> themes.set_plot_theme("geovista")
    >>> themes.set_plot_theme(themes.GeoVistaTheme())
    >>> themes.set_plot_theme(themes.NATIVE_THEMES.geovista.value())

    References to PyVista themes are also accepted:

    >>> themes.set_plot_theme("document")

    """
    if isinstance(theme, str):
        theme = theme.lower()
        with contextlib.suppress(KeyError):
            # Lookup a Theme matching the string reference if possible.
            # String may still be a valid reference to a PyVista theme so
            #  keep going regardless of KeyError.
            theme = NATIVE_THEMES[theme].value

    try:
        pv_themes.set_plot_theme(theme)
    except ValueError as err:
        if "not found" in str(err) and isinstance(theme, str):
            # Neither GeoVista nor PyVista could find a theme matching the
            #  string reference.
            msg = f"Theme {theme} not found in GeoVista's native themes. {err}"
        else:
            # Don't modify any other ValueErrors.
            msg = str(err)
        raise ValueError(msg) from err


if not GEOVISTA_IMAGE_TESTING:
    # only load the geovista theme if we're not performing image testing,
    # as the default pyvista testing theme is adopted instead
    set_plot_theme(GeoVistaTheme())
