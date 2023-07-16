#!/usr/bin/env python3
"""Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.4.0

"""
from __future__ import annotations

import geovista as gv
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv

import cartopy
from geovista.common import to_cartesian
import cartopy.crs as ccrs

from pyproj import CRS

import geovista



def main() -> None:
    """Create vectors plotting inspired by cartopy."""


    # make cool swirly pattern
    sphere = pv.Sphere(gv.common.RADIUS)
    vectors = np.vstack(
        (
            - sphere.points[:, 1],
            sphere.points[:, 0],
            sphere.points[:, 2] * 0.0,
        )
    ).T
    sphere["vectors"] = vectors * 0.1
    sphere.set_active_vectors("vectors")

    # plot mesh
    plotter = gv.GeoPlotter()
    plotter.set_background('gray')
    plotter.enable_anti_aliasing('ssaa')
    plotter.add_base_layer(color="white", lighting=False)
    plotter.add_coastlines(color="black", lighting=False)
    plotter.add_mesh(sphere.arrows, lighting=False)
    plotter.camera.zoom(1.5)
    plotter.add_axes()
    plotter.show()


if __name__ == '__main__':
    main()
