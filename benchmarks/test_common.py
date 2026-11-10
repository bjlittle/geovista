# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Benchmarks of :mod:`geovista.common`."""

from __future__ import annotations

import pytest

from geovista.common import from_cartesian


@pytest.mark.limit_memory("6 MB")
def test_from_cartesian(benchmark, grid_mesh):
    """Convert the global grid's points to geographic (bench spec §2 decision 7)."""
    result = benchmark(from_cartesian, grid_mesh)
    assert result.shape == (grid_mesh.n_points, 3)
