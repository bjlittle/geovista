#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Arrows
------

This example demonstrates how to render glyph arrows of a simple vector field.

📋 Summary
^^^^^^^^^^

The vector field is generated based on the cartesian ``XYZ`` vertices of a
regular quad-cell sample grid.

A Natural Earth base layer is also rendered for geolocation context.

.. tags:: Globe, Lighting, Texture, Vectors

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import numpy as np

import geovista as gv
from geovista.pantry.meshes import regular_grid
import geovista.theme


def main() -> None:
    """Plot a simple synthetic vector field.

    Notes
    -----
    .. versionadded:: 0.4.0

    """
    # Generate a regular (rN) YX grid of (N, 1.5N) cells.
    mesh = regular_grid(resolution="r25")

    # Attach synthetic vectors.
    vectors = np.vstack(
        (
            -mesh.points[:, 1],
            mesh.points[:, 0],
            mesh.points[:, 2] * 0,
        )
    ).T
    mesh["vectors"] = vectors * 0.1
    mesh.set_active_vectors("vectors")

    # Plot the vectors.
    plotter = gv.GeoPlotter()
    plotter.add_base_layer(texture=gv.natural_earth_1(), zlevel=0, lighting=False)
    plotter.add_mesh(mesh.arrows, lighting=False)
    plotter.add_axes()
    plotter.camera.zoom(1.3)
    plotter.show()


if __name__ == "__main__":
    main()
