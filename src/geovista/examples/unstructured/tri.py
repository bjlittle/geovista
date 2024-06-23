#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
WW3 Triangular Mesh
-------------------

This example demonstrates how to render an unstructured triangular mesh.

📋 Summary
^^^^^^^^^^

Creates a mesh from 1-D latitude and longitude unstructured points and connectivity.

The resulting mesh contains triangular cells. The connectivity is required to
construct the cells by indexing into the unstructured points.

WAVEWATCH III (WW3) sea surface wave significant height data is located on
mesh nodes/points, which are then interpolated across the mesh faces/cells.

Finally, a Natural Earth base layer is rendered along with Natural Earth
coastlines.

.. tags:: Coastlines, Globe, Unstructured, Texture

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import ww3_global_tri
import geovista.theme


def main() -> None:
    """Plot a WW3 unstructured triangular mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    sample = ww3_global_tri()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_unstructured(
        sample.lons, sample.lats, connectivity=sample.connectivity, data=sample.data
    )

    # Plot the unstructured mesh.
    plotter = gv.GeoPlotter()
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.view_xy(negative=True)
    plotter.add_text(
        "WW3 Triangular Mesh (10m Coastlines)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.camera.zoom(1.3)
    plotter.show()


if __name__ == "__main__":
    main()
