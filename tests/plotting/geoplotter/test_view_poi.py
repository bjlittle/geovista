# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotterBase.view_poi`."""

from __future__ import annotations

import pytest

import geovista as gv

CRS = [None, "eqc", "moll", "poly"]


@pytest.mark.image
@pytest.mark.parametrize("crs", CRS)
def test_lam_polar(crs, plot_nodeid, lam_polar, verify_image_cache):
    """Test Polar LAM POI as first rendered mesh."""
    verify_image_cache.test_name = plot_nodeid
    p = gv.GeoPlotter(crs=f"+proj={crs}" if crs else crs)
    p.add_mesh(lam_polar, show_edges=True, zlevel=10)
    p.view_poi()
    p.add_base_layer(texture=gv.natural_earth_1())
    p.show()


@pytest.mark.image
@pytest.mark.parametrize("crs", CRS)
def test_lam_polar_post(crs, plot_nodeid, lam_polar, verify_image_cache):
    """Test Polar LAM POI as first rendered mesh."""
    verify_image_cache.test_name = plot_nodeid
    p = gv.GeoPlotter(crs=f"+proj={crs}" if crs else crs)
    p.add_base_layer(texture=gv.natural_earth_1())
    p.add_mesh(lam_polar, show_edges=True, zlevel=10)
    p.view_poi()
    p.show()


@pytest.mark.image
@pytest.mark.parametrize("crs", CRS)
def test_lam_polar_offset(crs, plot_nodeid, lam_polar, verify_image_cache):
    """Test Polar LAM POI offset."""
    verify_image_cache.test_name = plot_nodeid
    p = gv.GeoPlotter(crs=f"+proj={crs}" if crs else crs)
    p.add_mesh(lam_polar, show_edges=True, zlevel=10)
    p.view_poi(-90, 80)
    p.add_base_layer(texture=gv.natural_earth_1())
    p.show()


@pytest.mark.image
@pytest.mark.parametrize(
    ("x", "y"),
    [
        (0, 0),
        (30, None),
        (-30, None),
        (None, 30),
        (None, 60),
    ],
)
def test_lam_uk_defaults(x, y, plot_nodeid, lam_uk, verify_image_cache):
    """Test UK LAM POI with spatial defaults."""
    verify_image_cache.test_name = plot_nodeid
    p = gv.GeoPlotter()
    p.add_mesh(lam_uk, show_edges=True, zlevel=10)
    p.add_base_layer(texture=gv.natural_earth_1())
    p.view_poi(x=x, y=y)
    p.show()


@pytest.mark.image
@pytest.mark.parametrize("crs", CRS)
def test_lam_uk(crs, plot_nodeid, lam_uk, verify_image_cache):
    """Test UK LAM POI as first rendered mesh."""
    verify_image_cache.test_name = plot_nodeid
    p = gv.GeoPlotter(crs=f"+proj={crs}" if crs else crs)
    p.add_mesh(lam_uk, show_edges=True, zlevel=10)
    p.view_poi()
    p.add_base_layer(texture=gv.natural_earth_1())
    p.show()


@pytest.mark.image
@pytest.mark.parametrize("crs", CRS)
def test_lam_uk_post(crs, plot_nodeid, lam_uk, verify_image_cache):
    """Test UK LAM POI as last rendered mesh."""
    verify_image_cache.test_name = plot_nodeid
    p = gv.GeoPlotter(crs=f"+proj={crs}" if crs else crs)
    p.add_base_layer(texture=gv.natural_earth_1())
    p.add_mesh(lam_uk, show_edges=True, zlevel=10)
    p.view_poi()
    p.show()
