import iris
import pyvista as pv

from geovista.bridge import Transform
from geovista.geometry import get_coastlines

# https://github.com/SciTools/iris-test-data/blob/master/test_data/NetCDF/volcello/volcello_Ofx_CESM2_deforest-globe_r1i1p1f1_gn.nc
fname = "./volcello_Ofx_CESM2_deforest-globe_r1i1p1f1_gn.nc"
cube = iris.load_cube(fname, "ocean_volume")[0]

lons = cube.coord("longitude").bounds
lats = cube.coord("latitude").bounds

mesh = Transform.from_2d(lons, lats, data=cube.data, name=cube.name())
coastlines = get_coastlines("10m")

plotter = pv.Plotter()
sargs = dict(title=f"{cube.name()} / {cube.units}")
plotter.add_mesh(mesh, cmap="balance", show_edges=False, scalar_bar_args=sargs)
plotter.add_mesh(coastlines, color="white")
plotter.add_axes()
plotter.show()
