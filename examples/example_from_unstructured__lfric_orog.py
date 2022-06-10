import iris
from iris.experimental.ugrid import PARSE_UGRID_ON_LOAD

import geovista as gv
import geovista.theme


def fix(cube):
    import numpy as np

    data = cube.data
    wt = np.array([data[i] for i in range(10250, 10273 + 1)])
    et = np.array([data[i] for i in range(10344, 10367 + 1)])
    t = (wt + et) / 2

    wm = np.array([data[i] for i in range(23, 2279 + 48, 48)])
    em = np.array([data[i] for i in range(25, 2281 + 48, 48)])
    m = (wm + em) / 2

    wb = np.array([data[i] for i in range(12625, 12649 + 1)])
    eb = np.array([data[i] for i in range(12529, 12553 + 1)])
    b = (wb + eb) / 2

    r = np.array([i for i in range(10297, 10320 + 1)])
    data[r] = t

    r = np.array([i for i in range(24, 2280 + 48, 48)])
    data[r] = m

    r = np.array([i for i in range(12577, 12601 + 1)])
    data[r] = b

    return data


fname = "./qrparm_shared.orog.ugrid.node.nc"
with PARSE_UGRID_ON_LOAD.context():
    cube = iris.load_cube(fname, "surface_altitude")

face_node = cube.mesh.face_node_connectivity
indices = face_node.indices_by_location()
lons, lats = cube.mesh.node_coords

data = fix(cube)

mesh = gv.Transform.from_unstructured(
    lons.points,
    lats.points,
    indices,
    data=data,
    start_index=face_node.start_index,
    name=cube.name(),
)

plotter = gv.GeoPlotter()
plotter.add_coastlines(resolution="50m", color="white")
plotter.add_mesh(mesh, cmap="balance", show_edges=False)
plotter.add_axes()
plotter.add_text(
    "Unstructured Cube-Sphere Node Data (N, 4)",
    position="upper_left",
    font_size=10,
    shadow=True,
)
plotter.show()
