#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.


"""
GeoTIFF DEM
-----------

This example demonstrates how to render **Digital Elevation Model** (DEM) data
encoded in an `OGC GeoTIFF <https://www.ogc.org/standards/geotiff/>`_
as a geolocated mesh.

📋 Summary
^^^^^^^^^^

Creates an elevation warped mesh from GeoTIFF encoded DEM data.

The data is sourced from the **USGS Earth Resources Observation and Science**
(EROS) Archive, which is freely available from the
`USGS EarthExplorer <https://earthexplorer.usgs.gov>`_.

The Digital Elevation Model data was collected as part of the **Shuttle
Radar Topography Mission** (SRTM) aboard the space shuttle *Endeavour*,
February 11-22, 2000.

Endeavour orbited Earth 16 times each day during the 11-day mission,
completing 176 orbits. SRTM successfully collected radar data over 80%
of the Earth's land surface between 60°N and 56°S latitude with
data points posted every 1 arc-second (approximately 30 meters).

This SRTM sample is of *Mount Fuji*, one of Japan's
`Three Holy Mountains <https://en.wikipedia.org/wiki/Mount_Fuji>`_,
which is an active stratovolcano, located on the Japanese island of *Honshū*.

The resulting mesh contains quad cells, with the elevation data located
on the mesh nodes/points.

The elevation data is used to extrude the mesh proportionally to reveal
the topography of Mount Fuji and its surrounding landscape.

.. tags::

    domain: orography,
    filter: warp,
    load: geotiff,
    plot: camera,
    style: shading,
    widget: logo

.. attention::

    Optional package dependency :mod:`rasterio` is required.

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import pyvista as pv

import geovista as gv
from geovista.pantry import fetch_raster
import geovista.theme


def main() -> None:
    """Plot and warp GeoTIFF DEM data.

    Notes
    -----
    .. versionadded:: 0.5.0

    """
    # Fetch the example GeoTIFF file.
    fname = fetch_raster("fuji_dem.tif")

    # Plot the DEM data.
    p = gv.GeoPlotter()

    # Load the GeoTIFF image, which requires the optional package
    # dependency 'rasterio'. Note that as a convenience the unit
    # encoded within the GeoTIFF will populate the placeholder.
    mesh = gv.Transform.from_tiff(fname, extract=True, name="Elevation / {units}")

    # Warp the mesh nodes by the elevation.
    mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
    mesh.warp_by_scalar(inplace=True, factor=2e-7)

    sargs = {"fmt": "%.1f"}
    p.add_mesh(mesh, cmap="speed_r", scalar_bar_args=sargs, smooth_shading=True)
    p.add_logo_widget(fetch_raster("japan_map.png"), position=(0.8, 0.8))
    p.add_axes()
    p.add_text(
        "Mount Fuji, Digital Elevation Model GeoTIFF",
        position="upper_left",
        font_size=10,
    )

    # Define a specific camera position and orientation.
    cpos = pv.CameraPosition(
        position=(-0.6134635189209598, 0.5500672658209347, 0.5735486559145044),
        focal_point=(-0.6130746222715426, 0.5383021484428419, 0.5780820278342568),
        viewup=(-0.6616613958706443, 0.25045119061438004, 0.7067378568708134),
    )

    p.show(cpos=cpos)


if __name__ == "__main__":
    main()
