#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Spherical Multi-Cell Mesh (Projected)
-------------------------------------

This example demonstrates how to render a projected unstructured quadrilateral mesh.

📋 Summary
^^^^^^^^^^

Creates a mesh from 2-D latitude and longitude unstructured cell bounds.

The resulting mesh contains quad cells.

It uses WAVEWATCH III (WW3) unstructured Spherical Multi-Cell (SMC) sea surface
wave significant height data located on mesh faces/cells.

Note that, a threshold is also applied to remove land ``NaN`` cells, and a
Natural Earth base layer is rendered along with Natural Earth coastlines. The mesh
is also transformed to the Sinusoidal (Sanson-Flamsteed) pseudo-cylindrical
projection.

.. tags::

    component: coastlines, component: texture,
    domain: oceanography,
    load: unstructured,
    filter: threshold,
    projection: crs

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import ww3_global_smc
import geovista.theme


def main() -> None:
    """Plot a projected SMC unstructured mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    sample = ww3_global_smc()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_unstructured(sample.lons, sample.lats, data=sample.data)

    # Threshold the mesh of NaNs.
    mesh = mesh.threshold()

    # Plot the unstructured mesh.
    crs = "+proj=sinu"
    p = gv.GeoPlotter(crs=crs)
    sargs = {
        "title": f"{sample.name} / {sample.units}",
        "outline": True,
        "background_color": "white",
        "fill": True,
    }
    p.add_mesh(mesh, scalar_bar_args=sargs)
    p.add_base_layer(texture=gv.natural_earth_hypsometric())
    p.add_coastlines()
    p.add_axes()
    p.add_text(
        f"WW3 Spherical Multi-Cell ({crs})",
        position="upper_left",
        font_size=10,
    )
    p.view_xy()
    p.camera.zoom(1.5)
    p.show()


if __name__ == "__main__":
    main()
