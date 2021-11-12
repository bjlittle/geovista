import iris
import pyvista as pv

import geovista as gv

fname = iris.sample_data_path("air_temp.pp")
cube = iris.load_cube(fname)

lons = cube.coord("longitude")
lats = cube.coord("latitude")

if not lons.has_bounds():
    lons.guess_bounds()

if not lats.has_bounds():
    lats.guess_bounds()

mesh = gv.Transform.from_1d(lons.bounds, lats.bounds, data=cube.data, name=cube.name())
coastlines = gv.get_coastlines("10m")

plotter = pv.Plotter()

sargs = dict(title=f"{cube.name()} / {cube.units}")
plotter.add_mesh(mesh, cmap="balance", show_edges=True, scalar_bar_args=sargs)
plotter.add_mesh(coastlines, color="white")

plotter.add_axes()
plotter.show()
