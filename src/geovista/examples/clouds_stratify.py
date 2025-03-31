#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Clouds Stratify
---------------

This example demonstrates how to render stratified cloud meshes.

📋 Summary
^^^^^^^^^^

Creates meshes from 1-D latitude and longitude unstructured cell points.

The resulting meshes contain quad cells and are constructed from CF UGRID
unstructured cell points and connectivity.

It uses an unstructured Met Office high-resolution LFRic C768 cubed-sphere
of Low, Medium, High and Very High Cloud Amount located on the mesh
faces/cells.

Note that, a threshold is applied to remove low-valued Cloud Amount cells,
and a linear opacity transfer function is applied to a custom cropped
colormap for each mesh which gets lighter with increased altitude. This
combination renders a cloud-like effect.

A Natural Earth base layer is also rendered along with Natural Earth
coastlines.

.. tags::

    component: coastlines, component: texture,
    domain: meteorology,
    filter: threshold,
    load: unstructured,
    resolution: high,
    style: colormap, style: opacity

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import cmocean
from cmocean.tools import crop_by_percent
from matplotlib.colors import LinearSegmentedColormap

import geovista as gv
from geovista.pantry.data import cloud_amount
import geovista.theme

# The colormap to render the clouds.
CMAP = cmocean.cm.gray

# Multiplication factor of the zlevel for cloud surface stratification.
ZLEVEL_FACTOR: int = 75


cmaps: dict[str, LinearSegmentedColormap] = {
    "low": crop_by_percent(CMAP, 10, which="both"),
    "medium": crop_by_percent(CMAP, 30, which="both"),
    "high": crop_by_percent(CMAP, 40, which="min"),
    "very_high": crop_by_percent(CMAP, 50, which="min"),
}


def main() -> None:
    """Plot stratified unstructured cloud meshes.

    Notes
    -----
    .. versionadded:: 0.4.0

    """
    # Use the pyvista linear opacity transfer function.
    opacity = "linear"

    # Define the data range.
    clim = (cmin := 0.3, 1.0)

    # Create the plotter.
    p = gv.GeoPlotter()

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
        )

        # Remove cells from the mesh below the specified threshold.
        mesh = mesh.threshold(cmin)

        p.add_mesh(
            mesh,
            clim=clim,
            opacity=opacity,
            cmap=cmaps[cloud],
            show_scalar_bar=False,
            zlevel=(i + 1) * ZLEVEL_FACTOR,
        )

    # Force zlevel alignment of coastlines and base layer.
    p.add_base_layer(texture=gv.natural_earth_1(), zlevel=0)
    p.add_coastlines()
    p.add_axes()
    p.add_text(
        "Low, Medium, High & Very High Cloud Amount",
        position="upper_left",
        font_size=10,
    )
    p.view_xy()
    p.camera.zoom(1.5)
    p.show()


if __name__ == "__main__":
    main()
