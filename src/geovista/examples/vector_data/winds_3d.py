#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
3D Wind Arrows
--------------

This example demonstrates how to plot 3D wind vectors.

📋 Summary
^^^^^^^^^^

The data source provides X and Y arrays containing plain longitude and
latitude values, which is the most common case.

3D wind components are provided in three separate field arrays, 'U, V and W',
i.e. eastward, northward and vertical components.

There is no connectivity provided, so each location has its own attached vector, and is
independent of the others.  We use the :meth:`geovista.bridge.Transform.from_points`
method, passing the winds to the ``vectors`` keyword, producing a mesh of scattered
points with attached vectors.

The arrows themselves are created from this mesh via the
:meth:`pyvista.DataSetFilters.glyph` method.

Here, we display 3-dimensional wind arrows.
We have amplified the "W" components by a considerable factor, which is typical since
vertical winds are generally much smaller in magnitude and otherwise tend to be not
very visible.

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
    """Demonstrate 3-dimensional wind arrows plotting.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    # get sample data
    sample = lfric_winds()

    # Create a mesh of individual points, adding vectors at each point.
    mesh = gv.Transform.from_points(
        sample.lons,
        sample.lats,
        # supply all three components, but with a big extra scaling on the "W" values
        vectors=(sample.u, sample.v, 1500.0 * sample.w),
        # offset from surface to avoid downward-pointing arrows disappearing
        radius=1.1,
    )

    # Create a new mesh containing arrow glyphs, from the mesh vectors.
    # NOTE: choose an overall scaling factor to make the arrows a reasonable size.
    arrows = mesh.glyph(factor=0.02)

    # Add the arrows to a Plotter with other aspects, and display
    p = gv.GeoPlotter()
    p.add_base_layer(texture=gv.natural_earth_hypsometric())
    p.add_mesh(arrows, cmap="inferno")
    p.add_graticule()

    # Define a specific camera position and orientation.
    cpos = pv.CameraPosition(
        position=(0.69178, -3.06569, 0.43180),
        focal_point=(0.41358, 0.07363, 0.50912),
        viewup=(0.80885, 0.05726, 0.58522),
    )
    p.camera.zoom(1.3)

    p.add_axes()
    p.show(cpos=cpos)


if __name__ == "__main__":
    main()
