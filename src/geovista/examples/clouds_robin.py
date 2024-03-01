#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Clouds (Projected)
------------------

This example demonstrates how to render projected stratified unstructured meshes.

📋 Summary
^^^^^^^^^^

Creates meshes from 1-D latitude and longitude unstructured cell points.

The resulting meshes contain quad cells and are constructed from CF UGRID
unstructured cell points and connectivity.

It uses an unstructured Met Office high-resolution LFRic C768 cubed-sphere
of low, medium, high and very high cloud amount located on the mesh
faces/cells.

Note that, a threshold is applied to remove lower cloud amount cells,
and a linear opacity transfer function is applied to a custom cropped
colormap of each cloud amount type mesh i.e., the colormaps get lighter
with increased altitude.

A Natural Earth base layer is also rendered along with Natural Earth
coastlines.

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import cmocean
from matplotlib.colors import LinearSegmentedColormap

import geovista as gv
from geovista.pantry.data import cloud_amount
import geovista.theme

#: The colormap to render the clouds.
CMAP = cmocean.cm.gray

#: Multiplication factor of the zlevel for cloud surface stratification.
ZLEVEL_FACTOR: int = 75


cmaps: dict[str, LinearSegmentedColormap] = {
    "low": cmocean.tools.crop_by_percent(CMAP, 10, which="both"),
    "medium": cmocean.tools.crop_by_percent(CMAP, 30, which="both"),
    "high": cmocean.tools.crop_by_percent(CMAP, 40, which="min"),
    "very_high": cmocean.tools.crop_by_percent(CMAP, 50, which="min"),
}


def main() -> None:
    """Plot projected stratified unstructured meshes.

    Notes
    -----
    .. versionadded:: 0.4.0

    """
    # Use the pyvista linear opacity transfer function.
    opacity = "linear"
    clim = (cmin := 0.3, 1.0)

    # Create the plotter.
    crs = "+proj=robin"
    plotter = gv.GeoPlotter(crs=crs)

    for i, cloud in enumerate(cmaps):
        # Load the sample data.
        sample = cloud_amount(cloud)

        # Create the mesh from the sample data.
        mesh = gv.Transform.from_unstructured(
            sample.lons,
            sample.lats,
            sample.connectivity,
            data=sample.data,
            start_index=sample.start_index,
            name=cloud,
        )

        # Remove cells from the mesh below the specified threshold.
        mesh = mesh.threshold(cmin)

        plotter.add_mesh(
            mesh,
            clim=clim,
            opacity=opacity,
            cmap=cmaps[cloud],
            show_scalar_bar=False,
            zlevel=(i + 1) * ZLEVEL_FACTOR,
        )

    # Force zlevel alignment of coastlines and base layer.
    plotter.add_base_layer(texture=gv.natural_earth_1(), zlevel=0)
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        f"Low, Medium, High & Very High Cloud Amount ({crs})",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.camera.zoom(1.5)
    plotter.show()


if __name__ == "__main__":
    main()
