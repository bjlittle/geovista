import iris
import pyvista as pv

import geovista as gv

# https://github.com/SciTools/iris-test-data/blob/master/test_data/NetCDF/ORCA2/votemper.nc
fname = "./votemper.nc"
cube = iris.load_cube(fname, "sea_water_potential_temperature")[0, 0]

lons = cube.coord("longitude").bounds
lats = cube.coord("latitude").bounds

mesh = gv.Transform.from_2d(lons, lats, data=cube.data, name=cube.name())
coastlines = gv.get_coastlines("10m")
base = pv.Sphere(radius=1 - (1e-3), theta_resolution=360, phi_resolution=180)

plotter = pv.Plotter()
sargs = dict(title=f"{cube.name()} / {cube.units}")
plotter.add_mesh(base, color="grey")
plotter.add_mesh(mesh, cmap="balance", show_edges=True, scalar_bar_args=sargs)
plotter.add_mesh(coastlines, color="white")
plotter.add_axes()
plotter.show()
