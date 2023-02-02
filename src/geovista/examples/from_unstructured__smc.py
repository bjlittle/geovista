#!/usr/bin/env python3
"""
Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.1.0

"""

import geovista as gv
from geovista.pantry import ww3_global_smc
import geovista.theme  # noqa: F401


def main() -> None:
    """
    This example demonstrates how to create a mesh from 2-D latitude and longitude
    unstructured cell bounds. The resulting mesh contains quad cells.

    It uses WAVEWATCH III (WW3) unstructured Spherical Multi-Cell (SMC) sea surface
    wave significant height data located on mesh faces/cells.

    Note that, a threshold is also applied to remove land NaN cells, and a
    Natural Earth base layer is rendered along with Natural Earth coastlines.

    """
    # load the sample data
    sample = ww3_global_smc()

    # create the mesh from the sample data
    mesh = gv.Transform.from_unstructured(sample.lons, sample.lats, data=sample.data)

    # provide mesh diagnostics via logging
    gv.logger.info("%s", mesh)

    # threshold the mesh of NaNs
    mesh = mesh.threshold()

    # plot the mesh
    plotter = gv.GeoPlotter()
    sargs = dict(title=f"{sample.name} / {sample.units}", shadow=True)
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        "WW3 Spherical Multi-Cell (10m Coastlines)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.show()


if __name__ == "__main__":
    main()
