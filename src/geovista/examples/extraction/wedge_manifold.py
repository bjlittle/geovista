#!/usr/bin/env python3
# Copyright (c) 2025, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Regional Manifold Extraction
----------------------------

This example demonstrates how to extract a region from a mesh using a geodesic manifold.

📋 Summary
^^^^^^^^^^
Creates a mesh from 1-D latitude and longitude unstructured points and
connectivity.

Isolates wedges of this mesh and plots them onto natural earth base layer
texture.

It uses an unstructured Met Office LFRic C48 cubed-sphere of surface altitude
data.

The resulting mesh contains quad cells and is constructed from CF UGRID
unstructured cell points and connectivity.

.. tags::

    domain: orography,
    component: texture,
    load: unstructured

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.geodesic import wedge
from geovista.pantry.meshes import lfric_orog
import geovista.theme


def main() -> None:
    """Plot three wedge shaped orographies, each with a different enclosure method.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    c48_orog = lfric_orog()

    # create the wedges
    first_bbox = wedge(-25, 25)
    second_bbox = wedge(65, 115)
    third_bbox = wedge(155, 205)

    # fill the wedges with orog plots, at three different preferences
    first_region = first_bbox.enclosed(c48_orog, preference="cell")
    second_region = second_bbox.enclosed(c48_orog, preference="point")
    third_region = third_bbox.enclosed(c48_orog, preference="center")
    clim = (-114, 5176)

    p = gv.GeoPlotter()
    sargs = {"title": f"{first_region.active_scalars_name} / m", "fmt": "%.1f"}

    # add the three wedges to the map
    p.add_mesh(first_region, clim=clim, scalar_bar_args=sargs)
    p.add_mesh(second_region, clim=clim, scalar_bar_args=sargs)
    p.add_mesh(third_region, clim=clim, scalar_bar_args=sargs)

    # add an outline to each wedge
    p.add_mesh(first_bbox.boundary(c48_orog), color="red", line_width=3)
    p.add_mesh(second_bbox.boundary(c48_orog), color="purple", line_width=3)
    p.add_mesh(third_bbox.boundary(c48_orog), color="orange", line_width=3)

    # add coastlines and a basic globe to the background
    p.add_base_layer(texture=gv.natural_earth_hypsometric())
    p.add_coastlines(resolution="10m")

    camera_angle = (90, 90, 90)
    p.view_vector(camera_angle)
    p.camera.zoom(1.2)
    p.show_axes()
    p.show()


if __name__ == "__main__":
    main()
