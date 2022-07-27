"""Define custom pyvista theme for geovista."""
import pyvista as pv

theme = pv.themes.DefaultTheme()
theme.background = (1.0, 1.0, 1.0)
theme.font.color = (0.0, 0.0, 0.0)
theme.outline_color = (0.0, 0.0, 0.0)
theme.title = "GeoVista"
pv.global_theme.load_theme(theme)
