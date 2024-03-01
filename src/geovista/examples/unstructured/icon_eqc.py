#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
ICON Mesh (Projected)
---------------------

This example demonstrates how to render a projected unstructured triangular mesh.

📋 Summary
^^^^^^^^^^

Creates a mesh from 2-D latitude and longitude unstructured cell bounds.

The resulting mesh contains triangular cells.

It uses Icosahedral Nonhydrostatic Weather and Climate Model (ICON) global 160km
resolution soil type data, as developed by the Deutscher Wetterdienst (DWD) and
the Max-Planck-Institut für Meteorologie (MPI-M). The data targets the mesh
faces/cells.

Note that, Natural Earth coastlines are also rendered, and the mesh is transformed
to the Equidistant Cylindrical (Plate Carrée) conformal cylindrical projection.

.. tags:: Coastlines, Projection, Unstructured

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import matplotlib as mpl

import geovista as gv
from geovista.pantry.data import icon_soil
import geovista.theme


def main() -> None:
    """Plot a projected ICON unstructured mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    sample = icon_soil()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_unstructured(sample.lons, sample.lats, data=sample.data)

    # Plot the unstructured mesh.
    crs = "+proj=eqc"
    plotter = gv.GeoPlotter(crs=crs)
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    cmap = mpl.colormaps.get_cmap("cet_CET_L17").resampled(lutsize=9)
    plotter.add_mesh(mesh, cmap=cmap, scalar_bar_args=sargs)
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        f"ICON 160km Resolution Triangular Mesh ({crs})",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.camera.zoom(1.5)
    plotter.show()


if __name__ == "__main__":
    main()
