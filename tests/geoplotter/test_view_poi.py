# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.view_poi`."""

from __future__ import annotations

import cartopy.crs as ccrs
import numpy as np
import pytest

import geovista as gv
from geovista.geoplotter import GeoPlotter


def test_no_poi_warning():
    """Test warning raised for no POI."""
    p = GeoPlotter()
    wmsg = r"No point-of-interest \(POI\) is available or has been provided."
    with pytest.warns(UserWarning, match=wmsg):
        p.view_poi()


def test_flat_crs_camera():
    """Test that a flat scene gets a plan-view camera, not a globe camera.

    A geographic CRS other than :data:`geovista.crs.WGS84` renders a flat
    scene, so the camera must look down on the plane rather than be positioned
    on a ray from the origin - which leaves it edge-on to the mesh.
    See :issue:`2522`.

    """
    lons, lats = np.linspace(10, 30, 3), np.linspace(30, 50, 3)
    data = np.arange(4, dtype=float).reshape(2, 2)
    mesh = gv.Transform.from_1d(lons, lats, data=data)

    p = GeoPlotter(crs=ccrs.PlateCarree())
    p.add_mesh(mesh)
    p.view_poi()

    position = np.array(p.camera.position)
    focal_point = np.array(p.camera.focal_point)
    direction = focal_point - position

    assert focal_point == pytest.approx(p._poi)
    assert position[:2] == pytest.approx(focal_point[:2])
    assert direction[:2] == pytest.approx([0.0, 0.0])
    assert direction[2] < 0
