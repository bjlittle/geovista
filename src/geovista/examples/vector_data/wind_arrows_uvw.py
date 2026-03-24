#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Wind Arrows 3D
--------------

This example demonstrates how to render 3D wind vectors.

📋 Summary
^^^^^^^^^^

The sample data contains a longitude and latitude point cloud, along with sample
winds provided in the form of three separate eastward (``U``), northward (``V``),
and upward (``W``) vector components.

The vector components are measured relative to each spatial sample point in the
point cloud.

No connectivity is provided within the sample data, so each point is a
separate location in a field of scattered points, and each point has an
associated wind vector independent of the others. We use the
:meth:`geovista.bridge.Transform.from_points` method, passing the winds with
the ``vectors`` keyword, along with the associated sample points to generate
a point cloud mesh with attached vectors.

The wind arrows are generated from this point cloud mesh via the
:meth:`pyvista.DataSetFilters.glyph` method, which scales each arrow in size and
colour relative to the magnitude of its associated wind vector.

Note that, we use all 3 wind components and amplify the upward (``W``) vector
component by a considerable factor for illustrative purposes. Vertical winds are
generally much smaller in magnitude, and tend not to be very visible otherwise.

.. tags::

    experimental 🧪,
    component: graticule, component: texture, component: vectors,
    domain: meteorology,
    filter: glyph,
    load: vectors,
    version: 0.6.0

----

"""  # noqa: D205,D212,D400

from __future__ import annotations

import pyvista as pv

import geovista as gv
from geovista.pantry.data import lfric_winds
import geovista.theme


def main() -> None:
    """Plot 3D wind arrows (UVW).

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    # Load the sample data.
    sample = lfric_winds()

    # Provide all three components, but with exaggerated upwards scaling bias.
    vectors = (sample.u, sample.v, sample.w * 1500.0)

    # Create the point cloud mesh with attached wind vectors from the
    # sample eastward (u), northward (v), and upward (w) components.
    mesh = gv.Transform.from_points(
        sample.lons,
        sample.lats,
        vectors=vectors,
        radius=1.1,
    )

    # Create a new mesh containing arrow glyphs, from the mesh vectors.
    # NOTE: choose an overall scaling factor to make the arrows a reasonable size.

    # Generate a mesh containing arrow glyphs from the wind vectors. Apply an
    # overall scaling factor to make the arrows a reasonable size, and colour
    # the arrows relative to their associated vector magnitude.
    arrows = mesh.glyph(factor=0.02, color_mode="vector")

    # Now render the plotter scene.
    p = gv.GeoPlotter()
    sargs = {"title": f"{sample.name} / {sample.units}"}
    p.add_mesh(arrows, cmap="inferno", scalar_bar_args=sargs)
    p.add_base_layer(texture=gv.natural_earth_hypsometric())
    p.add_graticule()

    # Define a specific camera position and orientation.
    cpos = pv.CameraPosition(
        position=(0.69178, -3.06569, 0.43180),
        focal_point=(0.41358, 0.07363, 0.50912),
        viewup=(0.80885, 0.05726, 0.58522),
    )
    p.camera.zoom(1.3)

    p.add_axes()
    p.show(cpos=cpos)


if __name__ == "__main__":
    main()
