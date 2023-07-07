"""Unit-tests for :func:`geovista.common.triangulated`."""
from __future__ import annotations

from geovista.common import triangulated


def test_not_triangulated(lam_uk):
    """Test detection of untriangulated mesh."""
    assert not triangulated(lam_uk)


def test_triangulated(lam_uk):
    """Test detection of triangulated mesh."""
    mesh = lam_uk.triangulate()
    assert triangulated(mesh)
