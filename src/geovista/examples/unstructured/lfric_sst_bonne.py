#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
LFRic Mesh (Projected)
----------------------

This example demonstrates how to render a projected unstructured quadrilateral mesh.

📋 Summary
^^^^^^^^^^

Creates a mesh from 1-D latitude and longitude unstructured points and connectivity.

The resulting mesh contains quad cells. The connectivity is required to construct
the cells by indexing into the CF UGRID unstructured points.

It uses an unstructured Met Office LFRic C48 cubed-sphere of surface temperature
data located on the mesh faces/cells.

Note that, a threshold is also applied to remove land ``NaN`` cells. A Natural Earth
base layer is also rendered along with Natural Earth coastlines and a graticule.
The mesh is also transformed to the Bonne projection.

.. tags:: Coastlines, Graticule, Projection, Unstructured, Texture, Threshold

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import lfric_sst
import geovista.theme


def main() -> None:
    """Plot a projected LFRic unstructured mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    sample = lfric_sst()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
    )

    # Remove cells from the mesh with NaN values.
    mesh = mesh.threshold()

    # Plot the unstructured mesh.
    crs = "+proj=bonne +lat_1=10 +lon_0=180"
    plotter = gv.GeoPlotter(crs=crs)
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.natural_earth_1())
    plotter.add_coastlines()
    plotter.add_graticule()
    plotter.add_axes()
    plotter.add_text(
        f"LFRic C48 Unstructured Cube-Sphere ({crs})",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.camera.zoom(1.5)
    plotter.show()


if __name__ == "__main__":
    main()
