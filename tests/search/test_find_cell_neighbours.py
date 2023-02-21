"""
Unit-tests for :func:`geovista.search.find_cell_neighbours`.

"""
from geovista.search import find_cell_neighbours


def test(lam_uk, neighbours):
    cids = find_cell_neighbours(lam_uk, neighbours.cid)
    assert cids == neighbours.expected
    assert neighbours.cid not in cids
