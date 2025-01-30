#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Horizontal Flow
---------------

This example demonstrates how to display equal-sized flow direction arrows.

📋 Summary
^^^^^^^^^^

The data source provides X and Y arrays containing plain longitude and
latitude values, with eastward- and northward-going flow components,
which is the most common case.

The sample flow data is actually provided in three separate surface-oriented
component arrays, 'U, V and W', i.e. eastward, northward and vertical components,
but we are only using the first two.  We use the
:meth:`geovista.bridge.Transform.from_points` method, passing the winds to the
``vectors`` keyword, producing a mesh of scattered points with attached vectors.

The arrows themselves are created from this mesh via the
:meth:`pyvista.DataSetFilters.glyph` method.

In this example we display flow arrows of a fixed length, showing direction
only, but with a colour scale indicating magnitude.
"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import lfric_winds


def main() -> None:
    """Demonstrate a flow direction plot with fixed-length arrows."""
    # get sample data
    sample = lfric_winds()

    mesh = gv.Transform.from_points(
        sample.lons,
        sample.lats,
        vectors=(sample.u, sample.v),
    )
    # Note: with "scale=False", arrow size is fixed and controlled by "factor".
    arrows = mesh.glyph(factor=0.1, scale=False)

    p = gv.GeoPlotter()
    p.add_base_layer()
    p.add_mesh(arrows, cmap="magma")
    p.add_coastlines()
    p.add_graticule()
    p.add_axes()

    p.camera.zoom(1.3)
    selected_view = [
        (-4.0688208659033505, -2.5462610064466777, -2.859304866708606),
        (-0.0037798285484313965, 0.005168497562408447, -0.0031679868698120117),
        (-0.523382090763761, -0.11174892277533728, 0.8447386372874786),
    ]
    p.camera_position = selected_view
    p.show()


if __name__ == "__main__":
    main()
