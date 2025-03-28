#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
DYNAMICO Mesh
-------------

This example demonstrates how to render an unstructured hexagon/pentagon mesh.

📋 Summary
^^^^^^^^^^

Creates a mesh from 2-D latitude and longitude unstructured cell bounds.

The resulting mesh contains hexagonal cells tessellated around 12 pentagon cells,
which are centered over the 12 vertices of a base icosahedron.

It uses surface air pressure data from the DYNAMICO project, a new dynamical core
for the Laboratoire de Météorologie Dynamique (LMD-Z), the atmospheric General
Circulation Model (GCM) part of Institut Pierre-Simon Laplace (IPSL-CM) Earth
System Model. The data targets the mesh faces/cells.

Note that, a graticule and Natural Earth coastlines are also rendered.

.. tags::

    component: coastlines, component: graticule,
    domain: meteorology,
    load: unstructured

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import dynamico
import geovista.theme


def main() -> None:
    """Plot a DYNAMICO unstructured mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # Load the sample data.
    sample = dynamico()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_unstructured(
        sample.lons,
        sample.lats,
        data=sample.data,
        name=f"{sample.name} / {sample.units}",
    )

    # Plot the unstructured mesh.
    p = gv.GeoPlotter()
    p.add_mesh(mesh)
    p.add_coastlines()
    p.add_graticule()
    p.add_axes()
    p.add_text(
        "DYNAMICO Icosahedral (10m Coastlines)",
        position="upper_left",
        font_size=10,
    )
    p.view_xz(negative=True)
    p.camera.zoom(1.3)
    p.show()


if __name__ == "__main__":
    main()
