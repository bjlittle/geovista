#!/usr/bin/env python3
"""Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

import geovista as gv
from geovista.pantry import icosahedral
import geovista.theme  # noqa: F401


def main() -> None:
    """Create a mesh from 2-D latitude and longitude unstructured cell bounds.

    The resulting mesh contains 6-sided (hexagonal) cells.

    It uses surface air pressure data from the DYNAMICO project, a new dynamical core
    for the Laboratoire de Météorologie Dynamique (LMD-Z), the atmospheric General
    Circulation Model (GCM) part of Institut Pierre-Simon Laplace (IPSL-CM) Earth
    System Model. The data targets the mesh faces/cells.

    Note that, a graticule and Natural Earth coastlines are rendered, and the
    mesh is also transformed to the Polyconic pseudo-conical projection.

    """
    # load the sample data
    sample = icosahedral()

    # create the mesh from the sample data
    mesh = gv.Transform.from_unstructured(sample.lons, sample.lats, data=sample.data)

    # provide mesh diagnostics via logging
    gv.logger.info("%s", mesh)

    # plot the mesh
    crs = "+proj=poly"
    plotter = gv.GeoPlotter(crs=crs)
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(mesh, scalar_bar_args=sargs)
    plotter.add_coastlines()
    plotter.add_graticule()
    plotter.add_axes()
    plotter.add_text(
        f"DYNAMICO Icosahedral ({crs})",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.show()


if __name__ == "__main__":
    main()
