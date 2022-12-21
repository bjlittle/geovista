#!/usr/bin/env python3

import geovista as gv
from geovista.pantry import ww3_global_tri
import geovista.theme  # noqa: F401


def main() -> None:
    # load the sample data
    sample = ww3_global_tri()

    # create the mesh from the sample data
    mesh = gv.Transform.from_unstructured(
        sample.lons, sample.lats, connectivity=sample.connectivity, data=sample.data
    )

    # plot the mesh
    plotter = gv.GeoPlotter()
    sargs = dict(title=f"{sample.name} / {sample.units}")
    plotter.add_mesh(mesh, show_edges=True, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
    resolution = "10m"
    plotter.add_coastlines(resolution=resolution, color="white")
    plotter.add_axes()
    plotter.view_xy(negative=True)
    plotter.add_text(
        f"WW3 Triangular Mesh ({resolution} Coastlines)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.show()


if __name__ == "__main__":
    main()
