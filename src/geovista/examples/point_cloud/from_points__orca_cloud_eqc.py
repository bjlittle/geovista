#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
ORCA2 Point Cloud (Projected)
-----------------------------

This example demonstrates how to render a projected point cloud.

📋 Summary
^^^^^^^^^^

Creates a point cloud from 1-D latitude, longitude and z-levels.

The resulting mesh contains only points.

Based on a curvilinear ORCA2 global ocean with tri-polar model grid of
sea water potential temperature data, which has been reduced to a limited
area and pre-filtered for temperature gradients.

Note that, Natural Earth coastlines are also rendered along with a Natural
Earth base layer with opacity. Additionally, the mesh is transformed to
the Equidistant Cylindrical (Plate Carrée) conformal cylindrical
projection.

.. tags:: Coastlines, Point Cloud, Opacity, Projection, Texture

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import nemo_orca2_gradient
from geovista.pantry.meshes import ZLEVEL_SCALE_CLOUD
import geovista.theme


def main() -> None:
    """Plot a projected point cloud.

    Notes
    -----
    .. versionadded:: 0.3.0

    """
    # Load the sample data.
    sample = nemo_orca2_gradient()

    # Create the point cloud from the sample data.
    cloud = gv.Transform.from_points(
        sample.lons,
        sample.lats,
        data=sample.zlevel,
        name=sample.name,
        zlevel=-sample.zlevel,
        zscale=ZLEVEL_SCALE_CLOUD,
    )

    # Plot the projected point cloud.
    crs = "+proj=eqc"
    plotter = gv.GeoPlotter(crs=crs)
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(
        cloud,
        cmap="deep",
        point_size=5,
        scalar_bar_args=sargs,
        render_points_as_spheres=True,
    )
    plotter.add_coastlines(color="black")
    # Force zlevel alignment of coastlines and base layer.
    plotter.add_base_layer(texture=gv.natural_earth_1(), opacity=0.5, zlevel=0)
    plotter.add_axes()
    plotter.view_xy()
    plotter.add_text(
        f"ORCA Point-Cloud ({crs})",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.camera.zoom(1.5)
    plotter.show()


if __name__ == "__main__":
    main()
