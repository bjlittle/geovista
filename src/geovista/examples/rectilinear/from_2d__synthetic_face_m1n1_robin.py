#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Synthetic Grid (Projected)
--------------------------

This example demonstrates how to render a projected rectilinear grid.

📋 Summary
^^^^^^^^^^

Creates a mesh from 2-D latitude and longitude rectilinear cell bounds.

The resulting mesh contains quad cells.

The data is synthetically generated and targets the mesh faces/cells.

Note that, Natural Earth coastlines are also rendered, and the mesh is transformed
to the Robinson pseudo-cylindrical projection.

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import numpy as np

import geovista as gv
import geovista.theme


def main() -> None:
    """Plot a projected synthetic rectilinear grid.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Create the 2-D spatial coordinates and data.
    M, N = 45, 90
    lats = np.linspace(-90, 90, M + 1)
    lons = np.linspace(-180, 180, N + 1)
    mlons, mlats = np.meshgrid(lons, lats, indexing="xy")
    clim = (0, 1)
    data = np.linspace(*clim, num=M * N)

    # Create the mesh from the synthetic data.
    mesh = gv.Transform.from_2d(mlons, mlats, data=data, name="Synthetic Cells")

    # Plot the rectilinear grid.
    crs = "+proj=robin"
    p = gv.GeoPlotter(crs=crs)
    p.add_mesh(mesh, clim=clim, cmap="tempo", show_edges=True)
    p.add_coastlines()
    p.add_axes()
    p.add_text(
        f"2-D Synthetic Face Data ({crs})",
        position="upper_left",
        font_size=10,
    )
    p.view_xy()
    p.camera.zoom(1.5)
    p.show()


if __name__ == "__main__":
    main()
