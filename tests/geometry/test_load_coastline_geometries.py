# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.geometry.test_load_coastline_geometries`."""

from __future__ import annotations

import numpy as np

from geovista.common import COASTLINES_RESOLUTION
from geovista.geometry import load_coastline_geometries as load


def test_defaults(mocker):
    """Test expected defaults are honoured."""
    import cartopy.io.shapereader as shp  # noqa: PLC0415

    spy = mocker.spy(shp, "natural_earth")
    _ = load()
    spy.assert_called_once_with(
        resolution=COASTLINES_RESOLUTION, category="physical", name="coastline"
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
