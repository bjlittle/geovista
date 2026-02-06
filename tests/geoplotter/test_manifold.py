# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :attr:`geovista.geoplotter.GeoPlotter.manifold`."""

from __future__ import annotations

import pytest

from geovista.geodesic import panel
from geovista.geoplotter import GeoPlotter


def test_no_manifold():
    """Test plotter creation with no manifold."""
    p = GeoPlotter()
    assert p.manifold is None


def test_kwarg():
    """Test plotter creation with manifold."""
    bbox = panel("asia")
    p = GeoPlotter(manifold=bbox)
    assert p.manifold is bbox
    p.manifold = None
    assert p.manifold is None


def test_bad_manifold():
    """Test setter trap of non-manifold."""
    p = GeoPlotter()
    assert p.manifold is None
    emsg = "'manifold' must be a 'BBox' instance"
    with pytest.raises(TypeError, match=emsg):
        p.manifold = "bbox"


def test_manifold():
    """Test setter of manifold."""
    bbox = panel("arctic")
    p = GeoPlotter()
    assert p.manifold is None
    p.manifold = bbox
    assert p.manifold is bbox
