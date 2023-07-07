"""Configures a custom pyvista theme for geovista.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

import pyvista as pv

theme = pv.themes.Theme()
theme.name = "geovista"
theme.background = (1.0, 1.0, 1.0)
theme.color = "lightgray"
theme.cmap = "balance"
theme.edge_color = "gray"
theme.font.color = (0.0, 0.0, 0.0)
theme.outline_color = (0.0, 0.0, 0.0)
theme.title = "GeoVista"
pv.global_theme.load_theme(theme)
