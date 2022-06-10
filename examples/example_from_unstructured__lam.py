import iris
from iris.experimental.ugrid import PARSE_UGRID_ON_LOAD

import geovista as gv
import geovista.theme

fname = "./lam.nc"
with PARSE_UGRID_ON_LOAD.context():
    cube = iris.load_cube(fname, "air_potential_temperature")[0]

face_node = cube.mesh.face_node_connectivity
indices = face_node.indices_by_location()
lons, lats = cube.mesh.node_coords

mesh = gv.Transform.from_unstructured(
    lons.points,
    lats.points,
    indices,
    data=cube.data,
    start_index=face_node.start_index,
    name=cube.name(),
)

plotter = gv.GeoPlotter()
sargs = dict(title=f"{cube.name()} / {cube.units}")
plotter.add_mesh(mesh, cmap="balance", show_edges=False, scalar_bar_args=sargs)
plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
plotter.add_coastlines(resolution="10m", color="white")
plotter.add_axes()
plotter.add_text(
    "Unstructured LAM Face Data (N, 4)",
    position="upper_left",
    font_size=10,
    shadow=True,
)
plotter.view_yz(negative=True)
plotter.show()
