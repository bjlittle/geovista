#!/usr/bin/env python3
"""Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

import geovista as gv
from geovista.pantry import lfric_sst
import geovista.theme  # noqa: F401


def main() -> None:
    """Create a mesh from 1-D latitude and longitude unstructured cell points.

    The resulting mesh contains quad cells and is constructed from CF UGRID unstructured
    cell points and connectivity.

    It uses an unstructured Met Office LFRic C48 cubed-sphere of surface temperature
    data located on the mesh faces/cells.

    Note that, a threshold is also applied to remove land NaN cells. A Natural Earth
    base layer is also rendered along with Natural Earth coastlines and a graticule.
    The mesh is also transformed to the Bonne projection.

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
    plotter = gv.GeoPlotter(crs=(projection := "+proj=bonne +lat_1=10 +lon_0=180"))
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, show_edges=True, scalar_bar_args=sargs)
    plotter.add_base_layer(texture=gv.natural_earth_1())
    plotter.add_coastlines()
    plotter.add_graticule()
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
