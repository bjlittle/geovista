#!/usr/bin/env python3
"""Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.4.0

"""
from __future__ import annotations

from warnings import warn

import geovista as gv
from geovista.pantry import usgs_earthquakes
import geovista.theme  # noqa: F401


def main() -> None:
    """Create a point cloud from a USGS earthquakes dataset.

    The resulting render contains a point cloud of M2.5+ earthquakes along
    with a Natural Earth base layer and Natural Earth coastlines. The point
    cloud is also transformed to the Winkel I pseudo-cylindrical projection.

    The earthquakes dataset is sourced from the
    `USGS Earthquake Hazards Program <https://www.usgs.gov/programs/earthquake-hazards>`_
    and
    `pre-processed <https://github.com/holoviz/holoviz/blob/main/examples/data/preprocessing/earthquake_data.py>`_
    as part of this
    `HoloViz Tutorial <https://holoviz.org/tutorial/Overview.html#the-holoviz-tutorial>`_.

    =========  =============================================================  =========================
    Magnitude  Earthquake Effects                                             Estimated Number per Year
    =========  =============================================================  =========================
    <=2.5      Usually not felt, but can be recorded by seismograph.          Millions
    2.5 - 5.4  Often felt, but only causes minor damage.                      500,000
    5.5 - 6.0  Slight damage to buildings and other structures.               350
    6.1 - 6.9  May cause a lot of damage in very populated areas.             100
    7.0 - 7.9  Major earthquake. Serious damage.                              10-15
    >=8.0      Great earthquake. Can destroy communities near the epicenter.  One every year or two
    =========  =============================================================  =========================

    `Reference <https://www.mtu.edu/geo/community/seismology/learn/earthquake-measure/magnitude/>`_.

    """
    # load sample data, which requires the optional package
    # dependencies 'pandas' and 'fastparquet'
    try:
        sample = usgs_earthquakes()
    except ImportError:
        wmsg = (
            "Missing optional dependencies 'pandas' and 'fastparquet' are "
            "required for the 'earthquakes' example. Use pip or conda to "
            "install them."
        )
        warn(wmsg, stacklevel=2)
        return

    # plot the mesh
    plotter = gv.GeoPlotter(crs=(projection := "+proj=wink1 +lon_0=180"))
    sargs = {"title": "Magnitude", "shadow": True}
    plotter.add_points(
        xs=sample.lons,
        ys=sample.lats,
        cmap="fire_r",
        render_points_as_spheres=True,
        scalars=sample.data,
        point_size=5,
        scalar_bar_args=sargs,
    )
    # force zlevel alignment of coastlines and base layer
    plotter.add_base_layer(texture=gv.natural_earth_1(), zlevel=0)
    plotter.add_graticule()
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        f"USGS M2.5+ Earthquakes, 2000-2018 ({projection})",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xy()
    plotter.camera.zoom(1.5)
    plotter.show()


if __name__ == "__main__":
    main()
