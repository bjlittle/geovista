#!/usr/bin/env python3

import matplotlib.pyplot as plt

import geovista as gv
from geovista.pantry import icon_soil
import geovista.theme  # noqa: F401


def main() -> None:
    # load the sample data
    sample = icon_soil()

    # create the mesh from the sample data
    mesh = gv.Transform.from_unstructured(sample.lons, sample.lats, data=sample.data)

    # plot the mesh
    plotter = gv.GeoPlotter()
    sargs = dict(title=f"{sample.name} / {sample.units}", shadow=True)
    cmap = plt.cm.get_cmap("cet_CET_L17", lut=9)
    plotter.add_mesh(mesh, cmap=cmap, show_edges=True, scalar_bar_args=sargs)
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        "ICON Global 160km Resolution (10m Coastlines)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_yz()
    plotter.show()


if __name__ == "__main__":
    main()
