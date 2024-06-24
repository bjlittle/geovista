#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
LFRic Orography
---------------

This example demonstrates how to render a warped unstructured cubed-sphere mesh.

📋 Summary
^^^^^^^^^^
Creates a mesh from 1-D latitude and longitude unstructured points and
connectivity.

It uses an unstructured Met Office LFRic C48 cubed-sphere of surface altitude
data.

The resulting mesh contains quad cells and is constructed from CF UGRID
unstructured cell points and connectivity.

Note that the scalar elevation values are located on the mesh nodes/points
which results in the rendered colours being interpolated across the cell faces.
A ``pyvista`` "warp" operation extrudes the mesh, using the same node altitude
values, to highlight the global surface topography.

The warp uses :meth:`~pyvista.PolyDataFilters.compute_normals` and
:meth:`~pyvista.DataSetFilters.warp_by_scalar`. See
`Computing Surface Normals <https://docs.pyvista.org/version/stable/examples/01-filter/compute-normals.htm>`_
for further details.

.. tags:: Globe, Unstructured, Warp

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import lfric_orog
import geovista.theme


def main() -> None:
    """Plot a warped LFRic unstructured mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    sample = lfric_orog()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
        name=sample.name,
    )

    # Warp the mesh nodes by the surface altitude.
    mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
    mesh.warp_by_scalar(scalars=sample.name, inplace=True, factor=2e-5)

    # Plot the unstructured mesh.
    plotter = gv.GeoPlotter()
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_axes()
    plotter.add_text(
        "LFRic C48 Unstructured Cube-Sphere",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.camera.zoom(1.3)
    plotter.show()


if __name__ == "__main__":
    main()
