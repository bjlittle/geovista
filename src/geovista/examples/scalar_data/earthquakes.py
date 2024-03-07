#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Earthquakes
-----------

This example demonstrates how to render scalar points-of-interest.

📋 Summary
^^^^^^^^^^

Creates a point cloud from a USGS earthquakes dataset.

The resulting render contains a point cloud of M2.5+ earthquakes along
with a Natural Earth base layer and Natural Earth coastlines.

The earthquakes dataset is sourced from the
`USGS Earthquake Hazards Program <https://www.usgs.gov/programs/earthquake-hazards>`_
and
`pre-processed <https://github.com/holoviz/holoviz/blob/main/examples/data/preprocessing/earthquake_data.py>`_
as part of this
`HoloViz Tutorial <https://holoviz.org/tutorial/Overview.html#the-holoviz-tutorial>`_.

=============  =============================================================  =========================
Magnitude      Earthquake Effects                                             Estimated Number per Year
=============  =============================================================  =========================
**<=2.5**      Usually not felt, but can be recorded by seismograph.          Millions
**2.5 - 5.4**  Often felt, but only causes minor damage.                      500,000
**5.5 - 6.0**  Slight damage to buildings and other structures.               350
**6.1 - 6.9**  May cause a lot of damage in very populated areas.             100
**7.0 - 7.9**  Major earthquake. Serious damage.                              10-15
**>=8.0**      Great earthquake. Can destroy communities near the epicenter.  One every year or two
=============  =============================================================  =========================

See `reference <https://www.mtu.edu/geo/community/seismology/learn/earthquake-measure/magnitude/>`_
for further details.

.. attention::

   Optional package dependencies `pandas <https://pandas.pydata.org/docs/>`_ and
   `fastparquet <https://fastparquet.readthedocs.io/en/stable>`_ are required.

.. tags:: Coastlines, Globe, Graticule, Points, Texture

----

"""  # noqa: D205,D212,D400,E501

from __future__ import annotations

import geovista as gv
from geovista.pantry.data import usgs_earthquakes
import geovista.theme


def main() -> None:
    """Plot points-of-interest for USGS earthquakes.

    Notes
    -----
    .. versionadded:: 0.4.0

    """
    # Load sample data, which requires the optional package
    # dependencies 'fastparquet' and 'pandas'.
    sample = usgs_earthquakes()

    # Plot the points.
    plotter = gv.GeoPlotter()
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
    # Force zlevel alignment of coastlines and base layer.
    plotter.add_base_layer(texture=gv.natural_earth_1(), zlevel=0)
    plotter.add_graticule()
    plotter.add_coastlines()
    plotter.add_axes()
    plotter.add_text(
        "USGS M2.5+ Earthquakes, 2000-2018",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xz(negative=True)
    plotter.camera.zoom(1.3)
    plotter.show()


if __name__ == "__main__":
    main()
