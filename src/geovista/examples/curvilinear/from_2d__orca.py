#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
ORCA2 Grid
----------

This example demonstrates how to render a curvilinear grid.

📋 Summary
^^^^^^^^^^

Creates a mesh from 2-D latitude and longitude curvilinear cell bounds.

The resulting mesh contains quad cells.

It uses an ORCA2 global ocean with tri-polar model grid with sea water
potential temperature data. The data targets the mesh faces/cells.

Note that, a threshold is also applied to remove land ``NaN`` cells, and a
Natural Earth base layer is rendered along with Natural Earth coastlines.

.. tags:: Coastlines, Curvilinear, Globe, Texture, Threshold

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import nemo_orca2
import geovista.theme


def main() -> None:
    """Plot an ORCA2 curvilinear grid.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    sample = nemo_orca2()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_2d(sample.lons, sample.lats, data=sample.data)

    # Remove cells from the mesh with NaN values.
    mesh = mesh.threshold()

    # Plot the curvilinear grid.
    plotter = gv.GeoPlotter()
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.natural_earth_1())
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        "ORCA (10m Coastlines)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.camera.zoom(1.3)
    plotter.show()


if __name__ == "__main__":
    main()
