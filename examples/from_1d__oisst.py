#!/usr/bin/env python3

import geovista as gv
from geovista.pantry import oisst_avhrr_sst
import geovista.theme  # noqa: F401


def main() -> None:
    # load sample data
    sample = oisst_avhrr_sst()

    # create the mesh from the sample data
    mesh = gv.Transform.from_1d(sample.lons, sample.lats, data=sample.data)

    # remove cells from the mesh with nan values
    mesh = mesh.threshold()

    # plot the mesh
    plotter = gv.GeoPlotter()
    sargs = dict(title=f"{sample.name} / {sample.units}", shadow=True)
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.blue_marble())
    resolution = "10m"
    plotter.add_coastlines(resolution=resolution, color="white")
    plotter.add_axes()
    plotter.add_text(
        f"NOAA/NCEI OISST AVHRR ({resolution} Coastlines)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.show()


if __name__ == "__main__":
    main()
