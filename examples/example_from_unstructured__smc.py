import geovista as gv
from geovista.samples import ww3_global_smc
import geovista.theme

# load the sample data
sample = ww3_global_smc()

# create the mesh from the sample data
mesh = gv.Transform.from_unstructured(
    sample.lons, sample.lats, sample.connectivity, data=sample.data
)

plotter = gv.GeoPlotter()
sargs = dict(title=f"{sample.name} / {sample.units}")
plotter.add_mesh(mesh, cmap="balance", scalar_bar_args=sargs)
plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
resolution = "10m"
plotter.add_coastlines(resolution=resolution, color="white")
plotter.add_axes()
plotter.add_text(
    f"WW3 Spherical Multi-Cell ({resolution} Coastlines)",
    position="upper_left",
    font_size=10,
    shadow=True,
)
plotter.show()
