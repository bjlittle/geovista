#!/usr/bin/env python3

import geovista as gv
from geovista.pantry import lfric_orog
import geovista.theme

# load the sample data
sample = lfric_orog()

# create the mesh from the sample data
mesh = gv.Transform.from_unstructured(
    sample.lons,
    sample.lats,
    sample.connectivity,
    data=sample.data,
    start_index=sample.start_index,
    name=sample.name,
)

# warp the mesh nodes by the surface altitude
mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
mesh.warp_by_scalar(scalars=sample.name, inplace=True, factor=2e-5)

# plot the mesh
plotter = gv.GeoPlotter()
sargs = dict(title=f"{sample.name} / {sample.units}")
plotter.add_mesh(mesh, show_edges=True, scalar_bar_args=sargs)
plotter.add_axes()
plotter.add_text(
    "LFRic Unstructured Cube-Sphere",
    position="upper_left",
    font_size=10,
    shadow=True,
)
plotter.show()
