import numpy as np

import geovista as gv

M, N = 45, 90
lats = np.linspace(-90, 90, M + 1)
lons = np.linspace(-180, 180, N + 1)
mlons, mlats = np.meshgrid(lons, lats, indexing="xy")
data = np.random.random(M * N)

mesh = gv.Transform.from_2d(mlons, mlats, data=data, name="synthetic")

plotter = gv.GeoPlotter()
plotter.add_mesh(mesh, cmap="tempo", show_edges=False)
plotter.add_coastlines(resolution="10m", color="white", line_width=3)
plotter.add_axes()
plotter.add_text(
    "2-D Synthetic Face Data (M+1, N+1)",
    position="upper_left",
    font_size=10,
    shadow=True,
)
plotter.show()
