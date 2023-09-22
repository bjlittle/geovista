"""Unit-tests for :class:`geovista.examples`."""
import pytest

import geovista as gv
from geovista.pantry import usgs_earthquakes

pytestmark = pytest.mark.skip_plotting


@pytest.fixture(autouse=True)
def verify_image_cache_wrapper(verify_image_cache):
    """Verify image cache wrapper."""
    return verify_image_cache


def test_earthquakes(verify_image_cache):
    """Test earthquakes."""
    sample = usgs_earthquakes()
    plotter = gv.GeoPlotter(off_screen=True)
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
