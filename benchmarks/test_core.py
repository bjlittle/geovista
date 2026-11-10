# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Benchmarks of :mod:`geovista.core`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.core import combine, resize, slice_cells, slice_mesh

#: The number of copies of the global grid the ``combine`` benchmark joins.
COPIES = 4


@pytest.mark.limit_memory("28 MB")
def test_slice_mesh(benchmark, grid_mesh, grid_data):
    """Cut the global grid at the antimeridian (bench spec §2 decision 7)."""
    result = benchmark(slice_mesh, grid_mesh)
    assert result.n_cells >= grid_data.size


@pytest.mark.limit_memory("28 MB")
def test_slice_cells(benchmark, grid_mesh, grid_data):
    """Cut the global grid's cells at 45.5° east (bench spec §2 decision 7)."""
    result = benchmark(slice_cells, grid_mesh, meridian=45.5)
    assert result.n_cells >= grid_data.size


@pytest.mark.limit_memory("76 MB")
def test_combine(benchmark, grid_mesh, grid_data):
    """Join four copies of the global grid (bench spec §2 decision 7)."""
    meshes = [grid_mesh.copy() for _ in range(COPIES)]
    result = benchmark(combine, *meshes)
    assert result.n_cells == COPIES * grid_data.size


@pytest.mark.limit_memory("12 MB")
def test_resize(benchmark, grid_mesh):
    """Lift the global grid one level above the surface (bench spec §2 decision 7)."""
    radius = np.linalg.norm(grid_mesh.points[0])
    result = benchmark(resize, grid_mesh, zlevel=1)
    assert result.n_points == grid_mesh.n_points
    assert np.linalg.norm(result.points[0]) > radius
