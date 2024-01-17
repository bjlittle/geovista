#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
LFRic LAM Mesh (Projected)
--------------------------

This example demonstrates how to render a projected unstructured quadrilateral mesh.

📋 Summary
^^^^^^^^^^

Creates a mesh from 1-D latitude and longitude unstructured cell points.

The resulting mesh contains quad cells and is constructed from CF UGRID unstructured
cell points and connectivity.

It uses a high-resolution Local Area Model (LAM) mesh of air potential
temperature data located on the mesh faces/cells.

Note that, a Natural Earth base layer is rendered along with Natural Earth
coastlines, and the mesh is transformed to the Mollweide pseudo-cylindrical
projection.

----

"""  # noqa: D205,D212,D400
from __future__ import annotations

import geovista as gv
from geovista.assets.pantry import lam_pacific
import geovista.theme


def main() -> None:
    """Plot a projected LFRic LAM unstructured mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    sample = lam_pacific()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
    )
    # sphinx_gallery_start_ignore
    # Provide mesh diagnostics via logging.
    gv.logger.info("%s", mesh)
    # sphinx_gallery_end_ignore

    # Plot the unstructured mesh.
    crs = "+proj=moll"
    plotter = gv.GeoPlotter(crs=crs)
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        f"CF UGRID LAM ({crs})",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.camera.zoom(1.5)
    plotter.show()


if __name__ == "__main__":
    main()
