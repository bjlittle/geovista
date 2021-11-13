import iris

import geovista as gv

# see https://fesom.de/cmip6/work-with-awi-cm-unstructured-data/
# https://swift.dkrz.de/v1/dkrz_0262ea1f00e34439850f3f1d71817205/FESOM/tos_Omon_AWI-ESM-1-1-LR_historical_r1i1p1f1_gn_185001-185012.nc
fname = "./tos_Omon_AWI-ESM-1-1-LR_historical_r1i1p1f1_gn_185001-185012.nc"
cube = iris.load_cube(fname, "tos")[0]

lons = cube.coord("longitude").bounds
lats = cube.coord("latitude").bounds

mesh = gv.Transform.from_unstructured(
    lons, lats, lons.shape, data=cube.data, name=cube.name()
)

plotter = gv.GeoPlotter()
sargs = dict(title=f"{cube.name()} / {cube.units}")
plotter.add_mesh(
    mesh, cmap="balance", show_edges=False, scalar_bar_args=sargs, edge_color="grey"
)
plotter.add_base_layer(color="grey")
plotter.add_coastlines(resolution="50m", color="white", line_width=2)
plotter.add_axes()
plotter.add_text(
    "Unstructured FESOM Face Data (N, 18)",
    position="upper_left",
    font_size=10,
    shadow=True,
)
plotter.show()
