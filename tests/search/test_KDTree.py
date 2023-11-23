# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.search.KDTree`."""
from __future__ import annotations

import numpy as np
from pyproj import CRS, Transformer
import pytest
import pyvista as pv

from geovista.common import GV_FIELD_CRS, from_cartesian
from geovista.crs import WGS84, to_wkt
from geovista.search import KDTREE_LEAF_SIZE, KDTREE_PREFERENCE, KDTree, Preference

PREFERENCES = Preference.values()


def test_defaults(lam_uk):
    """Test expected defaults are honoured for a kd-tree."""
    kdtree = KDTree(lam_uk)
    assert kdtree.leaf_size == KDTREE_LEAF_SIZE
    assert kdtree.preference.value == KDTREE_PREFERENCE


def test_serialization(lam_uk):
    """Test string and representation serialization."""
    kdtree = KDTree(lam_uk)
    expected = (
        f"KDTree(<PolyData N POINTS: {lam_uk.n_points}>, leaf_size={KDTREE_LEAF_SIZE}, "
        f"preference={KDTREE_PREFERENCE!r})"
    )
    assert repr(kdtree) == expected
    assert str(kdtree) == expected


@pytest.mark.parametrize("preference", PREFERENCES)
def test_preference(lam_uk, preference):
    """Test mesh preference points are registered with kd-tree."""
    kdtree = KDTree(lam_uk, preference=preference)
    n_points = (
        lam_uk.n_cells
        if Preference(preference) == Preference.CENTER
        else lam_uk.n_points
    )
    assert kdtree.n_points == n_points


def test_preference_fail(lam_uk):
    """Test trap of invalid preference."""
    options = " or ".join([f"{item!r}" for item in Preference.values()])
    emsg = f"Expected a preference of {options}"
    with pytest.raises(ValueError, match=emsg):
        _ = KDTree(lam_uk, preference="invalid")


@pytest.mark.parametrize("preference", PREFERENCES)
def test_missing_crs(lam_uk, preference):
    """Test kd-tree construction using mesh without CRS."""
    assert GV_FIELD_CRS in lam_uk.field_data
    lam_uk.field_data.pop(GV_FIELD_CRS)
    assert GV_FIELD_CRS not in lam_uk.field_data
    kdtree = KDTree(lam_uk, preference=preference)
    expected = (
        lam_uk.points
        if Preference(preference) == Preference.POINT
        else lam_uk.cell_centers().points
    )
    np.testing.assert_array_almost_equal(kdtree.points, expected)


@pytest.mark.parametrize("preference", PREFERENCES)
def test_crs_eqc(lam_uk, preference):
    """Test kd-tree CRS transformation."""
    lam_xyz = (
        lam_uk.points
        if Preference(preference) == Preference.POINT
        else lam_uk.cell_centers().points
    )
    lam_lonlat = from_cartesian(pv.PolyData(lam_xyz))
    crs = CRS.from_user_input("+proj=eqc")
    transformer = Transformer.from_crs(WGS84, crs, always_xy=True)
    xs, ys = transformer.transform(lam_lonlat[:, 0], lam_lonlat[:, 1])
    mesh = pv.PolyData(np.vstack([xs, ys, np.zeros_like(xs)]).T)
    to_wkt(mesh, crs)
    kdtree = KDTree(mesh, preference=preference)
    kdtree_lonlat = from_cartesian(pv.PolyData(kdtree.points))
    np.testing.assert_array_almost_equal(lam_lonlat, kdtree_lonlat)


def test_poi_cid(lam_uk, poi):
    """Test cell center nearest neighbour to point-of-interest."""
    kdtree = KDTree(lam_uk, preference="center")
    _, idx = kdtree.query(poi.lon, poi.lat)
    assert idx.size == 1
    assert idx == poi.cid


def test_cell_neighbours(lam_uk, neighbours):
    """Test k nearest cell neighbours of a cell."""
    kdtree = KDTree(lam_uk, preference="center")
    lonlat = from_cartesian(pv.PolyData(kdtree.points))
    cid = neighbours.cid
    expected = [cid] + neighbours.expected
    k = len(expected)
    lon, lat = lonlat[cid][0], lonlat[cid][1]
    _, idx = kdtree.query(lon, lat, k=k)
    np.testing.assert_array_equal(np.unique(idx), np.sort(expected))


def test_vertex(lam_uk, vertex):
    """Test k nearest cell neighbours of a point."""
    kdtree = KDTree(lam_uk, preference="center")
    lonlat = from_cartesian(pv.PolyData(lam_uk.points))
    pid = vertex.pid
    k = len(vertex.cids)
    lon, lat = lonlat[pid][0], lonlat[pid][1]
    _, idx = kdtree.query(lon, lat, k=k)
    np.testing.assert_array_equal(np.unique(idx), np.sort(vertex.cids))


def test_cell_quad_points(lam_uk, center):
    """Test k nearest point neighbours of a cell center."""
    kdtree = KDTree(lam_uk, preference="point")
    lonlat = from_cartesian(pv.PolyData(lam_uk.cell_centers().points))
    cid = center.cid
    lon, lat = lonlat[cid][0], lonlat[cid][1]
    _, idx = kdtree.query(lon, lat, k=4)
    np.testing.assert_array_equal(np.unique(idx), np.sort(center.pids))
