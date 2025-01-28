#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Wind Directions
---------------

This example demonstrates how to display equal-sized wind direction arrows.

📋 Summary
^^^^^^^^^^

The data source provides X and Y arrays containing plain longitude and
latitude values, which is the most common case.

The wind information is provided in three separate field arrays, 'U, V and W',
i.e. eastward, northward and vertical components.

These values are coded for each location (X, Y), measured relative to the longitude,
latitude and vertical directions at each point.

In this example we show how to display wind arrows ith a fixed length, showing
direction only, but with scale colour still indicating mangitude.
"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import lfric_winds

# get sample data
sample = lfric_winds()

mesh = gv.Transform.from_points(
    sample.lons,
    sample.lats,
    vectors=(sample.u, sample.v),
)
# Note: with "scale=False", the sizes don't changes and the basic size is now different,
# so the visibly suitable 'factor' is also rather different.
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
