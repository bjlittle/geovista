import numpy as np

import geovista as gv
import geovista.theme

M, N = 45, 90
lats = np.linspace(-90, 90, M + 1)
lons = np.linspace(-180, 180, N + 1)
data = np.random.random(M * N)

mesh = gv.Transform.from_1d(lons, lats, data=data, name="synthetic")

plotter = gv.GeoPlotter()
plotter.add_mesh(mesh, cmap="ice", show_edges=True)
plotter.add_coastlines(resolution="10m", color="white")
plotter.add_axes()
plotter.add_text(
    "1-D Synthetic Face Data (M+1,) (N+1,)",
    position="upper_left",
    font_size=10,
    shadow=True,
)
plotter.show()
