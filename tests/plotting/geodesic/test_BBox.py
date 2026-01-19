# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geodesic.BBox`."""

from __future__ import annotations

import pytest

import geovista as gv
from geovista.geodesic import BBox, panel


@pytest.mark.image
def test_outline(plot_nodeid, verify_image_cache):
    """Test edge outline of bounding-box manifold."""
    verify_image_cache.test_name = plot_nodeid
    p = gv.GeoPlotter()
    bbox = panel("arctic")
    p.add_mesh(bbox.mesh, color="orange")
    p.add_mesh(bbox.outline, color="yellow", line_width=3)
    p.add_base_layer(texture=gv.natural_earth_1(), opacity=0.5)
    p.view_vector(vector=(1, 1, 0))
    p.camera.zoom(1.5)
    p.show()


@pytest.mark.image
def test___call__(plot_nodeid, verify_image_cache, lfric_sst):
    """Test callable enclosed behaviour."""
    verify_image_cache.test_name = plot_nodeid
    p = gv.GeoPlotter()
    bbox = panel("africa")
    p.add_mesh(bbox(lfric_sst))
    p.view_yz()
    p.camera.zoom(1.2)
    p.show()


@pytest.mark.image
def test_enclosed_point_eqc(
    plot_nodeid, verify_image_cache, africa_corners, lfric_sst_eqc
):
    """Test cross-crs manifold with point preference."""
    verify_image_cache.test_name = plot_nodeid
    lons, lats = africa_corners
    bbox = BBox(lons, lats)
    region = bbox.enclosed(lfric_sst_eqc, preference="point")
    p = gv.GeoPlotter(crs="+proj=eqc")
    _ = p.add_mesh(bbox.boundary(), line_width=2, color="orange", zlevel=1)
    _ = p.add_mesh(region, show_scalar_bar=False)
    p.view_xy()
    p.camera.zoom(1.3)
    p.show()


@pytest.mark.image
def test_enclosed_cell_eqc(
    plot_nodeid, verify_image_cache, africa_corners, lfric_sst_eqc
):
    """Test cross-crs manifold with cell preference."""
    verify_image_cache.test_name = plot_nodeid
    lons, lats = africa_corners
    bbox = BBox(lons, lats)
    region = bbox.enclosed(lfric_sst_eqc, preference="cell")
    p = gv.GeoPlotter(crs="+proj=eqc")
    _ = p.add_mesh(bbox.boundary(), line_width=2, color="orange", zlevel=1)
    _ = p.add_mesh(region, show_scalar_bar=False)
    p.view_xy()
    p.camera.zoom(1.3)
    p.show()


@pytest.mark.image
def test_enclosed_center_eqc(plot_nodeid, verify_image_cache, lfric_sst_eqc):
    """Test cross-crs manifold with center preference."""
    verify_image_cache.test_name = plot_nodeid
    bbox = panel("africa")
    region = bbox.enclosed(lfric_sst_eqc, preference="center")
    p = gv.GeoPlotter(crs="+proj=eqc")
    _ = p.add_mesh(bbox.boundary(), line_width=2, color="orange", zlevel=1)
    _ = p.add_mesh(region, show_scalar_bar=False)
    p.view_xy()
    p.camera.zoom(1.3)
    p.show()
