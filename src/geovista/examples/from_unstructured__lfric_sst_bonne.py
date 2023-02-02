#!/usr/bin/env python3
"""
Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.1.0

"""

import geovista as gv
from geovista.pantry import lfric_sst
import geovista.theme  # noqa: F401


def main() -> None:
    """
    This example demonstrates how to create a mesh from CF UGRID 1-D latitude and
    longitude unstructured cell points and connectivity. The resulting mesh
    contains quad cells.

    It uses an unstructured Met Office LFRic C48 cubed-sphere of surface temperature
    data located on the mesh faces/cells.

    Note that, a threshold is also applied to remove land NaN cells, and a
    Natural Earth texture is rendered as a base layer. The mesh is also
    transformed to the Bonne projection.

    """
    # load the sample data
    sample = lfric_sst()

    # create the mesh from the sample data
    mesh = gv.Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
    )

    # provide mesh diagnostics via logging
    gv.logger.info("%s", mesh)

    # remove cells from the mesh with nan values
    mesh = mesh.threshold()

    # plot the mesh
    plotter = gv.GeoPlotter(crs=(projection := "+proj=bonne +lat_1=10"))
    sargs = dict(title=f"{sample.name} / {sample.units}", shadow=True)
    plotter.add_mesh(mesh, show_edges=True, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.natural_earth_1())
    plotter.add_axes()
    plotter.add_text(
        f"LFRic C48 Unstructured Cube-Sphere ({projection})",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.camera.zoom(1.5)
    plotter.show()


if __name__ == "__main__":
    main()
