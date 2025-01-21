#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
3D Wind Arrows
--------------

This example demonstrates how to display wind vector data.

📋 Summary
^^^^^^^^^^

The data source provides X and Y arrays containing plain longitude and
latitude values, which is the most common case.

The wind information is provided in three separate field arrays, 'U, V and W',
i.e. eastward, northward and vertical components.

These values are coded for each location (X, Y), measured relative to the longitude,
latitude and vertical directions at each point.

There is no connectivity provided, so each location has a vector and is independent of
the others.  Hence we use the ``geovista.Transform.from_points`` function, passing the
winds to the ``vectors`` keyword.

Initially, we can just show the horizontal winds, as this easier to interpret.
"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import lfric_winds

# get sample data
sample = lfric_winds()

# Create a mesh of individual points, adding vectors at each point.
# NOTE: this creates a mesh with 'mesh vectors' : a specific concept in PyVista.
mesh = gv.Transform.from_points(
    sample.lons,
    sample.lats,
    vectors=(sample.u, sample.v),
)

# Create a new mesh containing arrow glyphs, from the mesh vectors.
# NOTE: use an overall scaling factor to make the arrows a reasonable size.
arrows = mesh.glyph(factor=0.02)

# Add the arrows to a plotter with other aspects, and display
plotter = gv.GeoPlotter()
plotter.add_base_layer(radius=0.99)
plotter.add_mesh(arrows, cmap="inferno")
plotter.add_coastlines()
plotter.add_graticule()
plotter.add_axes()

# Set up a nice default view
plotter.camera.zoom(1.3)  # adjusts the camera view angle
selected_view = [
    (-4.0688208659033505, -2.5462610064466777, -2.859304866708606),
    (-0.0037798285484313965, 0.005168497562408447, -0.0031679868698120117),
    (-0.523382090763761, -0.11174892277533728, 0.8447386372874786),
]
plotter.camera_position = selected_view
plotter.show()


# %%
# Repeat, but now add in the 'W' vertical components.
# To be visible, these need scaling up, since vertical wind values are typically much
# smaller than horizontal.
# We also apply a vertical offset ("radius"), to prevent downward-going arrows from
# disappearing into the surface.

# Create a mesh of individual points, adding vectors at each point
mesh = gv.Transform.from_points(
    sample.lons,
    sample.lats,
    # supply all three components
    vectors=(sample.u, sample.v, sample.w),
    # apply additional scaling to W values
    vectors_z_scaling=1500.0,
    # offset from surface so avoid downward-pointing arrows disappearing
    radius=1.1,
)
arrows = mesh.glyph(factor=0.02)

plotter = gv.GeoPlotter()
plotter.add_base_layer()
plotter.add_mesh(arrows, color="darkred")
plotter.add_coastlines()
plotter.add_graticule()
plotter.add_axes()

plotter.camera.zoom(1.3)
selected_view = [
    (0.6917810912064826, -3.065688850990997, 0.4317999141924935),
    (0.41358279170396495, 0.07362917740509836, 0.5091223320854129),
    (0.8088496364623022, 0.05726400555597287, 0.5852205560833343),
]
plotter.camera_position = selected_view
plotter.show()


# %%
# Finally, it sometimes makes more sense to display all arrows the same size so that
# direction is always readable.
# Here's an example with constant size arrows, but still colored by windspeed.

mesh = gv.Transform.from_points(
    sample.lons,
    sample.lats,
    vectors=(sample.u, sample.v),
)
# Note: with no scaling, the basic arrows size is now rather different
arrows = mesh.glyph(factor=0.1, scale=False)

plotter = gv.GeoPlotter()
plotter.add_base_layer()
plotter.add_mesh(arrows, cmap="magma")
plotter.add_coastlines()
plotter.add_graticule()
plotter.add_axes()

plotter.camera.zoom(1.3)
selected_view = [
    (-4.0688208659033505, -2.5462610064466777, -2.859304866708606),
    (-0.0037798285484313965, 0.005168497562408447, -0.0031679868698120117),
    (-0.523382090763761, -0.11174892277533728, 0.8447386372874786),
]
plotter.camera_position = selected_view
plotter.show()
