import iris
import pyvista as pv

from geovista.bridge import Transform
from geovista.geometry import get_coastlines


# see https://fesom.de/cmip6/work-with-awi-cm-unstructured-data/
# https://swift.dkrz.de/v1/dkrz_0262ea1f00e34439850f3f1d71817205/FESOM/tos_Omon_AWI-ESM-1-1-LR_historical_r1i1p1f1_gn_185001-185012.nc
fname = "./tos_Omon_AWI-ESM-1-1-LR_historical_r1i1p1f1_gn_185001-185012.nc"
cube = iris.load_cube(fname, "tos")[0]

lons = cube.coord("longitude").bounds
lats = cube.coord("latitude").bounds

mesh = Transform.from_unstructured(lons, lats, lons.shape, data=cube.data)
coastlines = get_coastlines("10m")
base = pv.Sphere(radius=1 - (1e-3), theta_resolution=360, phi_resolution=180)

plotter = pv.Plotter()

sargs = dict(title=f"{cube.name()} / {cube.units}")
plotter.add_mesh(base, color="grey")
plotter.add_mesh(
    mesh, cmap="balance", show_edges=True, scalar_bar_args=sargs, edge_color="grey"
)
plotter.add_mesh(coastlines, color="white", line_width=2)

plotter.add_axes()
plotter.show()
