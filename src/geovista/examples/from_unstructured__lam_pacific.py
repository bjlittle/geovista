#!/usr/bin/env python3
"""Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

import geovista as gv
from geovista.pantry import lam_pacific
import geovista.theme  # noqa: F401


def main() -> None:
    """Create a mesh from 1-D latitude and longitude unstructured cell points.

    The resulting mesh contains quad cells and is constructed from CF UGRID unstructured
    cell points and connectivity.

    It uses a high-resolution Local Area Model (LAM) mesh of air potential
    temperature data located on the mesh faces/cells.

    Note that, a Natural Earth base layer is rendered along with Natural Earth
    coastlines.

    """
    # load the sample data
    sample = lam_pacific()

    # create the mesh from the sample data
    mesh = gv.Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
    )

    # provide mesh diagnostics via logging
    gv.logger.info("%s", mesh)

    # plot the mesh
    plotter = gv.GeoPlotter()
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.view_yz(negative=True)
    plotter.add_text(
        "CF UGRID LAM (10m Coastlines)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.show()


if __name__ == "__main__":
    main()
