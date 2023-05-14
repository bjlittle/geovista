"""Unit-tests for :func:`geovista.search.find_cell_neighbours`."""
from geovista.search import find_cell_neighbours


def test(lam_uk, neighbours):
    """Test finding all neighbouring cells of a target cell within a UK LAM mesh."""
    cids = find_cell_neighbours(lam_uk, neighbours.cid)
    assert cids == neighbours.expected
    assert neighbours.cid not in cids
