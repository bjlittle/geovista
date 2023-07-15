#!/usr/bin/env python3
"""Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.4.0

"""
from __future__ import annotations

import geovista as gv
from geovista.pantry import sample_earthquake
from geovista.common import to_cartesian
import geovista.theme


def main() -> None:
    """Create a point cloud from 2-D latitude and longitude large earthquake dataset.

    The resulting mesh contains point cloud of large earthquake.

    It uses a sample large earthquake dataset with point model.

    """
    # load sample data
    sample = sample_earthquake()

    # convert coordinate to cartesian
    points = to_cartesian(lons=sample.lons, lats=sample.lats)

    # plot the mesh
    plotter = gv.GeoPlotter()
    plotter.add_points(points, render_points_as_spheres=True, color="red")
    plotter.add_base_layer(texture=gv.natural_earth_1())
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.show()


if __name__ == "__main__":
    main()
