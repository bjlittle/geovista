import netCDF4 as nc

import geovista as gv
import geovista.theme

# load the netcdf dataset
fname = "./tamar_v2_2tsteps.nc"
ds = nc.Dataset(fname)

# cherry-pick the topology, connectivity and data
lons = ds.variables["lon"][:]
lats = ds.variables["lat"][:]
connectivity = ds.variables["nv"][:] - 1
elements = ds.variables["h_center"][:]
nodes = ds.variables["h"][:]

# create the mesh and warp it
mesh = gv.Transform.from_unstructured(
    lons, lats, connectivity.T, data=elements, name="elements"
)
mesh.point_data["nodes"] = nodes
mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
mesh.warp_by_scalar(scalars="nodes", inplace=True, factor=2e-5)

# plot the mesh
plotter = gv.GeoPlotter()
sargs = dict(title="Bathymetry / m")
plotter.add_mesh(mesh, cmap="balance", show_edges=True, scalar_bar_args=sargs)
plotter.add_axes()
plotter.show()
