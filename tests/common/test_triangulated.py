# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

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
