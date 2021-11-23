#
# python -i example_from_unstructured__fesom_timeseries.py
#

import iris
from iris.experimental.ugrid import PARSE_UGRID_ON_LOAD

import geovista as gv


def callback() -> None:
    global cube
    global mesh
    global idx
    global time
    global actor

    idx = (idx + 1) % cube.shape[0]
    name = mesh.active_scalars_name
    mesh[name] = cube[idx].data
    text = time.units.num2date(time.points[idx]).strftime("%Y-%m-%d")
    actor.SetText(3, text)


fname = "./tos_Omon_AWI-ESM-1-1-LR_historical_r1i1p1f1_gn_185001-185012.nc"
with PARSE_UGRID_ON_LOAD.context():
    cube = iris.load_cube(fname, "tos")

lons = cube.coord("longitude").bounds
lats = cube.coord("latitude").bounds
time = cube.coord("time")

idx = 0

mesh = gv.Transform.from_unstructured(
    lons,
    lats,
    lons.shape,
    data=cube.data[idx],
    name=cube.name(),
)

plotter = gv.GeoBackgroundPlotter()
sargs = dict(title=f"{cube.name()} / {cube.units}")
plotter.add_mesh(
    mesh, cmap="balance", show_edges=False, scalar_bar_args=sargs, clim=(-2, 33)
)
plotter.add_base_layer(color="grey", show_scalar_bar=False)
plotter.add_coastlines(resolution="10m", color="white")
plotter.add_axes()
text = time.units.num2date(time.points[idx]).strftime("%Y-%m-%d")
actor = plotter.add_text(text, position="upper_right", font_size=10, shadow=True)
plotter.add_text(
    "AWI-ESM CMIP6 FESOM", position="upper_left", font_size=10, shadow=True
)
plotter.add_callback(callback, interval=250)
