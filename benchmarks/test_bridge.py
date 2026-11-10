# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Benchmarks of :mod:`geovista.bridge`."""

from __future__ import annotations

import pytest

from geovista.bridge import Transform

#: The number of cells of the global grid, 360 by 180.
GRID_CELLS = 64_800

#: The number of points of the cloud.
CLOUD_POINTS = 100_000


@pytest.mark.limit_memory("16 MB")
def test_from_1d(benchmark, grid_bounds, grid_data):
    """Build the global grid from its 1-D bounds (bench spec §2 decision 7)."""
    result = benchmark(Transform.from_1d, *grid_bounds, data=grid_data)
    assert result.n_cells == GRID_CELLS


@pytest.mark.limit_memory("14 MB")
def test_from_2d(benchmark, grid_bounds_2d, grid_data):
    """Build the global grid from its 2-D bounds (bench spec §2 decision 7)."""
    result = benchmark(Transform.from_2d, *grid_bounds_2d, data=grid_data)
    assert result.n_cells == GRID_CELLS


@pytest.mark.limit_memory("14 MB")
def test_from_unstructured(benchmark, grid_nodes, grid_data):
    """Build the global grid from its nodes and faces (bench spec §2 decision 7)."""
    xs, ys, faces = grid_nodes
    result = benchmark(
        Transform.from_unstructured, xs, ys, connectivity=faces, data=grid_data
    )
    assert result.n_cells == GRID_CELLS


@pytest.mark.limit_memory("11 MB")
def test_from_points(benchmark, cloud):
    """Build a cloud of 100,000 points (bench spec §2 decision 7)."""
    result = benchmark(Transform.from_points, *cloud)
    assert result.n_points == CLOUD_POINTS
