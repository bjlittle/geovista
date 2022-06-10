import iris

import geovista as gv
import geovista.theme

# https://github.com/SciTools/iris-test-data/blob/master/test_data/NetCDF/volcello/volcello_Ofx_CESM2_deforest-globe_r1i1p1f1_gn.nc
fname = "./volcello_Ofx_CESM2_deforest-globe_r1i1p1f1_gn.nc"
cube = iris.load_cube(fname, "ocean_volume")[0]

lons = cube.coord("longitude").bounds
lats = cube.coord("latitude").bounds

mesh = gv.Transform.from_2d(lons, lats, data=cube.data, name=cube.name())

plotter = gv.GeoPlotter()
sargs = dict(title=f"{cube.name()} / {cube.units}")
plotter.add_mesh(mesh, cmap="balance", show_edges=True, scalar_bar_args=sargs)
plotter.add_base_layer(color="grey")
plotter.add_coastlines(resolution="10m", color="white")
plotter.add_axes()
plotter.add_text(
    "2-D Volcello Face Data (M, N, 4)", position="upper_left", font_size=10, shadow=True
)
plotter.show()
