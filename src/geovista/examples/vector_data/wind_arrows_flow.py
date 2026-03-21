#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Wind Arrows Flow
----------------

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
    """Demonstrate a flow direction plot with fixed-length arrows.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    # get sample data
    sample = lfric_winds()

    mesh = gv.Transform.from_points(
        sample.lons,
        sample.lats,
        vectors=(sample.u, sample.v),
    )
    # Note: with "scale=False", arrow size is fixed and controlled by "factor".
    arrows = mesh.glyph(factor=0.1, scale=False, color_mode="vector")

    p = gv.GeoPlotter()
    sargs = {"title": f"{sample.name} / {sample.units}"}
    p.add_mesh(arrows, cmap="magma", scalar_bar_args=sargs)
    p.add_base_layer(texture=gv.natural_earth_hypsometric())
    p.add_graticule()

    # Define a specific camera position and orientation.
    cpos = pv.CameraPosition(
        position=(-4.06882, -2.54626, -2.85930),
        focal_point=(-0.00378, 0.00517, -0.00317),
        viewup=(-0.52338, -0.11175, 0.84474),
    )
    p.camera.zoom(1.3)

    p.add_axes()
    p.show(cpos=cpos)


if __name__ == "__main__":
    main()
