# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotterBase.add_mesh`."""

from __future__ import annotations

import pyproj
import pytest

import geovista as gv
from geovista.crs import WGS84, from_wkt
from geovista.transform import transform_mesh


@pytest.mark.image
def test_wgs84_to_wgs84(plot_nodeid, verify_image_cache, lfric_sst):
    """Test noop transformation for WGS84."""
    verify_image_cache.test_name = plot_nodeid
    assert from_wkt(lfric_sst) == WGS84
    p = gv.GeoPlotter()
    assert p.crs == WGS84
    _ = p.add_mesh(lfric_sst)
    p.camera.zoom(1.5)
    p.show()


@pytest.mark.image
def test_wgs84_to_eqc(plot_nodeid, verify_image_cache, lfric_sst):
    """Test transformation from WGS84 to Equidistant Cylindrical."""
    verify_image_cache.test_name = plot_nodeid
    assert from_wkt(lfric_sst) == WGS84
    tgt_crs = "+proj=eqc"
    p = gv.GeoPlotter(crs=tgt_crs)
    assert p.crs == pyproj.CRS.from_user_input(tgt_crs)
    _ = p.add_mesh(lfric_sst)
    p.view_xy()
    p.camera.zoom(1.5)
    p.show()


@pytest.mark.image
def test_eqc_to_eqc(plot_nodeid, verify_image_cache, lfric_sst):
    """Test noop transformation for Equidistant Cylindrical."""
    verify_image_cache.test_name = plot_nodeid
    assert from_wkt(lfric_sst) == WGS84
    tgt_crs = "+proj=eqc"
    lfric_eqc = transform_mesh(lfric_sst, tgt_crs=tgt_crs)
    crs = from_wkt(lfric_eqc)
    assert crs == pyproj.CRS.from_user_input(tgt_crs)
    p = gv.GeoPlotter(crs=crs)
    assert p.crs == crs
    _ = p.add_mesh(lfric_eqc)
    p.view_xy()
    p.camera.zoom(1.5)
    p.show()


@pytest.mark.image
def test_eqc_to_wgs84(plot_nodeid, verify_image_cache, lfric_sst):
    """Test transformation from Robinson to WGS84."""
    verify_image_cache.test_name = plot_nodeid
    assert from_wkt(lfric_sst) == WGS84
    tgt_crs = "+proj=eqc"
    lfric_eqc = transform_mesh(lfric_sst, tgt_crs=tgt_crs)
    crs = from_wkt(lfric_eqc)
    assert crs == pyproj.CRS.from_user_input(tgt_crs)
    p = gv.GeoPlotter()
    assert p.crs == WGS84
    _ = p.add_mesh(lfric_eqc)
    p.camera.zoom(1.5)
    p.show()
