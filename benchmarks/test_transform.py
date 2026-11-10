# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Benchmarks of :mod:`geovista.transform`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.crs import WGS84
from geovista.transform import transform_mesh, transform_points

#: The target projections, as PROJ strings, each named.
PROJECTIONS = pytest.mark.parametrize(
    "projection",
    [
        pytest.param("+proj=robin", id="robinson"),
        pytest.param("+proj=moll", id="mollweide"),
        pytest.param("+proj=eqc", id="plate-carree"),
    ],
)


@pytest.mark.limit_memory("28 MB")
@PROJECTIONS
def test_transform_mesh(benchmark, grid_mesh, grid_data, projection):
    """Project the global grid, cut at the antimeridian (bench spec §2 decision 7)."""
    result = benchmark(transform_mesh, grid_mesh, projection)
    assert result.n_cells >= grid_data.size


@pytest.mark.limit_memory("6 MB")
@PROJECTIONS
def test_transform_points(benchmark, cloud, projection):
    """Project a cloud of 100,000 points (bench spec §2 decision 7)."""
    result = benchmark(transform_points, WGS84, projection, *cloud)
    assert result.shape == (cloud[0].size, 3)
    assert np.isfinite(result).all()
