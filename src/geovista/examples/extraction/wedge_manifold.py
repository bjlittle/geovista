#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Wedge Extraction
----------------

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

    component: coastlines,
    component: manifold,
    component: texture,
    domain: orography,
    load: unstructured

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.geodesic import wedge
from geovista.pantry.data import lfric_orog
import geovista.theme


def main() -> None:
    """Extract and plot 3 wedge regions, each using different enclosure methods.

    Notes
    -----
    .. versionadded:: 0.6.0

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

    # Calculate the sample data range.
    clim = mesh.get_data_range()

    # Create 3 different wedge geodesic bounding-box manifolds.
    bbox_1 = wedge(-25, 25)
    bbox_2 = wedge(65, 115)
    bbox_3 = wedge(155, 205)

    # Extract the underlying sample mesh within each manifold using a different
    # preference which defines the criterion of sample mesh cell enclosure.
    region_1 = bbox_1.enclosed(mesh, preference="cell")
    region_2 = bbox_2.enclosed(mesh, preference="point")
    region_3 = bbox_3.enclosed(mesh, preference="center")

    p = gv.GeoPlotter()
    sargs = {"title": f"{sample.name} / {sample.units}", "fmt": "%.1f"}

    # Add the 3 extracted regions.
    p.add_mesh(region_1, clim=clim, scalar_bar_args=sargs)
    p.add_mesh(region_2, clim=clim, scalar_bar_args=sargs)
    p.add_mesh(region_3, clim=clim, scalar_bar_args=sargs)

    # Add the surface boundary of each wedge region.
    p.add_mesh(bbox_1.boundary(mesh), color="red", line_width=3)
    p.add_mesh(bbox_2.boundary(mesh), color="purple", line_width=3)
    p.add_mesh(bbox_3.boundary(mesh), color="orange", line_width=3)

    # Add coastlines and a texture mapped base layer.
    p.add_base_layer(texture=gv.natural_earth_hypsometric())
    p.add_coastlines(resolution="10m")

    # Define a specific camera position.
    p.view_vector(vector=(1, 1, 1))
    p.camera.zoom(1.2)

    p.show_axes()
    p.show()


if __name__ == "__main__":
    main()
