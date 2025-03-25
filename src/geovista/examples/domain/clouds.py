#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Clouds
------

This example demonstrates how to render an unstructured cloud mesh.

📋 Summary
^^^^^^^^^^

Creates a mesh from 1-D latitude and longitude unstructured cell points.

The resulting mesh contains quad cells and is constructed from CF UGRID
unstructured cell points and connectivity.

It uses an unstructured Met Office high-resolution LFRic C768 cubed-sphere
of High Cloud Amount located on the mesh faces/cells.

Note that, a threshold is applied to remove low-valued Cloud Amount cells,
and a custom colormap is applied to the mesh to crop out unwanted darker
shades.

A Natural Earth base layer is also rendered along with Natural Earth
coastlines.

.. tags::

    component: coastlines, component: texture,
    domain: meteorology,
    filter: threshold,
    load: unstructured,
    resolution: high

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import cmocean
from cmocean.tools import crop_by_percent

import geovista as gv
from geovista.pantry.data import cloud_amount
import geovista.theme

#: Multiplication factor of the zlevel for cloud surface stratification.
ZLEVEL_FACTOR: int = 75


def main() -> None:
    """Plot an unstructured cloud mesh.

    Notes
    -----
    .. versionadded:: 0.4.0

    """
    # Define the data range.
    clim = (cmin := 0.3, 1.0)

    # Customise the colormap.
    cmap = crop_by_percent(cmocean.cm.gray, 40, which="min")

    # Create the plotter.
    p = gv.GeoPlotter()

    # Load the sample data.
    sample = cloud_amount("high")

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
        cmap=cmap,
        show_scalar_bar=False,
        zlevel=ZLEVEL_FACTOR,
    )

    # Force zlevel alignment of coastlines and base layer.
    p.add_base_layer(texture=gv.natural_earth_1(), zlevel=0)
    p.add_coastlines()
    p.add_axes()
    p.add_text(
        "High Cloud Amount",
        position="upper_left",
        font_size=10,
    )
    p.camera.zoom(1.5)
    p.show()


if __name__ == "__main__":
    main()
