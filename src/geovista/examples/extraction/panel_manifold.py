#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Panel Extraction
----------------

This example demonstrates how to extract a cubed-sphere panel using a geodesic manifold.

📋 Summary
^^^^^^^^^^

TBD.

.. tags::

    component: coastlines, component: manifold, component: texture,
    sample: unstructured

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.geodesic import panel
from geovista.pantry.meshes import lfric_sst
import geovista.theme


def main() -> None:
    """TBD.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    # Load the sample mesh.
    mesh = lfric_sst()

    # Calculate the sample data range.
    clim = mesh.get_data_range()

    bbox = panel("antarctic")

    region = bbox.enclosed(mesh, preference="center")
    boundary = bbox.boundary(mesh)

    p = gv.GeoPlotter(shape="2|1")
    sargs = {"title": "Surface Temperature / K", "fmt": "%.0f"}

    # Extract the edges of the bounding-box manifold.
    bbox_edge = bbox.mesh.extract_feature_edges()

    p.subplot(0)
    p.add_mesh(mesh, show_scalar_bar=False)
    p.add_mesh(boundary, color="pink", line_width=3)
    p.add_mesh(bbox.mesh, color="orange", opacity=0.5)
    p.add_mesh(bbox_edge, color="yellow", line_width=3)
    p.add_text("0", position="upper_right", font_size=10, color="red")

    p.subplot(1)
    p.add_mesh(mesh, opacity=0.5, show_scalar_bar=False)
    p.add_mesh(boundary, color="pink", line_width=3)
    p.add_mesh(bbox.mesh, color="orange")
    p.add_mesh(bbox_edge, color="yellow", line_width=3)
    p.add_text("1", position="upper_right", font_size=10, color="red")

    p.subplot(2)
    p.add_mesh(region.threshold(), clim=clim, scalar_bar_args=sargs)
    p.add_mesh(boundary, color="pink", line_width=3)
    p.add_base_layer(texture=gv.natural_earth_1())
    p.add_coastlines(resolution="10m")
    title = "Cubed-Sphere Antarctic Panel Extraction"
    p.add_text(title, position="upper_left", font_size=10)
    p.add_text("2", position="upper_right", font_size=10, color="red")

    # Define a specific camera position.
    p.link_views()
    p.view_xy(negative=True)
    p.camera.roll = 45
    p.camera.zoom(1.2)

    p.add_axes()
    p.show()


if __name__ == "__main__":
    main()
