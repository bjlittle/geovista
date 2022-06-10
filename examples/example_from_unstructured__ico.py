import netCDF4

import geovista as gv
import geovista.theme

# ds = netCDF4.Dataset("https://vesg.ipsl.upmc.fr/thredds/dodsC/IPSLFS/brocksce/gridsCF/phis.nc")
ds = netCDF4.Dataset("icosahedral.nc")

lons = ds.variables["bounds_lon_i"][:]
lats = ds.variables["bounds_lat_i"][:]
data = ds.variables["phis"][:]

mesh = gv.Transform.from_unstructured(lons, lats, lons.shape, data=data)

plotter = gv.GeoPlotter()
plotter.add_mesh(mesh, cmap="balance", show_edges=True)
plotter.add_coastlines(resolution="10m", color="white")
plotter.add_axes()
plotter.show()
