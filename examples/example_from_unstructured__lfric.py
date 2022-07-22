import geovista as gv
from geovista.pantry import lfric_sst
import geovista.theme

sample = lfric_sst()

mesh = gv.Transform.from_unstructured(
    sample.lons,
    sample.lats,
    sample.connectivity,
    data=sample.data,
    start_index=sample.start_index,
)

mesh = mesh.threshold()

plotter = gv.GeoPlotter()
sargs = dict(title=f"{sample.name} / {sample.units}")
plotter.add_mesh(
    mesh, cmap="balance", show_edges=True, edge_color="grey", scalar_bar_args=sargs
)
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
