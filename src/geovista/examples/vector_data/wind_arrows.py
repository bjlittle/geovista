#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Wind Arrows Plot
----------------

This example demonstrates how to display horizontal winds.

📋 Summary
^^^^^^^^^^

The data source provides X and Y arrays containing plain longitude and
latitude values, which is the most common case.

The wind information is provided in three separate field arrays, 'U, V and W',
i.e. eastward, northward and vertical components.

These values are coded for each location (X, Y), measured relative to the longitude,
latitude and vertical directions at each point.

There is no connectivity provided, so each point is a separate location in a mesh of
scattered points, and each point has an associated vector value independent of
the others.  We use the :meth:`geovista.bridge.Transform.from_points` method, passing
the winds to the ``vectors`` keyword, producing a mesh of scattered points with
attached vectors.

The arrows themselves are created from this mesh via the
:meth:`pyvista.DataSetFilters.glyph` method.

Here we show just horizontal winds (U, V), which are usually of the most interest.

.. tags::

    component: graticule, component: texture, component: vectors,
    domain: meteorology,
    filter: glyph,
    load: vectors,
    version: 0.6.0

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import pyvista as pv

import geovista as gv
from geovista.pantry.data import lfric_winds
import geovista.theme


def main() -> None:
    """Demonstrate horizontal wind arrows plotting."""
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
    # NOTE: apply an overall scaling factor to make the arrows a reasonable size.
    arrows = mesh.glyph(factor=0.02)

    # Add the arrows to a Plotter with other aspects, and display
    p = gv.GeoPlotter()
    p.add_base_layer(texture=gv.natural_earth_hypsometric())
    p.add_mesh(arrows, cmap="inferno")
    p.add_graticule()

    # Define a specific camera position and orientation.
    cpos = pv.CameraPosition(
        position=(-4.0688208659033505, -2.5462610064466777, -2.859304866708606),
        focal_point=(
            -0.0037798285484313965,
            0.005168497562408447,
            -0.0031679868698120117,
        ),
        viewup=(-0.523382090763761, -0.11174892277533728, 0.8447386372874786),
    )
    p.camera.zoom(1.3)

    p.add_axes()
    p.show(cpos=cpos)


if __name__ == "__main__":
    main()
