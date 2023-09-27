#!/usr/bin/env python3
"""Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

from pyproj import CRS

import geovista as gv
from geovista.common import cast_UnstructuredGrid_to_PolyData as cast
from geovista.pantry import um_orca2
import geovista.theme  # noqa: F401
from geovista.transform import transform_mesh


def main() -> None:
    """Create a mesh from 2-D latitude and longitude curvilinear cell bounds.

    The resulting mesh contains quad cells.

    It uses an ORCA2 global ocean with tri-polar model grid with sea water
    potential temperature data. The data targets the mesh faces/cells.

    Note that, a threshold is applied to remove land NaN cells, before the
    mesh is then transformed to the Mollweide pseudo-cylindrical projection
    and extruded to give depth to the projected surface. Finally, 10m
    resolution Natural Earth coastlines are also rendered.

    """
    # load sample data
    sample = um_orca2()

    # create the mesh from the sample data
    mesh = gv.Transform.from_2d(sample.lons, sample.lats, data=sample.data)

    # provide mesh diagnostics via logging
    gv.logger.info("%s", mesh)

    # create the target coordinate reference system
    crs = CRS.from_user_input(projection := "+proj=moll")

    # remove cells from the mesh with nan values
    mesh = cast(mesh.threshold())

    # transform and extrude the mesh
    mesh = transform_mesh(mesh, crs)
    mesh.extrude((0, 0, -1000000), capping=True, inplace=True)

    # plot the mesh
    plotter = gv.GeoPlotter(crs=crs)
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_coastlines(color="black")
    plotter.add_axes()
    plotter.add_text(
        f"ORCA ({projection} extrude)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.camera.zoom(1.5)
    plotter.show()


if __name__ == "__main__":
    main()
