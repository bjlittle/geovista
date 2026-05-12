# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Configures custom pyvista themes for geovista.

These themes are discoverable by :doc:`pyvista <pyvista:index>` and registered
through ``project.entry-points`` metadata (``PEP621``) in our ``pyproject.toml``.

Registered themes may be enabled through :func:`set_plot_theme`,
:func:`pyvista.set_plot_theme` or the ``PYVISTA_PLOT_THEME`` environment variable.

See Also
--------
:func:`pyvista.registered_themes`
    The list of available registered themes.

Notes
-----
.. versionadded:: 0.6.0

"""

from __future__ import annotations

from copy import deepcopy
from typing import ClassVar

import lazy_loader as lazy
from pyvista.plotting.theme_registry import (
    _available_theme_names,
    _resolve_dotted_path,
    _resolve_theme,
)
from pyvista.plotting.themes import DocumentTheme, Theme

import geovista.config as gvc

# lazy import third-party dependencies
pv = lazy.load("pyvista")

__all__ = [
    "GeoVistaDocumentTheme",
    "GeoVistaTheme",
    "ThemeMixin",
    "resolve_theme_name",
    "restore_plot_theme",
    "set_plot_theme",
]


# support theme restoration with cache of previous theme (set_plot_theme)
_cached_theme: Theme | None = None


class ThemeMixin:
    """Common geovista theme property state.

    Notes
    -----
    .. versionadded:: 0.6.0

    """

    def mixin_state(self) -> None:
        """Configure common property state."""
        self.allow_empty_mesh = True
        self.background = "white"
        self.cmap = "balance"
        self.color = "lightgray"
        self.edge_color = "gray"
        self.font.label_size = None  # type: ignore[attr-defined]
        self.font.title_size = None  # type: ignore[attr-defined]
        self.font.color = "black"  # type: ignore[attr-defined]
        self.outline_color = "black"
        self.title = "GeoVista"


class GeoVistaTheme(Theme, ThemeMixin):  # type: ignore[misc]
    """Default geovista plot theme.

    Examples
    --------
    Make the geovista theme the global default.

    >>> import pyvista as pv
    >>> from geovista.themes import GeoVistaTheme
    >>> pv.set_plot_theme(GeoVistaTheme())

    Alternatively, set via a string.

    >>> pv.set_plot_theme("geovista")

    Notes
    -----
    .. versionadded:: 0.6.0

    """

    _default_name: ClassVar[str] = "geovista"

    def __init__(self) -> None:
        """Initialize the theme."""
        super().__init__()
        self.mixin_state()


class GeoVistaDocumentTheme(DocumentTheme, ThemeMixin):  # type: ignore[misc]
    """Theme used for building the documentation.

    Notes
    -----
    .. versionadded:: 0.6.0

    """

    _default_name: ClassVar[str] = "geovista_document"

    def __init__(self) -> None:
        """Initialize the theme."""
        super().__init__()
        self.mixin_state()


def resolve_theme_name(name: str) -> Theme:
    """Create an instance of the registered theme or arbitrary theme class.

    Parameters
    ----------
    name : str
        The name of the registered theme to lookup or the arbitrary
        ``package.module:ClassName`` theme to be created.

    Returns
    -------
    Theme
        An instance of the theme or ``None`` if the requested theme
        is not registered.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if ":" in name:
        cls = _resolve_dotted_path(name)
        theme = cls()
    else:
        theme = _resolve_theme(name)

    return theme


def restore_plot_theme() -> bool:
    """Activate the previous plot theme.

    Provides a convenience to undo the last call to :func:`set_plot_theme`.
    Note that only the single previous replaced theme is cached.

    Returns
    -------
    bool
        Whether the cached theme has been successfully activated.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    global _cached_theme  # noqa: PLW0603

    if success := _cached_theme is not None:
        pv.set_plot_theme(_cached_theme)
        _cached_theme = None

    return success


def set_plot_theme(theme: Theme | str = None) -> None:
    """Set plotting parameters to a predefined theme.

    This plot theme will be the default used by all geovista plotters.

    Note that the previous replaced theme is cached and may be restored with
    :func:`geovista.themes.restore_plot_theme`.

    Parameters
    ----------
    theme : Theme or str
        The theme to apply, which may be either:

        * A registered theme name. See :func:`pyvista.registered_themes` for
          the available :doc:`pyvista <pyvista:index>` built-in and
          third-party entry-point group themes.
        * A ``package.module:ClassName`` dotted path to an importable
          :class:`pyvista.plotting.themes.Theme` subclass.
        * A :class:`pyvista.plotting.themes.Theme` subclass instance.

    See Also
    --------
    :func:`geovista.themes.restore_plot_theme`
        Reinstates the plot theme to the previous replaced theme.
    :func:`pyvista.registered_themes`
        The list of available registered themes.
    :class:`pyvista.plotting.themes.Theme`
        Base class for all themes. Subclasses with the class property
        ``_default_name`` are discoverable by :doc:`pyvista <pyvista:index>`.

    Notes
    -----
    .. versionadded:: 0.6.0

    Examples
    --------
    Set the default geovista theme.

    >>> import geovista as gv
    >>> gv.set_plot_theme("geovista")

    Set the pyvista dark theme.

    >>> gv.set_plot_theme("dark")

    Load a theme from an importable package module specified as a dotted path.

    >>> gv.set_plot_theme("geovista.themes:GeoVistaTheme")

    Set the pyvista paraview theme.

    >>> from pyvista import themes
    >>> gv.set_plot_theme(themes.ParaViewTheme())

    """
    if not (gvc.GEOVISTA_DISABLE_PLOT_THEME or gvc.GEOVISTA_IMAGE_TESTING):
        snapshot = deepcopy(pv.global_theme)

        if isinstance(theme, str):
            resolved = resolve_theme_name(theme)

            if resolved is None:
                allowed = ", ".join(_available_theme_names())
                emsg = (
                    f"Theme {theme} not found. Available themes: {allowed}. "
                    'To load from an arbitrary module use "package.module:ClassName".'
                )
                raise ValueError(emsg)

            pv.set_plot_theme(resolved)
        elif isinstance(theme, Theme):
            pv.set_plot_theme(theme)
        else:
            emsg = (
                f'Expected a theme type of "pyvista.plotting.themes.Theme" or "str", '
                f'got "{type(theme).__name__}" instead.'
            )
            raise TypeError(emsg)

        global _cached_theme  # noqa: PLW0603
        _cached_theme = snapshot
