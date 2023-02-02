#!/usr/bin/env python3
"""
Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.1.0

"""

import geovista as gv
from geovista.pantry import oisst_avhrr_sst
import geovista.theme  # noqa: F401


def main() -> None:
    """
    This example demonstrates how to create a mesh from 1-D latitude and longitude
    rectilinear cell bounds. The resulting mesh contains quad cells.

    It uses NOAA/NECI 1/4° Daily Optimum Interpolation Sea Surface Temperature
    (OISST) v2.1 Advanced Very High Resolution Radiometer (AVHRR) gridded data
    (https://doi.org/10.25921/RE9P-PT57). The data targets the mesh faces/cells.

    Note that, a threshold is also applied to remove land NaN cells, and a
    NASA Blue Marble base layer is rendered along with Natural Earth coastlines.

    """
    # load sample data
    sample = oisst_avhrr_sst()

    # create the mesh from the sample data
    mesh = gv.Transform.from_1d(sample.lons, sample.lats, data=sample.data)

    # provide mesh diagnostics via logging
    gv.logger.info("%s", mesh)

    # remove cells from the mesh with nan values
    mesh = mesh.threshold()

    # plot the mesh
    plotter = gv.GeoPlotter()
    sargs = dict(title=f"{sample.name} / {sample.units}", shadow=True)
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.blue_marble())
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        "NOAA/NCEI OISST AVHRR (10m Coastlines)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.show()


if __name__ == "__main__":
    main()
