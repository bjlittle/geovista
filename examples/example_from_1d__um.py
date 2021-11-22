import iris

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

plotter = gv.GeoPlotter()
sargs = dict(title=f"{cube.name()} / {cube.units}")
plotter.add_mesh(mesh, cmap="balance", show_edges=True, scalar_bar_args=sargs)
plotter.add_coastlines(resolution="10m", color="white")
plotter.add_axes()
plotter.add_text(
    "1-D UM Face Data (M, 2) (N, 2)", position="upper_left", font_size=10, shadow=True
)
plotter.show()
