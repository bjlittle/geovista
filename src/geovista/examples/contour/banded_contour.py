#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Banded Contour
--------------

This example demonstrates how to use banded contours.

📋 Summary
^^^^^^^^^^
Creates a mesh from 1-D latitude and longitude unstructured points.

It uses an unstructured Met Office LFRic C48 cubed-sphere of surface altitude
data.

We triangulate the mesh as this is the preferred format when using filters.

We use a threshold to make sure that all the land is contoured, while leaving the
sea thresholded out and then cast this to cells rather than points.

We set the number of contours to 13 as the color map we add (Set3) has 12 unique
colours and we have number of contours -1 actual contours.

.. tags::

    component: coastlines,
    component: texture,
    domain: orography,
    filter: threshold,
    load: unstructured,
    style: colormap

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista
from geovista.common import cast_UnstructuredGrid_to_PolyData as cast
from geovista.pantry.meshes import lfric_orog
import geovista.theme


def main() -> None:
    """Plot banded contours of surface altitude with a colormap.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    # Load the sample mesh.
    mesh = lfric_orog()

    # Triangulate the mesh prior to contouring.
    mesh.triangulate(inplace=True)

    # Remove only those cells where all their vertices have a surface altitude
    # below the specified height threshold.
    height = 1e-1
    mesh = cast(mesh.threshold(height, preference="point"))

    # Generate the filled contours and contour edges between bands.
    n_contours = 13
    contours, edges = mesh.contour_banded(n_contours)

    p = geovista.GeoPlotter()

    sargs = {"title": "Surface Altitude / m", "fmt": "%.0f"}
    p.add_mesh(contours, cmap="Set3", n_colors=n_contours - 1, scalar_bar_args=sargs)
    p.add_mesh(edges, color="black", zlevel=1)

    p.add_base_layer(texture=geovista.natural_earth_1())
    p.add_coastlines()

    # Render the scene using super-sample anti-aliasing.
    p.enable_anti_aliasing(aa_type="ssaa")

    # Define a specific camera position.
    p.view_vector(vector=(0, 1, 0.5))
    p.camera.zoom(1.2)

    p.add_axes()
    p.show()


if __name__ == "__main__":
    main()
