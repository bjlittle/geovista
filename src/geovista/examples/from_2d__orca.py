#!/usr/bin/env python3
"""Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

import geovista as gv
from geovista.pantry import um_orca2
import geovista.theme  # noqa: F401


def main() -> None:
    """Create a mesh from 2-D latitude and longitude curvilinear cell bounds.

    The resulting mesh contains quad cells.

    It uses an ORCA2 global ocean with tri-polar model grid with sea water
    potential temperature data. The data targets the mesh faces/cells.

    Note that, a threshold is also applied to remove land NaN cells, and a
    Natural Earth base layer is rendered along with Natural Earth coastlines.

    """
    # load sample data
    sample = um_orca2()

    # create the mesh from the sample data
    mesh = gv.Transform.from_2d(sample.lons, sample.lats, data=sample.data)

    # provide mesh diagnostics via logging
    gv.logger.info("%s", mesh)

    # remove cells from the mesh with nan values
    mesh = mesh.threshold()

    # plot the mesh
    plotter = gv.GeoPlotter()
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, show_edges=True, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.natural_earth_1())
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        "ORCA (10m Coastlines)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.show()


if __name__ == "__main__":
    main()
