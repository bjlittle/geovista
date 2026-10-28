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

from geovista.bridge import Transform
from geovista.common import GV_FIELD_CRS, from_cartesian
from geovista.crs import WGS84, to_wkt
from geovista.globe import Globe
from geovista.search import (
    KDTREE_LEAF_SIZE,
    KDTREE_PREFERENCE,
    KDTree,
    SearchPreference,
)
from geovista.transform import transform_mesh

PREFERENCES = SearchPreference.values()


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
        if SearchPreference(preference) == SearchPreference.CENTER
        else lam_uk.n_points
    )
    assert kdtree.n_points == n_points


def test_preference_fail(lam_uk):
    """Test trap of invalid preference."""
    options = " or ".join([f"{item!r}" for item in SearchPreference.values()])
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
        if SearchPreference(preference) == SearchPreference.POINT
        else lam_uk.cell_centers().points
    )
    np.testing.assert_array_almost_equal(kdtree.points, expected)


@pytest.mark.parametrize("preference", PREFERENCES)
def test_crs_eqc(lam_uk, preference):
    """Test kd-tree CRS transformation."""
    lam_xyz = (
        lam_uk.points
        if SearchPreference(preference) == SearchPreference.POINT
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
    expected = [cid, *neighbours.expected]
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


@pytest.mark.parametrize("radius", [1.0, 6378137.0])
def test_query_uses_the_globe_of_the_tree(radius):
    """Test a query lies on the globe of the mesh the tree was built from."""
    lons, lats = [0.0, 10.0, 20.0], [0.0, 10.0]
    mesh = Transform.from_1d(lons, lats, globe=Globe(render_radius=radius))
    kdtree = KDTree(mesh)
    distances, indices = kdtree.query(10.0, 10.0)
    lonlats = from_cartesian(mesh)
    (expected,) = np.flatnonzero(
        np.isclose(lonlats[:, 0], 10.0) & np.isclose(lonlats[:, 1], 10.0)
    )
    assert int(np.ravel(indices)[0]) == expected
    np.testing.assert_allclose(np.ravel(distances)[0], 0, atol=1e-9 * radius)


def test_a_tree_of_a_projected_mesh():
    """Test a projected mesh is placed at the render radius it records."""
    mesh = Transform.from_1d(
        [0.0, 10.0, 20.0], [0.0, 10.0], globe=Globe(render_radius=2)
    )
    planar = transform_mesh(mesh, "+proj=eqc")
    kdtree = KDTree(planar)
    np.testing.assert_allclose(np.linalg.norm(kdtree.points, axis=1), 2, rtol=1e-12)


def test_radius_is_gone(lam_uk):
    """Test the radius keyword is refused."""
    with pytest.raises(TypeError, match="radius"):
        KDTree(lam_uk).query(0.0, 0.0, radius=2.0)
