# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.transform.transform_mesh`."""

from __future__ import annotations

import pyproj
import pytest
import pyvista as pv

from geovista.crs import WGS84, from_wkt
from geovista.transform import transform_mesh


@pytest.mark.image
def test_wgs84_to_wgs84(plot_nodeid, verify_image_cache, lfric_sst):
    """Test noop transformation for WGS84."""
    verify_image_cache.test_name = plot_nodeid
    assert from_wkt(lfric_sst) == WGS84
    mesh = transform_mesh(lfric_sst, tgt_crs=WGS84)
    assert mesh is lfric_sst
    p = pv.Plotter()
    _ = p.add_mesh(mesh)
    p.camera.zoom(1.5)
    p.show()


@pytest.mark.image
def test_wgs84_to_eqc(plot_nodeid, verify_image_cache, lfric_sst):
    """Test transformation from WGS84 to Equidistant Cylindrical."""
    verify_image_cache.test_name = plot_nodeid
    assert from_wkt(lfric_sst) == WGS84
    tgt_crs = "+proj=eqc"
    mesh = transform_mesh(lfric_sst, tgt_crs=tgt_crs)
    assert from_wkt(mesh) == pyproj.CRS.from_user_input(tgt_crs)
    p = pv.Plotter()
    _ = p.add_mesh(mesh)
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
    mesh = transform_mesh(lfric_eqc, tgt_crs=crs)
    assert mesh is lfric_eqc
    p = pv.Plotter()
    _ = p.add_mesh(mesh)
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
    assert from_wkt(lfric_eqc) == pyproj.CRS.from_user_input(tgt_crs)
    mesh = transform_mesh(lfric_eqc, tgt_crs=WGS84)
    assert from_wkt(mesh) == WGS84
    p = pv.Plotter()
    _ = p.add_mesh(mesh)
    p.camera.zoom(1.5)
    p.show()
