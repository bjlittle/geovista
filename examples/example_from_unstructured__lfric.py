import iris
from iris.experimental.ugrid import PARSE_UGRID_ON_LOAD
import pyvista as pv

import geovista as gv

fname = "./qrclim.sst.ugrid.nc"
with PARSE_UGRID_ON_LOAD.context():
    cube = iris.load_cube(fname)[0]

face_node = cube.mesh.face_node_connectivity
indices = face_node.indices_by_src()
lons, lats = cube.mesh.node_coords

mesh = gv.Transform.from_unstructured(
    lons.points,
    lats.points,
    indices,
    data=cube.data,
    start_index=face_node.start_index,
    name=cube.name(),
)
coastlines = gv.get_coastlines("10m")

plotter = pv.Plotter()
sargs = dict(title=f"{cube.name()} / {cube.units}")
plotter.add_mesh(mesh, cmap="balance", show_edges=True, scalar_bar_args=sargs)
plotter.add_mesh(coastlines, color="white")
plotter.add_axes()
plotter.show()
