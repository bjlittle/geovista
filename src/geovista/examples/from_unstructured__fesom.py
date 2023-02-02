#!/usr/bin/env python3
"""
Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.1.0

"""

import geovista as gv
from geovista.pantry import fesom
import geovista.theme  # noqa: F401


def main() -> None:
    """
    This example demonstrates how to create a mesh from 2-D latitude and longitude
    unstructured cell bounds. The resulting mesh is formed from masked connectivity,
    allowing the mesh to contain mixed cell geometries up to 18-sides (octadecagon).

    It uses a AWI Climate Model (AWI-CI) Finite Element Sea ice-Ocean Model (FESOM)
    v1.4 unstructured mesh of surface sea temperature data. The data targets the
    mesh faces/cells.

    Note that, a Natural Earth base layer is rendered along with Natural Earth coastlines.

    """
    # load the sample data
    sample = fesom()

    # create the mesh from the sample data
    mesh = gv.Transform.from_unstructured(
        sample.lons, sample.lats, connectivity=sample.connectivity, data=sample.data
    )

    # provide mesh diagnostics via logging
    gv.logger.info("%s", mesh)

    # plot the mesh
    plotter = gv.GeoPlotter()
    sargs = dict(title=f"{sample.name} / {sample.units}", shadow=True)
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        "AWI-CM FESOM v1.4 (10m Coastlines)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.show()


if __name__ == "__main__":
    main()
