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

Creates a mesh from 2-D latitude and longitude curvilinear cell bounds.

The resulting mesh contains quad cells.

It uses an ORCA2 global ocean with tri-polar model grid with sea water
potential temperature data. The data targets the mesh faces/cells.

Note that, a threshold is applied to remove land ``NaN`` cells, before the
mesh is then transformed to the Mollweide pseudo-cylindrical projection
and extruded to give depth to the projected surface. Finally, 10m
resolution Natural Earth coastlines are also rendered.

"""  # noqa: D205,D212,D400
from __future__ import annotations

from pyproj import CRS

import geovista as gv
from geovista.common import cast_UnstructuredGrid_to_PolyData as cast
from geovista.pantry import um_orca2
import geovista.theme
from geovista.transform import transform_mesh


def main() -> None:
    """Plot a projected ORCA2 curvilinear grid.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    sample = um_orca2()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_2d(sample.lons, sample.lats, data=sample.data)
    # sphinx_gallery_start_ignore
    # Provide mesh diagnostics via logging.
    gv.logger.info("%s", mesh)
    # sphinx_gallery_end_ignore

    # create the target coordinate reference system
    crs = CRS.from_user_input(projection := "+proj=moll")

    # Remove cells from the mesh with NaN values.
    mesh = cast(mesh.threshold())

    # Transform and extrude the mesh.
    mesh = transform_mesh(mesh, crs)
    mesh.extrude((0, 0, -1000000), capping=True, inplace=True)

    # Plot the curvilinear mesh.
    plotter = gv.GeoPlotter(crs=crs)
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_coastlines(color="black")
    plotter.add_axes()
    plotter.add_text(
        f"ORCA ({projection} extrude)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.show()


if __name__ == "__main__":
    main()
