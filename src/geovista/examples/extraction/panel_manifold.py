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

This example uses an unstructured Met Office LFRic C48 cubed-sphere mesh of
surface temperature data located on the mesh faces/cells.

A geodesic cubed-sphere manifold is constructed for the Antarctic panel to
extract the cells of the surface temperature mesh contained within it. Note
that the extracted region contains only those cells where the center of the
cell is within the manifold.

The relationship between the manifold and the mesh is highlighted in the
first two subplots. Note that the boundary where the manifold intersects the
surface of the mesh being sampled is rendered in pink.

The cells extracted from the surface temperature mesh are rendered along with
a Natural Earth base layer and Natural Earth coastlines in the third subplot.
Again, the boundary of intersection between the manifold and mesh is rendered
in pink.

.. tags::

    component: coastlines, component: manifold, component: texture,
    filter: threshold,
    render: camera, render: subplots,
    sample: unstructured,
    style: opacity

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.geodesic import panel
from geovista.pantry.meshes import lfric_sst
import geovista.theme


def main() -> None:
    """Plot a cubed-sphere panel manifold and extracted region.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    # Load the sample mesh.
    mesh = lfric_sst()

    # Calculate the sample data range.
    clim = mesh.get_data_range()

    # Generate the geodesic bounding-box manifold for the antarctic
    # cubed-sphere panel.
    bbox = panel("antarctic")

    # Extract only cells from the sample mesh that have cell centers
    # enclosed within the manifold.
    region = bbox.enclosed(mesh, preference="center")

    # Determine the boundary where the manifold intersects the surface
    # of the sample data mesh.
    boundary = bbox.boundary(mesh)

    # Create a plotter containing three subplots in two columns, where
    # the first column has two rows, and the second column has only one.
    p = gv.GeoPlotter(shape="2|1")
    sargs = {"title": "Surface Temperature / K", "fmt": "%.0f"}

    # Extract the edges of the bounding-box manifold.
    bbox_edge = bbox.mesh.extract_feature_edges()

    # First subplot: render the sample data with a transparent
    # manifold, highlighting the manifold edges and boundary.
    p.subplot(0)
    p.add_mesh(mesh, show_scalar_bar=False)
    p.add_mesh(boundary, color="pink", line_width=3)
    p.add_mesh(bbox.mesh, color="orange", opacity=0.5)
    p.add_mesh(bbox_edge, color="yellow", line_width=3)
    p.add_text("0", position="upper_right", font_size=10, color="red")

    # Second subplot: now render a transparent sample data mesh with a
    # solid manifold, again highlighting the manifold edges and boundary.
    p.subplot(1)
    p.add_mesh(mesh, opacity=0.5, show_scalar_bar=False)
    p.add_mesh(boundary, color="pink", line_width=3)
    p.add_mesh(bbox.mesh, color="orange")
    p.add_mesh(bbox_edge, color="yellow", line_width=3)
    p.add_text("1", position="upper_right", font_size=10, color="red")

    # Third subplot: render the extracted antarctic region of sample data
    # along with the boundary and coastlines on a texture mapped base layer.
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
