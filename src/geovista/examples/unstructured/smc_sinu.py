#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

import geovista as gv
from geovista.pantry import ww3_global_smc
import geovista.theme


def main() -> None:
    """Create a mesh from 2-D latitude and longitude unstructured cell bounds.

    The resulting mesh contains quad cells.

    It uses WAVEWATCH III (WW3) unstructured Spherical Multi-Cell (SMC) sea surface
    wave significant height data located on mesh faces/cells.

    Note that, a threshold is also applied to remove land ``NaN`` cells, and a
    Natural Earth base layer is rendered along with Natural Earth coastlines. The mesh
    is also transformed to the Sinusoidal (Sanson-Flamsteed) pseudo-cylindrical
    projection.

    """
    # load the sample data
    sample = ww3_global_smc()

    # create the mesh from the sample data
    mesh = gv.Transform.from_unstructured(sample.lons, sample.lats, data=sample.data)

    # provide mesh diagnostics via logging
    gv.logger.info("%s", mesh)

    # threshold the mesh of NaNs
    mesh = mesh.threshold()

    # plot the mesh
    crs = "+proj=sinu"
    plotter = gv.GeoPlotter(crs=crs)
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        f"WW3 Spherical Multi-Cell ({crs})",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.show()


if __name__ == "__main__":
    main()