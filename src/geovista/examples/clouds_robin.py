#!/usr/bin/env python3
"""Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.4.0

"""
from __future__ import annotations

import cmocean
from matplotlib.colors import LinearSegmentedColormap

import geovista as gv
from geovista.pantry import cloud_amount
import geovista.theme  # noqa: F401

#: The colormap to render the clouds.
CMAP = cmocean.cm.gray

#: Multiplication factor of the zlevel for cloud surface stratification.
ZLEVEL_FACTOR: int = 75


cmaps: dict[str, LinearSegmentedColormap] = {
    "low": cmocean.tools.crop_by_percent(CMAP, 10, which="both"),
    "medium": cmocean.tools.crop_by_percent(CMAP, 30, which="both"),
    "high": cmocean.tools.crop_by_percent(CMAP, 40, which="min"),
    "very_high": cmocean.tools.crop_by_percent(CMAP, 50, which="min"),
}


def main() -> None:
    """Create meshes from 1-D latitude and longitude unstructured cell points.

    The resulting meshes contain quad cells and are constructed from CF UGRID
    unstructured cell points and connectivity.

    It uses an unstructured Met Office high-resolution LFRic C768 cubed-sphere
    of low, medium, high and very high cloud amount located on the mesh
    faces/cells.

    Note that, a threshold is applied to remove lower cloud amount cells,
    and a linear opacity transfer function is applied to a custom cropped
    colormap of each cloud amount type mesh i.e., the colormaps get lighter
    with increased altitude.

    A Natural Earth base layer is also rendered along with Natural Earth
    coastlines.

    """
    # use the pyvista linear opacity transfer function
    opacity = "linear"
    clim = (cmin := 0.3, 1.0)

    # create the plotter
    plotter = gv.GeoPlotter(crs=(projection := "+proj=robin"))

    for i, cloud in enumerate(cmaps):
        # load the sample data
        sample = cloud_amount(cloud)

        # create the mesh from the sample data
        mesh = gv.Transform.from_unstructured(
            sample.lons,
            sample.lats,
            sample.connectivity,
            data=sample.data,
            start_index=sample.start_index,
            name=cloud,
        )

        # remove cells from the mesh below the specified threshold
        mesh = mesh.threshold(cmin)

        plotter.add_mesh(
            mesh,
            clim=clim,
            opacity=opacity,
            cmap=cmaps[cloud],
            show_scalar_bar=False,
            zlevel=(i + 1) * ZLEVEL_FACTOR,
        )

    # force zlevel alignment of coastlines and base layer
    plotter.add_base_layer(texture=gv.natural_earth_1(), zlevel=0)
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        f"Low, Medium, High & Very High Cloud Amount ({projection})",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.camera.zoom(1.5)
    plotter.show()


if __name__ == "__main__":
    main()
