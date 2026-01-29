# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Image tests for :meth:`geovista.geoplotter.GeoPlotterBase.add_mesh`."""

from __future__ import annotations

import pytest

import geovista as gv

CRS = [None, "moll", "poly", "ups"]


@pytest.mark.image
@pytest.mark.parametrize("crs", CRS)
@pytest.mark.parametrize(
    "n_samples",
    [
        pytest.param(None, id="default"),
        pytest.param((None, 5), id="coarse_lat"),
        pytest.param((5, None), id="coarse_lon"),
        pytest.param((15, 10), id="lowres"),
        pytest.param((720, 360), id="highres"),
    ],
)
def test_graticule_samples(plot_nodeid, verify_image_cache, crs, n_samples):
    """Test number of samples used for graticule lines."""
    verify_image_cache.test_name = plot_nodeid

    tgt_crs = f"+proj={crs}" if crs else None
    p = gv.GeoPlotter(crs=tgt_crs)
    p.add_base_layer()
    p.add_graticule(n_samples=n_samples)
    if crs:
        # projected plots look better in the XY plane:
        p.camera_position = "xy"
    p.camera.zoom(1.5)
    p.show()


@pytest.mark.image
@pytest.mark.parametrize("crs", CRS)
@pytest.mark.parametrize("factor", [None, 0.1, 2, 100])
def test_graticule_factor(plot_nodeid, verify_image_cache, crs, factor):
    """Test graticule sample scaling factor."""
    verify_image_cache.test_name = plot_nodeid

    tgt_crs = f"+proj={crs}" if crs else None
    p = gv.GeoPlotter(crs=tgt_crs)
    p.add_base_layer()
    p.add_graticule(factor=factor)
    if crs:
        # projected plots look better in the XY plane:
        p.camera_position = "xy"
    p.camera.zoom(1.5)
    p.show()
