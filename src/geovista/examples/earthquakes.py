#!/usr/bin/env python3
"""Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.4.0

"""
from __future__ import annotations

from warnings import warn

import geovista as gv
from geovista.common import to_cartesian
from geovista.pantry import usgs_earthquakes
import geovista.theme


def main() -> None:
    """Create a point cloud from a USGS earthquakes dataset.

    The resulting render contains a point cloud of M2.5+ earthquakes along
    with a Natural Earth base layer along and Natural Earth coastlines.

    The earthquakes dataset is sourced from the
    [USGS Earthquake Hazards Program](https://www.usgs.gov/programs/earthquake-hazards)
    and [pre-processed](https://github.com/holoviz/holoviz/blob/main/examples/data/preprocessing/earthquake_data.py)
    as part of this
    [HoloViz Tutorial](https://holoviz.org/tutorial/Overview.html#the-holoviz-tutorial).

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

    # convert coordinate to cartesian
    points = to_cartesian(lons=sample.lons, lats=sample.lats)

    # plot the mesh
    plotter = gv.GeoPlotter()
    sargs = {"title": "Magnitude", "shadow": True}
    plotter.add_points(
        points,
        cmap="fire_r",
        render_points_as_spheres=True,
        scalars=sample.data,
        point_size=5,
        scalar_bar_args=sargs,
    )
    plotter.add_base_layer(texture=gv.natural_earth_1(), zlevel=0)
    plotter.add_graticule()
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        "USGS M2.5+ Earthquakes (2000-2018)",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xz(negative=True)
    plotter.camera.zoom(1.5)
    plotter.show()


if __name__ == "__main__":
    main()
