#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
3D Wind Arrows
--------------

This example demonstrates how to display wind vectors.

📋 Summary
^^^^^^^^^^

The data source provides X and Y arrays containing plain longitude and
latitude values, which is the most common case.  

The wind information is provided in three separate field arrays, 'U, V and W'
 -- i.e. eastward, northward and vertical components.  
These values are coded for each location (X, Y), measured relative to the longitude,
latitude and vertical directions at each point.

There is no connectivity provided, so each location has a vector and is independent of
the others.  Hence we use the `geovista.Transform.from_points` function, passing the
winds to the `vectors` keyword. 

Initially, we can just show the horizontal winds, as this easier to interprt
We scale up the 'W' values, since vertical winds are typically much smaller than
horizontal.  Coastlines and a base layer are also added for ease of viewing.

"""  # noqa: D205,D212,D400
import geovista as gv
from geovista.pantry.data import lfric_winds

# get sample data
sample = lfric_winds()

# Create a mesh of individual points, adding vectors at each point
mesh = gv.Transform.from_points(
    sample.lons,
    sample.lats,
    vectors = (sample.u, sample.v),
)

# Create a new mesh containing arrow glyphs, from the mesh vectors
# NOTE: the 'mesh vectors' are a specific concept in PyVista
# NOTE ALSO: the 'arrows' property is effectively a convenience for calling
#  :meth:'~pyvista.Dataset.glyph'
arrows = mesh.glyph(factor=0.02)  # Note the overall scaling factor

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
    (-0.523382090763761, -0.11174892277533728, 0.8447386372874786)
]
plotter.camera_position = selected_view
plotter.show()
print(plotter.camera_position)


# %%
# Repeat, but now add in the 'W' vertical components.
# These need scaling up, since vertical winds are typically much smaller than
# horizontal.
# We also use one colour, and apply a vertical offset to prevent downward-going arrows
# from disappearing into the surface.

# Create a mesh of individual points, adding vectors at each point
mesh = gv.Transform.from_points(
    sample.lons,
    sample.lats,
    # supply all three components
    vectors = (sample.u, sample.v, sample.w),
    # apply additional scaling and a vertical offset
    vectors_z_scaling=1500.,
    radius=1.1
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
    (0.9892890077409511, -2.9925812011503097, 1.008438916341214),
    (0.456372154072792, 0.10044567821980169, 0.7120015972700701),
    (-0.39009517660643345, 0.021012607195809205, 0.9205347486799345)
]
plotter.camera_position = selected_view
plotter.show()
print(plotter.camera_position)


# %%
# Finally, it sometimes makes more sense to display all arrows the same size so that
# direction is always readable.
# Here's an example of constant size, but still colored by windspeed.

# Create a mesh of individual points, adding vectors at each point
mesh = gv.Transform.from_points(
    sample.lons,
    sample.lats,
    # supply all three components
    vectors = (sample.u, sample.v),
)
# Note: the overall size scale is now different, too
arrows = mesh.glyph(factor=0.1, scale=False)

plotter = gv.GeoPlotter()
plotter.add_base_layer()
plotter.add_mesh(arrows, cmap="magma")
plotter.add_coastlines()
plotter.add_graticule()
plotter.add_axes()

plotter.camera.zoom(1.3)  # adjusts the camera view angle
selected_view = [
    (-4.0688208659033505, -2.5462610064466777, -2.859304866708606),
    (-0.0037798285484313965, 0.005168497562408447, -0.0031679868698120117),
    (-0.523382090763761, -0.11174892277533728, 0.8447386372874786)
]
plotter.camera_position = selected_view
plotter.show()
print(plotter.camera_position)
