"""
Unit-tests for :func:`geovista.search.find_nearest_cell`.

"""
import pytest

from geovista.common import to_lonlat, to_xy0
from geovista.search import find_nearest_cell


def test_cell_centers(lam_uk):
    # calculate cartesian xyz cell centers of the lam
    cell_centers = lam_uk.cell_centers()
    # convert the cell centers to lon/lat
    lonlat = to_xy0(cell_centers)
    # check the calculated cell ids of the cell centers
    for expected, poi in enumerate(lonlat):
        cids = find_nearest_cell(lam_uk, *poi)
        assert len(cids) == 1
        assert cids[0] == expected


@pytest.mark.xfail(reason="requires projection support")
def test_cell_centers__lam_rotated_pole():
    assert 0


def test_poi(lam_uk, poi):
    lon, lat = poi.lon, poi.lat
    cids = find_nearest_cell(lam_uk, lon, lat)
    assert len(cids) == 1
    assert cids[0] == poi.cid


def test_vertex(lam_uk, vertex):
    point = lam_uk.points[vertex.pid]
    lonlat = to_lonlat(point)
    cids = find_nearest_cell(lam_uk, *lonlat)
    assert cids == vertex.cids


def test_vertex__single(lam_uk, vertex_corner):
    point = lam_uk.points[vertex_corner.pid]
    lonlat = to_lonlat(point)
    cid = find_nearest_cell(lam_uk, *lonlat, single=True)
    assert cid == vertex_corner.cids


def test_vertex__single_fail(lam_uk):
    point = lam_uk.points[0]
    lonlat = to_lonlat(point)
    emsg = "Expected to find 1 cell"
    with pytest.raises(ValueError, match=emsg):
        _ = find_nearest_cell(lam_uk, *lonlat, single=True)
