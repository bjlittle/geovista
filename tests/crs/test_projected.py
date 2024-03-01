# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.crs.projected`."""

from __future__ import annotations

from pyproj import CRS
import pyvista as pv

from geovista.crs import WGS84, has_wkt, projected, to_wkt


def test_planar__no_crs():
    """Test that the mesh is projected."""
    mesh = pv.Plane()
    assert projected(mesh)


def test_planer__with_crs():
    """Test that the mesh CRS is used over the geometry heuristic."""
    mesh = pv.Plane()
    to_wkt(mesh, WGS84)
    assert not projected(mesh)


def test_non_planar__no_crs(sphere):
    """Test that the mesh is not projected."""
    assert not projected(sphere)


def test_non_planer__with_crs(sphere):
    """Test that the mesh CRS is used over the geometry heuristic."""
    assert has_wkt(sphere) is False
    crs = CRS.from_user_input("+proj=eqc")
    to_wkt(sphere, crs)
    assert projected(sphere)
