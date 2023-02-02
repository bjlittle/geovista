#!/usr/bin/env python3
"""
Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.1.0

"""

import numpy as np

import geovista as gv
import geovista.theme  # noqa: F401


def main() -> None:
    """
    This example demonstrates how to create a mesh from 2-D latitude and longitude
    rectilinear cell bounds. The resulting mesh contains quad cells.

    The data is synthetically generated and targets the mesh faces/cells.

    Note that, Natural Earth coastlines are also rendered.

    """
    # create the 2D spatial coordinates and data
    M, N = 45, 90
    lats = np.linspace(-90, 90, M + 1)
    lons = np.linspace(-180, 180, N + 1)
    mlons, mlats = np.meshgrid(lons, lats, indexing="xy")
    data = np.random.random(M * N)

    # create the mesh from the synthetic data
    name = "Synthetic Cells"
    mesh = gv.Transform.from_2d(mlons, mlats, data=data, name=name)

    # provide mesh diagnostics via logging
    gv.logger.info("%s", mesh)

    # plot the data
    plotter = gv.GeoPlotter()
    sargs = sargs = dict(title=f"{name} / 1", shadow=True)
    plotter.add_mesh(
        mesh, clim=(0, 1), cmap="tempo", scalar_bar_args=sargs, show_edges=True
    )
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        "2-D Synthetic Face Data",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.show()


if __name__ == "__main__":
    main()
