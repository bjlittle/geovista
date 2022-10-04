import geovista as gv
from geovista.pantry import lfric_sst
import geovista.theme

# load the sample data
sample = lfric_sst()

# create the mesh from the sample data
mesh = gv.Transform.from_unstructured(
    sample.lons,
    sample.lats,
    sample.connectivity,
    data=sample.data,
    start_index=sample.start_index,
)

# remove cells from the mesh with nan values
mesh = mesh.threshold()

# plot the mesh
plotter = gv.GeoPlotter()
sargs = dict(title=f"{sample.name} / {sample.units}")
plotter.add_mesh(mesh, show_edges=True, scalar_bar_args=sargs)
plotter.add_base_layer(texture=gv.natural_earth_1())
resolution = "10m"
plotter.add_coastlines(resolution=resolution, color="white")
plotter.add_axes()
plotter.add_text(
    f"LFric Unstructured Cube-Sphere ({resolution} Coastlines)",
    position="upper_left",
    font_size=10,
    shadow=True,
)
plotter.show()
