# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Benchmarks of :mod:`geovista.search`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.search import KDTree, find_nearest_cell

#: The number of the cloud's points the ``query`` benchmark asks for.
QUERIES = 10_000


@pytest.mark.limit_memory("2 MB")
def test_kdtree(benchmark, cloud_mesh):
    """Build a kd-tree over the cloud's 100,000 points (bench spec §2 decision 7)."""
    result = benchmark(KDTree, cloud_mesh)
    assert result.n_points == cloud_mesh.n_points


@pytest.mark.limit_memory("3 MB")
def test_kdtree_query(benchmark, cloud, cloud_mesh):
    """Find 10,000 of the cloud's points in its tree (bench spec §2 decision 7)."""
    tree = KDTree(cloud_mesh)
    lons, lats = cloud[0][:QUERIES], cloud[1][:QUERIES]
    _, indices = benchmark(tree.query, lons, lats)
    np.testing.assert_array_equal(indices, np.arange(QUERIES))


@pytest.mark.limit_memory("6 MB")
def test_find_nearest_cell(benchmark, grid_mesh):
    """Find the grid's cell nearest 12.3°E, 45.6°N (bench spec §2 decision 7)."""
    result = benchmark(find_nearest_cell, grid_mesh, 12.3, 45.6)
    assert np.size(result) == 1
