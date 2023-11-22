"""Unit-tests for :func:`geovista.search.find_nearest_cell`."""
from __future__ import annotations

import pytest

from geovista.common import from_cartesian, to_lonlat
from geovista.search import find_nearest_cell


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
