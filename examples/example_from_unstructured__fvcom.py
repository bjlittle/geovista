#!/usr/bin/env python3

import geovista as gv
from geovista.pantry import fvcom_tamar
import geovista.theme

# load the sample data
sample = fvcom_tamar()

# create the mesh from the sample data
mesh = gv.Transform.from_unstructured(
    sample.lons, sample.lats, sample.connectivity, sample.face, name="face"
)

# warp the mesh nodes by the bathymetry
mesh.point_data["node"] = sample.node
mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
mesh.warp_by_scalar(scalars="node", inplace=True, factor=2e-5)

# plot the mesh
plotter = gv.GeoPlotter()
sargs = dict(title=f"{sample.name} / {sample.units}")
plotter.add_mesh(mesh, show_edges=True, scalar_bar_args=sargs)
plotter.add_axes()
plotter.add_text(
    "PML FVCOM Tamar",
    position="upper_left",
    font_size=10,
    shadow=True,
)
plotter.show()
