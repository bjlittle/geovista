# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Configures custom :doc:`pyvista <pyvista:index>` themes for ``geovista``.

These themes are discoverable by ``pyvista`` and registered
through ``[project.entry-points]`` TOML table metadata (``PEP621``) in our
``pyproject.toml``.

Registered themes may be enabled through :func:`geovista.set_plot_theme`,
:func:`pyvista.set_plot_theme` or the ``PYVISTA_PLOT_THEME`` environment variable.

See Also
--------
:func:`pyvista.registered_themes`
    Enumeration of available registered themes.

Notes
-----
.. versionadded:: 0.6.0

"""

from __future__ import annotations

import copy
import os
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


# support theme restoration with a stack of previous themes
_cached_themes: list[Theme] = []


class ThemeMixin:
    """Common ``geovista`` plotting theme property state.

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
    """Default ``geovista`` plot theme.

    Notes
    -----
    .. versionadded:: 0.6.0

    Examples
    --------
    Make the ``geovista`` theme the global default using an
    instance of the theme.

    >>> import pyvista as pv
    >>> from geovista.themes import GeoVistaTheme
    >>> pv.set_plot_theme(GeoVistaTheme())

    Alternatively, enable the theme via its string name.

    >>> pv.set_plot_theme("geovista")

    """

    _default_name: ClassVar[str] = "geovista"

    def __init__(self) -> None:
        """Default plotting theme for ``geovista``."""
        super().__init__()
        # apply common theme state to the theme instance
        self.mixin_state()


class GeoVistaDocumentTheme(DocumentTheme, ThemeMixin):  # type: ignore[misc]
    """Theme used for building the documentation.

    Notes
    -----
    .. versionadded:: 0.6.0

    Examples
    --------
    Make the ``geovista_document`` theme the global default using an
    instance of the theme.

    >>> import pyvista as pv
    >>> from geovista.themes import GeoVistaDocumentTheme
    >>> pv.set_plot_theme(GeoVistaDocumentTheme())

    Alternatively, enable the theme via its string name.

    >>> pv.set_plot_theme("geovista_document")

    """

    _default_name: ClassVar[str] = "geovista_document"

    def __init__(self) -> None:
        """Documentation plotting theme for ``geovista``."""
        super().__init__()
        # apply common theme state to the theme instance
        self.mixin_state()


def resolve_theme_name(name: str) -> Theme | None:
    """Create an instance of the registered theme or dotted path theme class.

    Parameters
    ----------
    name : str
        The name of the registered theme to lookup or the dotted path
        ``package.module:ClassName`` theme to be created.

    Returns
    -------
    Theme | None
        An instance of the theme or ``None`` if the requested theme
        is not registered.

    Raises
    ------
    ValueError
        When `name` is an invalid dotted path specification or cannot be imported.

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


def restore_plot_theme() -> Theme | None:
    """Activate the previous plot theme.

    Provides a convenience to undo the last call to
    :func:`geovista.themes.set_plot_theme`. Note that the entire call stack
    history is cached, so multiple calls to :func:`geovista.themes.set_plot_theme`
    may be undone in reverse order to restore a previous theme.

    When no cached theme is available, the current theme will remain active and
    ``None`` is returned.

    Returns
    -------
    Theme | None
        The previously cached theme if available, otherwise ``None``.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    previous_theme = _cached_themes.pop() if _cached_themes else None

    if previous_theme is not None:
        pv.set_plot_theme(previous_theme)

    return previous_theme


def set_plot_theme(
    theme: Theme | str,
    /,
    *,
    bootstrap: bool | None = False,
) -> bool:
    """Set plotting parameters to a predefined theme.

    The enabled plot theme will be used by all plotters and rendering.

    Requests to enable a plot theme will be ignored when the environment variable
    ``GEOVISTA_DISABLE_PLOT_THEME`` is set.

    Note that the replaced theme is cached and may be restored with
    :func:`geovista.themes.restore_plot_theme`.

    Parameters
    ----------
    theme : Theme or str
        The theme to apply, which may be either:

        * The string name of a registered theme. See :func:`pyvista.registered_themes`
          for the available :doc:`pyvista <pyvista:index>` built-in and
          third-party entry-point group themes.
        * A string ``package.module:ClassName`` dotted path to an importable
          :class:`pyvista.plotting.themes.Theme` subclass.
        * A :class:`pyvista.plotting.themes.Theme` subclass instance.
    bootstrap : bool, default=False
        When ``True``, theme configuration is skipped if the environment
        variable ``PYVISTA_PLOT_THEME`` is set. Otherwise, the provided `theme`
        will be enabled regardless of that environment variable. This behaviour
        allows a pre-defined ``PYVISTA_PLOT_THEME`` to take precedence.

    Returns
    -------
    bool
        ``True`` if the theme was successfully enabled, otherwise ``False``.

    Raises
    ------
    ValueError
        When `theme` is an invalid dotted path specification or cannot be imported.

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
    Set the default ``geovista`` theme.

    >>> import geovista as gv
    >>> gv.set_plot_theme("geovista")
    True

    Set the pyvista dark theme.

    >>> gv.set_plot_theme("dark")
    True

    Load a theme from an importable package module specified as a dotted path.

    >>> gv.set_plot_theme("geovista.themes:GeoVistaTheme")
    True

    Set the pyvista paraview theme.

    >>> from pyvista import themes
    >>> gv.set_plot_theme(themes.ParaViewTheme())
    True

    """
    if bootstrap and os.environ.get("PYVISTA_PLOT_THEME"):
        return False

    snapshot = copy.deepcopy(pv.global_theme)

    if not (gvc.GEOVISTA_DISABLE_PLOT_THEME or gvc.GEOVISTA_IMAGE_TESTING):
        if isinstance(theme, str):
            resolved = resolve_theme_name(theme)

            if resolved is None:
                allowed = ", ".join(_available_theme_names())
                emsg = (
                    f'Theme "{theme}" not found. Available themes: {allowed}. '
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

        _cached_themes.append(snapshot)
        result = True
    else:
        result = False

    return result
