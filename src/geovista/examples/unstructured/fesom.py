#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
FESOM Mesh
----------

This example demonstrates how to render an unstructured mesh.

📋 Summary
^^^^^^^^^^

Creates a mesh from 2D latitude and longitude unstructured bounds and connectivity.

The resulting mesh is formed from masked connectivity indexing into the points,
allowing the mesh to contain mixed cell geometries up to 18-sides (octadecagon).

It uses a AWI Climate Model (AWI-CI) Finite Element Sea ice-Ocean Model (FESOM)
v1.4 unstructured mesh of surface sea temperature data. The data targets the
mesh faces/cells.

Note that a Natural Earth base layer is rendered along with Natural Earth
coastlines.

.. tags::

    component: coastlines, component: texture,
    domain: oceanography,
    load: unstructured

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import fesom
import geovista.theme


def main() -> None:
    """Plot a FESOM unstructured mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    sample = fesom()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
        name=f"{sample.name} / {sample.units}",
    )

    # Plot the unstructured mesh.
    p = gv.GeoPlotter()
    p.add_mesh(mesh)
    p.add_base_layer(texture=gv.natural_earth_hypsometric())
    p.add_coastlines()
    p.add_axes()
    p.add_text(
        "AWI-CM FESOM v1.4 (10m Coastlines)",
        position="upper_left",
        font_size=10,
    )
    p.camera.zoom(1.3)
    p.show()


if __name__ == "__main__":
    main()
