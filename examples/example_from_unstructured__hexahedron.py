#!/usr/bin/env python3

import geovista as gv
from geovista.pantry import hexahedron
import geovista.theme

# load the sample data
sample = hexahedron()

# create the mesh from the sample data
mesh = gv.Transform.from_unstructured(sample.lons, sample.lats, data=sample.data)

# plot the mesh
plotter = gv.GeoPlotter()
sargs = dict(title=f"{sample.name} / {sample.units}")
plotter.add_mesh(mesh, show_edges=True, scalar_bar_args=sargs)
resolution = "10m"
plotter.add_coastlines(resolution=resolution, color="white")
plotter.add_axes()
plotter.add_text(
    f"DYNAMICO Hexahedron ({resolution} Coastlines)",
    position="upper_left",
    font_size=10,
    shadow=True,
)
plotter.show()
