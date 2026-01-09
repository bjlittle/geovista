#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
ORCA2 Grid (Projected)
----------------------

This example demonstrates how to render a projected extruded curvilinear grid.

📋 Summary
^^^^^^^^^^

Creates a mesh from 2D latitude and longitude curvilinear cell bounds.

The resulting mesh contains quad cells.

It uses an ORCA2 global ocean with tri-polar model grid with sea water
potential temperature data. The data targets the mesh faces/cells.

Note that a threshold is applied to remove land ``NaN`` cells, before the
mesh is then transformed to the Mollweide pseudo-cylindrical projection
and extruded to give depth to the projected surface. Finally, 10m
resolution Natural Earth coastlines are also rendered.

.. tags::

    component: coastlines, component: texture,
    domain: oceanography,
    filter: cast, filter: extrude, filter: threshold,
    load: curvilinear,
    projection: crs, projection: transform

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.common import cast_UnstructuredGrid_to_PolyData as cast
from geovista.pantry.data import nemo_orca2
import geovista.theme
from geovista.transform import transform_mesh


def main() -> None:
    """Plot a projected ORCA2 curvilinear grid.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    sample = nemo_orca2()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_2d(
        sample.lons,
        sample.lats,
        data=sample.data,
        name=f"{sample.name} / {sample.units}",
    )

    # Remove cells from the mesh with NaN values.
    mesh = cast(mesh.threshold())

    # Transform the mesh to the Mollweide projection and extrude.
    mesh = transform_mesh(mesh, crs := "esri:54009")
    mesh.extrude((0, 0, -1000000), capping=True, inplace=True)

    # Plot the curvilinear mesh.
    p = gv.GeoPlotter(crs=crs)
    p.add_mesh(mesh)
    p.add_coastlines(color="black")
    p.add_axes()
    p.add_text(
        f"ORCA ({crs}, extrude)",
        position="upper_left",
        font_size=10,
    )
    p.view_xy()
    p.camera.zoom(1.5)
    p.show()


if __name__ == "__main__":
    main()
