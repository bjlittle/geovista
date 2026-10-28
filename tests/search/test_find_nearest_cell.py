# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.search.find_nearest_cell`."""

from __future__ import annotations

import pytest

from geovista.bridge import Transform
from geovista.common import from_cartesian, to_lonlat
from geovista.globe import Globe
from geovista.search import find_nearest_cell
from geovista.transform import transform_mesh


def test_cell_centers(lam_uk):
    """Test only a single cell is found when given a cell center."""
    # calculate cartesian xyz cell centers of the lam
    cell_centers = lam_uk.cell_centers()
    # convert the cell centers to lon/lat
    lonlat = from_cartesian(cell_centers)
    # check the calculated cell ids of the cell centers
    for expected, poi in enumerate(lonlat):
        cids = find_nearest_cell(lam_uk, *poi)
        assert len(cids) == 1
        assert cids[0] == expected


@pytest.mark.xfail(reason="requires projection support")
def test_cell_centers__lam_rotated_pole():
    """Test requires projection support before implementing."""
    # TODO @bjlittle: Complete this test case.
    raise AssertionError


def test_poi(lam_uk, poi):
    """Test only a single cell is found for the given Point-Of-Interest (POI)."""
    lon, lat = poi.lon, poi.lat
    cids = find_nearest_cell(lam_uk, lon, lat)
    assert len(cids) == 1
    assert cids[0] == poi.cid


def test_vertex(lam_uk, vertex):
    """Test the correct cell-IDs are found for the given lam_uk point-ID (pid)."""
    point = lam_uk.points[vertex.pid]
    lonlat = to_lonlat(point)
    cids = find_nearest_cell(lam_uk, *lonlat)
    assert cids == vertex.cids


def test_vertex__single(lam_uk, vertex_corner):
    """Test the correct lam_uk corner cell is found given the corner point-ID (pid)."""
    point = lam_uk.points[vertex_corner.pid]
    lonlat = to_lonlat(point)
    cid = find_nearest_cell(lam_uk, *lonlat, single=True)
    assert cid == vertex_corner.cids


def test_vertex__single_fail(lam_uk):
    """Test trap for point that has more than one cell."""
    point = lam_uk.points[0]
    lonlat = to_lonlat(point)
    emsg = "Expected to find 1 cell"
    with pytest.raises(ValueError, match=emsg):
        _ = find_nearest_cell(lam_uk, *lonlat, single=True)


@pytest.mark.parametrize("z", [0, None])
def test_planar_z(z):
    """Test a POI with no z-coordinate on a projected mesh defaults to zero."""
    mesh = transform_mesh(Transform.from_1d([0, 10, 20], [0, 10, 20]), "+proj=eqc")
    x, y, _ = mesh.cell_centers().points[3]
    assert find_nearest_cell(mesh, x, y, z=z) == [3]


@pytest.mark.parametrize("radius", [2.0, 6378137.0])
def test_a_mesh_on_another_globe(radius):
    """Test the cells found are those of the same mesh at a render radius of 1."""
    lons, lats = [0.0, 10.0, 20.0, 30.0], [0.0, 10.0, 20.0]
    expected = find_nearest_cell(Transform.from_1d(lons, lats), 10.0, 10.0)
    mesh = Transform.from_1d(lons, lats, globe=Globe(render_radius=radius))
    assert find_nearest_cell(mesh, 10.0, 10.0) == expected
    assert len(expected) == 4
