"""
This module configures a custom pyvista theme for geovista.

Notes
-----
.. versionadded:: 0.1.0

"""
import pyvista as pv

theme = pv.themes.DefaultTheme()
theme.name = "geovista"
theme.background = (1.0, 1.0, 1.0)
theme.cmap = "balance"
theme.edge_color = "grey"
theme.font.color = (0.0, 0.0, 0.0)
theme.outline_color = (0.0, 0.0, 0.0)
theme.title = "GeoVista"
pv.global_theme.load_theme(theme)
