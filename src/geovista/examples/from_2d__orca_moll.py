#!/usr/bin/env python3
"""
Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.1.0

"""

import geovista as gv
from geovista.pantry import um_orca2
import geovista.theme  # noqa: F401


def main() -> None:
    """
    This example demonstrates how to create a mesh from 2-D latitude and longitude
    curvilinear cell bounds. The resulting mesh contains quad cells.

    It uses an ORCA2 global ocean with tri-polar model grid with sea water
    potential temperature data. The data targets the mesh faces/cells.

    Note that, a threshold is also applied to remove land NaN cells, and a
    Natural Earth texture is rendered as a base layer. The mesh is also
    transformed to the Mollweide pseudo-cylindrical projection.

    """
    # load sample data
    sample = um_orca2()

    # create the mesh from the sample data
    mesh = gv.Transform.from_2d(sample.lons, sample.lats, data=sample.data)

    # provide mesh diagnostics via logging
    gv.logger.info("%s", mesh)

    # remove cells from the mesh with nan values
    mesh = mesh.threshold()

    # plot the mesh
    plotter = gv.GeoPlotter(crs=(projection := "+proj=moll"))
    sargs = dict(title=f"{sample.name} / {sample.units}", shadow=True)
    plotter.add_mesh(mesh, show_edges=True, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.natural_earth_1())
    plotter.add_axes()
    plotter.add_text(
        f"ORCA ({projection})",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.camera.zoom(1.5)
    plotter.show()


if __name__ == "__main__":
    main()
