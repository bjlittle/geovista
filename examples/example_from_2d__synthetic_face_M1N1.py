import numpy as np

import geovista as gv
import geovista.theme

# create the 2D spatial coordinates and data
M, N = 45, 90
lats = np.linspace(-90, 90, M + 1)
lons = np.linspace(-180, 180, N + 1)
mlons, mlats = np.meshgrid(lons, lats, indexing="xy")
data = np.random.random(M * N)

# create the mesh from the synthetic data
mesh = gv.Transform.from_2d(mlons, mlats, data=data, name="synthetic")

# plot the data
plotter = gv.GeoPlotter()
plotter.add_mesh(mesh, cmap="tempo", show_edges=True)
plotter.add_coastlines(resolution="10m", color="white")
plotter.add_axes()
plotter.add_text(
    "2-D Synthetic Face Data (M+1, N+1)",
    position="upper_left",
    font_size=10,
    shadow=True,
)
plotter.show()
