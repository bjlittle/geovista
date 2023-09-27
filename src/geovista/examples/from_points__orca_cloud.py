"""Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.2.0

"""
from __future__ import annotations

import geovista as gv
from geovista.pantry import um_orca2_gradient
from geovista.samples import ZLEVEL_SCALE_CLOUD
import geovista.theme  # noqa: F401


def main() -> None:
    """Create a point-cloud from 1-D latitude, longitude and z-levels.

    The resulting mesh contains only points.

    Based on a curvilinear ORCA2 global ocean with tri-polar model grid of
    sea water potential temperature data, which has been reduced to a limited
    area and pre-filtered for temperature gradients.

    Note that, Natural Earth coastlines are also rendered along with a Natural
    Earth base layer with opacity.

    """
    # load the sample data
    sample = um_orca2_gradient()

    # create the point-cloud from the sample data
    cloud = gv.Transform.from_points(
        sample.lons,
        sample.lats,
        data=sample.zlevel,
        name=sample.name,
        zlevel=-sample.zlevel,
        zscale=ZLEVEL_SCALE_CLOUD,
    )

    # provide cloud diagnostics via logging
    gv.logger.info("%s", cloud)

    # plot the point-cloud
    plotter = gv.GeoPlotter()
    sargs = {"title": f"{sample.name} / {sample.units}", "shadow": True}
    plotter.add_mesh(
        cloud,
        cmap="deep",
        point_size=5,
        scalar_bar_args=sargs,
        render_points_as_spheres=True,
    )
    plotter.add_coastlines(color="black")
    # force zlevel alignment of coastlines and base layer
    plotter.add_base_layer(texture=gv.natural_earth_1(), opacity=0.5, zlevel=0)
    plotter.add_axes()
    plotter.view_yz()
    plotter.add_text(
        "ORCA Point-Cloud (10m Coastlines)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.show()


if __name__ == "__main__":
    main()
