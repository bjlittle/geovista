"""Unit-tests for :func:`geovista.geometry.test_load_coastline_geometries`."""
import numpy as np

from geovista.geometry import COASTLINE_RESOLUTION
from geovista.geometry import load_coastline_geometries as load


def test_defaults(mocker):
    """Test expected defaults are honoured."""
    import cartopy.io.shapereader as shp

    spy = mocker.spy(shp, "natural_earth")
    _ = load()
    spy.assert_called_once_with(
        resolution=COASTLINE_RESOLUTION, category="physical", name="coastline"
    )


def test(resolution):
    """Test structure of line geometries from natural earth coastlines shapefile."""
    geoms = load(resolution=resolution)
    assert len(geoms)
    for geom in geoms:
        assert geom.ndim == 2
        assert geom.shape[-1] == 3
        xs, ys, zs = geom[:, 0], geom[:, 1], geom[:, 2]
        assert np.sum(zs) == 0
        ymin, ymax = ys.min(), ys.max()
        assert -90 <= ymin <= 90
        assert -90 < ymax <= 90
        xmin, xmax = xs.min(), xs.max()
        assert -180 <= xmin <= 180
        assert -180 <= xmax <= 180
