#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
LFRic Orography (Projected)
---------------------------

This example demonstrates how to render a projected warped unstructured
cubed-sphere mesh.

📋 Summary
^^^^^^^^^^

Uses an unstructured Met Office LFRic C48 cubed-sphere mesh of surface altitude
data.

The mesh contains quad cells and is constructed from CF UGRID unstructured cell
points and connectivity.

The mesh is transformed onto an Equidistant Cylindrical (Plate Carrée)
projection.

Note that the scalar elevation values are located on the mesh nodes/points
which results in the rendered colours being interpolated across the cell faces.
A ``pyvista`` "warp" operation extrudes the mesh, using the same node altitude
values, to highlight the global surface topography.

The warp uses :meth:`~pyvista.PolyDataFilters.compute_normals` and
:meth:`~pyvista.DataSetFilters.warp_by_scalar`. See
`Computing Surface Normals <https://docs.pyvista.org/examples/01-filter/compute-normals>`_
for further details.

.. tags::

    domain: orography,
    filter: warp,
    sample: unstructured,
    projection: crs, projection: transform

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.meshes import lfric_orog
import geovista.theme
from geovista.transform import transform_mesh


def main() -> None:
    """Plot a projected warped LFRic unstructured mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample mesh.
    mesh = lfric_orog()

    # Transform the mesh to the Plate Carrée projection.
    mesh = transform_mesh(mesh, crs := "esri:54001")

    # Warp the mesh nodes by the surface altitude.
    mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
    mesh.warp_by_scalar(inplace=True, factor=200)

    # Plot the unstructured mesh.
    p = gv.GeoPlotter(crs=crs)
    sargs = {
        "title": "Surface Altitude / m",
        "fmt": "%.0f",
        "outline": True,
        "background_color": "white",
        "fill": True,
    }
    p.add_mesh(mesh, scalar_bar_args=sargs)
    p.add_axes()
    p.add_text(
        f"LFRic C48 Unstructured Cube-Sphere ({crs})",
        position="upper_left",
        font_size=10,
    )
    p.view_xy()
    p.camera.zoom(1.5)
    p.show()


if __name__ == "__main__":
    main()
