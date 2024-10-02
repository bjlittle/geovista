#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
OISST AVHRR Grid
----------------

This example demonstrates how to render a rectilinear grid.

📋 Summary
^^^^^^^^^^

Creates a mesh from 1-D latitude and longitude rectilinear cell bounds.

The resulting mesh contains quad cells.

The example uses NOAA/NECI 1/4° Daily Optimum Interpolation Sea Surface Temperature
(OISST) v2.1 Advanced Very High Resolution Radiometer (AVHRR) gridded data.
The data targets the mesh faces/cells.

Note that, a threshold is also applied to remove land ``NaN`` cells, and a
NASA Blue Marble base layer is rendered along with Natural Earth coastlines.

.. tags:: Coastlines, Globe, Rectilinear, Texture, Threshold

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import oisst_avhrr_sst
import geovista.theme


def main() -> None:
    """Plot an OISST AVHRR rectilinear grid.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    sample = oisst_avhrr_sst()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_1d(sample.lons, sample.lats, data=sample.data)

    # Remove cells from the mesh with NaN values.
    mesh = mesh.threshold()

    # Plot the rectilinear grid.
    plotter = gv.GeoPlotter()
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.blue_marble())
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        "NOAA/NCEI OISST AVHRR (10m Coastlines)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.camera.zoom(1.3)
    plotter.show()


if __name__ == "__main__":
    main()
