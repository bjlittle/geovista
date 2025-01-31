#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
"True" Winds on a Foreign Grid
------------------------------

This example demonstrates how to display "true" winds, when attached to data points
given in a non-standard coordinate system.

📋 Summary
^^^^^^^^^^

The example constructs some sample points on a polar stereographic grid, and assigns
synthetic vector values to them, representing wind data.  These data are presented as
"true" winds, i.e. northward and eastward components, so *not* related to the sample
grid.  This is a fairly typical real-world case.

In this case, the synthetic wind is a steady 4.0 ms-1 Eastward everywhere, so the
meaning is clearly seen.

We use the :meth:`geovista.bridge.Transform.from_points` method, passing the
winds to the ``vectors`` keyword, and specifying the different coordinate reference
systems of both the sample points (``crs``) and the vectors (``vectors_crs``).

Please refer to other code examples, e.g. `wind_arrows <./wind_arrows.html>`_ for more
details of the basic methods used.

"""  # noqa: D205,D212,D400

from __future__ import annotations

# Use cartopy as a source for specifying Coordinate Reference Systems
#  (which we can translate into PROJ via the .to_wkt() method)
import cartopy.crs as ccrs
import numpy as np

import geovista as gv


def main() -> None:
    """Demonstrate plotting vectors on different CRS from points."""
    # Create a mesh of individual points, adding vectors at each point.
    # NOTE: this creates a mesh with 'mesh vectors' : a specific concept in PyVista.

    # Create a CRS for "ordinary latitude-longitude"
    crs_latlon = ccrs.Geodetic().to_wkt()
    # Create a CRS for "polar stereographic"
    crs_polar = ccrs.NorthPolarStereo().to_wkt()
    # Create polar grid points
    xx = np.linspace(-5.0e6, 5.0e6, 20)
    yy = np.linspace(-4.0e6, 2.0e6, 20)
    xx, yy = np.meshgrid(xx, yy)
    # Make vector component arrays matching the XX and YY arrays
    xx, yy = xx.flatten(), yy.flatten()
    vx, vy = 4.0 * np.ones_like(xx), np.zeros_like(yy)

    # Create a mesh of location points with attached vector information
    mesh = gv.Transform.from_points(
        xx, yy, vectors=(vx, vy), crs=crs_polar, vectors_crs=crs_latlon
    )

    # Create a new mesh containing arrow glyphs, from the mesh vectors.
    arrows = mesh.glyph(factor=0.02)

    # Add the arrows to a Plotter with other aspects, and display
    p = gv.GeoPlotter()
    # Scale the base layer slightly to ensure it remains 'below' other elements.
    p.add_base_layer(radius=0.99)
    p.add_mesh(arrows, color="red")
    p.add_coastlines()
    p.add_graticule()
    p.add_axes()

    # Set up a nice default view
    selected_view = [
        (0.6037050543418041, -0.011033743353827528, 3.069575190259155),
        (0.0, 0.0, 0.0028896447726441954),
        (-0.9809865744261353, -0.019981215106321615, 0.19304427429621296),
    ]
    p.camera_position = selected_view
    p.show()


if __name__ == "__main__":
    main()
