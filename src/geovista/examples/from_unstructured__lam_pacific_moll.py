#!/usr/bin/env python3
"""
Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.1.0

"""

import geovista as gv
from geovista.pantry import lam_pacific
import geovista.theme  # noqa: F401


def main() -> None:
    """
    This example demonstrates how to create a mesh from CF UGRID 1-D latitude and
    longitude unstructured cell points and connectivity. The resulting mesh
    contains quad cells.

    It uses a high-resolution Local Area Model (LAM) mesh of air potential
    temperature data located on the mesh faces/cells.

    Note that, a Natural Earth texture is rendered as a base layer, and the
    mesh is transformed to the Mollweide pseudo-cylindrical projection.

    """
    # load the sample data
    sample = lam_pacific()

    # create the mesh from the sample data
    mesh = gv.Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
    )

    # provide mesh diagnostics via logging
    gv.logger.info("%s", mesh)

    # plot the mesh
    plotter = gv.GeoPlotter(crs=(projection := "+proj=moll"))
    sargs = dict(title=f"{sample.name} / {sample.units}", shadow=True)
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
    plotter.add_axes()
    plotter.add_text(
        f"CF UGRID LAM ({projection})",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.camera.zoom(1.5)
    plotter.show()


if __name__ == "__main__":
    main()
