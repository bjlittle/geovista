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

import pyvista as pv

from . import GEOVISTA_IMAGE_TESTING

theme = pv.themes.Theme()
"""Customised plotting :class:`~pyvista.plotting.themes.Theme` for geovista."""
theme.name = "geovista"
theme.allow_empty_mesh = True
theme.background = (1.0, 1.0, 1.0)
theme.cmap = "balance"
theme.color = "lightgray"
theme.edge_color = "gray"
theme.font.color = (0.0, 0.0, 0.0)
theme.outline_color = (0.0, 0.0, 0.0)
theme.title = "GeoVista"

if not GEOVISTA_IMAGE_TESTING:
    # only load the geovista theme if we're not performing image testing,
    # as the default pyvista testing theme is adopted instead
    pv.global_theme.load_theme(theme)
