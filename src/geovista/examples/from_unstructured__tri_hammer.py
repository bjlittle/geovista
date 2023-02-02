#!/usr/bin/env python3
"""
Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.1.0

"""

import geovista as gv
from geovista.pantry import ww3_global_tri
import geovista.theme  # noqa: F401


def main() -> None:
    """
    This example demonstrates how to create a mesh from 1-D latitude and longitude
    unstructured cell points and connectivity. The resulting mesh contains
    triangular cells.

    It uses a WAVEWATCH III (WW3) unstructured triangular mesh sea surface
    wave significant height data located on mesh nodes/points.

    Note that, a threshold is also applied to remove land NaN cells, and a
    Natural Earth texture is rendered as a base layer. The mesh is also
    transformed to the Hammer & Eckert-Greifendorff azimuthal projection.
    As data is located on the mesh nodes/points, these values are interpolated
    across the mesh faces/cells.

    """
    # load the sample data
    sample = ww3_global_tri()

    # create the mesh from the sample data
    mesh = gv.Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
        name=sample.name,
    )

    # provide mesh diagnostics via logging
    gv.logger.info("%s", mesh)

    # plot the mesh
    plotter = gv.GeoPlotter(crs=(projection := "+proj=hammer"))
    sargs = dict(title=f"{sample.name} / {sample.units}", shadow=True)
    plotter.add_mesh(mesh, show_edges=True, scalar_bar_args=sargs, scalars=sample.name)
    plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
    plotter.add_axes()
    plotter.add_text(
        f"WW3 Triangular Mesh ({projection})",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.camera.zoom(1.5)
    plotter.show()


if __name__ == "__main__":
    main()
