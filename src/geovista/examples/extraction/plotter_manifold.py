#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Plotter Extraction
------------------

This example demonstrates how to streamline geometry extraction within a plotter.

📋 Summary
^^^^^^^^^^

This example uses an unstructured DYNAMICO icosahedral unstructured mesh of
Surface Air Pressure data located on hexagonal/pentagonal faces/cells.

A geodesic bounding-box manifold (:class:`~geovista.geodesic.BBox`) is constructed
for the cubed-sphere Arctic panel. Note that the boundary where this manifold
intersects the surface of the earth is highlighted in gold.

Global geometries are added to the plotter first before the bounding-box
manifold is then used by the plotter to automatically extract geometries added to
the scene.

The behaviour of the extraction is controlled through the
:attr:`~geovista.geodesic.BBox.preference` and :attr:`~geovista.geodesic.BBox.outside`
propetries of the bounding-box manifold. These properties define the extraction
membership criterion of a mesh cell and whether cells inside or outside the manifold
are selected.

A threshold is applied to the Surface Air Pressure mesh prior to extraction,
and Natural Earth coastlines and texture mapped Natural Earth base layers of
different colours and types are rendered inside and outside the Arctic cubed-sphere
panel to reinforce the region of interest.

.. hint::
    :class: dropdown, toggle-shown

    A :class:`~geovista.geoplotter.GeoPlotter` instance may be created using
    the ``manifold`` keyword argument e.g.,

    .. code-block:: python

       import geovista
       from geovista.geodesic import panel

       p = geovista.GeoPlotter(manifold=panel("africa"))


.. tags::

    component: coastlines, component: graticule, component: manifold, component: texture,
    filter: threshold,
    plot: anti-aliasing, plot: camera,
    sample: unstructured,
    widget: north-arrow

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.geodesic import panel
from geovista.pantry.meshes import dynamico
import geovista.theme


def main() -> None:
    """Demonstrate automated manifold extraction of plotter geometries.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    # Load the sample mesh.
    mesh = dynamico()

    # Generate the geodesic bounding-box manifold for the arctic
    # cubed-sphere panel.
    bbox = panel("arctic")

    p = gv.GeoPlotter()

    # Render a global NASA Black Marble "night lights" texture
    # and highlight the bounding-box manifold boundary.
    p.add_base_layer(texture=gv.black_marble())
    p.add_mesh(bbox.boundary(), color="gold", line_width=2)

    # Add the bounding-box manifold to the plotter which will
    # automatically extract geometries added to the scene.
    p.manifold = bbox
    p.add_base_layer(texture=gv.natural_earth_1())

    # Change the bounding-box manifold extraction criterion
    # from cell "center" (default) to the entire mesh "cell".
    p.manifold.preference = "cell"

    # Extract and render the coastlines, meridians, parallels and the
    # DYNAMICO icosahedral mesh (thresholded) enclosed by the manifold.
    sargs = {"title": "Surface Air Pressure / Pa", "fmt": "%.0f"}
    p.add_mesh(mesh.threshold(1e5, invert=True), cmap="diff", scalar_bar_args=sargs)
    p.add_graticule(factor=2, mesh_args={"line_width": 2})
    p.add_coastlines()

    # Now extract geometries "outside" the manifold rather than "inside".
    p.manifold.outside = True
    p.add_coastlines(color="gold")

    # Render the scene with fast approximate anti-aliasing.
    p.enable_anti_aliasing(aa_type="fxaa")

    # Define a specific camera position.
    p.view_xy()
    p.camera.zoom(1.7)

    p.add_north_arrow_widget()
    p.show()


if __name__ == "__main__":
    main()
