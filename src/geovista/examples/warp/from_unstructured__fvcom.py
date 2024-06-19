#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
FVCOM Bathymetry
----------------

This example demonstrates how to render a warped unstructured triangular mesh.

📋 Summary
^^^^^^^^^^

Creates a mesh from 1-D latitude and longitude unstructured points and
connectivity, warped to show the vertical profile.

It uses an unstructured grid Finite Volume Community Ocean Model (FVCOM) mesh of
sea floor depth below geoid data.

The resulting mesh contains triangular cells. The connectivity is required to
construct the cells from the unstructured points.

Note that, the data is on the mesh faces/cells, but also on the nodes/points.

A ``pyvista`` "warp" operation is used to extrude the mesh by the point depth
values, to reveal the bathymetry of the Plymouth Sound and Tamar River in
Cornwall, UK.

The warp uses :meth:`~pyvista.PolyDataFilters.compute_normals` and
:meth:`~pyvista.DataSetFilters.warp_by_scalar`. See
`Computing Surface Normals <https://docs.pyvista.org/version/stable/examples/01-filter/compute-normals.htm>`_
for further details.

.. tags:: Unstructured, Warp

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import fvcom_tamar
import geovista.theme


def main() -> None:
    """Plot a warped FVCOM unstructured mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    sample = fvcom_tamar()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.face,
        name="face",
    )

    # Warp the mesh nodes by the bathymetry.
    mesh.point_data["node"] = sample.node
    mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
    mesh.warp_by_scalar(scalars="node", inplace=True, factor=2e-5)

    # Plot the unstructured mesh.
    plotter = gv.GeoPlotter()
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, cmap="deep", scalars="face", scalar_bar_args=sargs)
    plotter.add_axes()
    plotter.add_text(
        "PML FVCOM Tamar",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.camera.zoom(1.2)
    plotter.show()


if __name__ == "__main__":
    main()
