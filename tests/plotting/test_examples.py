"""Unit-tests for :mod:`geovista.examples`."""
from __future__ import annotations

from warnings import warn

import geovista as gv
from geovista.pantry import usgs_earthquakes
import geovista.theme  # noqa: F401
from geovista.examples import earthquakes


def test_earthquakes(verify_image_cache):
    """Test earthquakes example."""
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
    plotter = gv.GeoPlotter(off_screen=off_screen)
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
        "USGS M2.5+ Earthquakes, 2000-2018",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.view_xz(negative=True)
    plotter.camera.zoom(1.5)
    plotter.show()
