import netCDF4 as nc

import geovista as gv
import geovista.theme

# load the netcdf file
fname = "./ww3.201809_hs.nc"
ds = nc.Dataset(fname)

# load the lon/lat points
lons = ds.variables["longitude"][:]
lats = ds.variables["latitude"][:]

# load the connectivity
offset = 1  # minimum connectivity index offset
connectivity = ds.variables["tri"][:] - offset

# load some mesh payload
data = ds.variables["hs"]
name = data.standard_name
units = data.units

# we know this is a timeseries, a priori
idx = 0

mesh = gv.Transform.from_unstructured(lons, lats, connectivity, data=data[idx])

plotter = gv.GeoPlotter()
sargs = dict(title=f"{name} / {units}")
plotter.add_mesh(
    mesh, cmap="balance", show_edges=True, scalar_bar_args=sargs, edge_color="grey"
)
plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
resolution = "10m"
plotter.add_coastlines(resolution=resolution, color="white")
plotter.add_axes()
plotter.view_xy(negative=True)
plotter.camera.position = (
    7.048545779114734e-05,
    -0.00020368315852914431,
    -4.082199423859821,
)
plotter.show()
