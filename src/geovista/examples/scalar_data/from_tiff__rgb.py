#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
GeoTIFF RGB
-----------

This example demonstrates how to render an
`OGC GeoTIFF <https://www.ogc.org/standards/geotiff/>`_ RGB image as a
geolocated mesh.

📋 Summary
^^^^^^^^^^

Creates a mesh from a GeoTIFF encoded RGB image.

The resulting mesh contains quad cells.

The GeoTIFF RGB image is first pre-processed using :func:`rasterio.features.sieve`
to remove several unwanted masked regions within the interior of the image, which
are due to a lack of dynamic range in the ``uint8`` image data.

Note that the RGB image pixel data is located on the mesh nodes/points.

The masked RGB pixels are then removed by extracting only mesh cells with no
masked points.

.. tags::

    load: geotiff,
    style: lighting

.. attention::

    Optional package dependency :mod:`rasterio` is required.

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import geovista as gv
from geovista.pantry import fetch_raster
import geovista.theme


def main() -> None:
    """Plot a GeoTIFF RGB image.

    Notes
    -----
    .. versionadded:: 0.5.0

    """
    # Fetch the example GeoTIFF file.
    fname = fetch_raster("bahamas_rgb.tif")

    # Plot the RGB image.
    p = gv.GeoPlotter()

    # Load the GeoTIFF image, which requires the optional package
    # dependency 'rasterio'.
    mesh = gv.Transform.from_tiff(fname, rgb=True, sieve=True, extract=True)

    p.add_mesh(mesh, lighting=False, rgb=True)
    p.add_axes()
    p.add_text(
        "Bahamas, RGB GeoTIFF",
        position="upper_left",
        font_size=10,
    )
    p.view_xz()
    p.camera.zoom(1.3)
    p.show()


if __name__ == "__main__":
    main()
