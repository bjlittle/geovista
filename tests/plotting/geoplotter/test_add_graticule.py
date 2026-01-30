# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Image tests for :meth:`geovista.geoplotter.GeoPlotterBase.add_mesh`."""

from __future__ import annotations

import pytest

import geovista as gv


@pytest.mark.image
@pytest.mark.parametrize(
    "n_samples", [(12, 6), (None, 6)], ids=["coarse", "coarse_lat"]
)
def test_graticule_samples(plot_nodeid, verify_image_cache, n_samples):
    """Test number of samples used for graticule lines."""
    verify_image_cache.test_name = plot_nodeid

    tgt_crs = "+proj=poly"
    p = gv.GeoPlotter(crs=tgt_crs)
    p.add_base_layer()
    p.add_graticule(n_samples=n_samples)
    p.camera_position = "xy"
    p.camera.zoom(1.5)
    p.show()


@pytest.mark.image
@pytest.mark.parametrize("factor", [0.1, 10])
def test_graticule_factor(plot_nodeid, verify_image_cache, factor):
    """Test graticule sample scaling factor."""
    verify_image_cache.test_name = plot_nodeid

    tgt_crs = "+proj=poly"
    p = gv.GeoPlotter(crs=tgt_crs)
    p.add_base_layer()
    p.add_graticule(factor=factor)
    p.camera_position = "xy"
    p.camera.zoom(1.5)
    p.show()
