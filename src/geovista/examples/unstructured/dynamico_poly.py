#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
DYNAMICO Mesh (Projected)
-------------------------

This example demonstrates how to render a projected unstructured hexagon/pentagon mesh.

📋 Summary
^^^^^^^^^^

Creates a mesh from 2-D latitude and longitude unstructured cell bounds.

The resulting mesh contains hexagonal cells tessellated around 12 pentagon cells,
which are centered over the 12 vertices of a base icosahedron.

It uses surface air pressure data from the DYNAMICO project, a new dynamical core
for the Laboratoire de Météorologie Dynamique (LMD-Z), the atmospheric General
Circulation Model (GCM) part of Institut Pierre-Simon Laplace (IPSL-CM) Earth
System Model. The data targets the mesh faces/cells.

Note that, a graticule and Natural Earth coastlines are rendered, and the
mesh is also transformed to the Polyconic pseudo-conical projection.

.. tags:: Coastlines, Graticule, Projection, Unstructured

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import dynamico
import geovista.theme


def main() -> None:
    """Plot a projected DYNAMICO unstructured mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    sample = dynamico()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_unstructured(sample.lons, sample.lats, data=sample.data)

    # Plot the unstructured mesh.
    crs = "+proj=poly"
    plotter = gv.GeoPlotter(crs=crs)
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_coastlines()
    plotter.add_graticule()
    plotter.add_axes()
    plotter.add_text(
        f"DYNAMICO Icosahedral ({crs})",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.camera.zoom(1.2)
    plotter.show()


if __name__ == "__main__":
    main()
