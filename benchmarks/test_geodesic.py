# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Benchmarks of :mod:`geovista.geodesic`."""

from __future__ import annotations

import pytest

from geovista import geodesic
from geovista.geodesic import BBox, npoints, wedge

#: The number of points along the geodesic of the ``npoints`` benchmark.
NPTS = 10_000


@pytest.mark.limit_memory("24 MB")
def test_line(benchmark, line):
    """Build a geodesic line through 2,000 vertices (bench spec §2 decision 7)."""
    result = benchmark(geodesic.line, *line)
    assert result.n_points > line[0].size


@pytest.mark.limit_memory("1 MB")
def test_npoints(benchmark):
    """Compute 10,000 points along one geodesic (bench spec §2 decision 7)."""
    lons, _ = benchmark(npoints, -120.0, -45.0, 150.0, 60.0, npts=NPTS)
    assert len(lons) == NPTS


@pytest.mark.limit_memory("51 MB")
def test_bbox_enclosed(benchmark, grid_mesh):
    """Extract the cells of the global grid in a box (bench spec §2 decision 7)."""
    bbox = BBox([-30, 30, 30, -30], [-20, -20, 40, 40])
    result = benchmark(bbox.enclosed, grid_mesh)
    assert result.n_cells > 0


@pytest.mark.limit_memory("1 MB")
def test_wedge(benchmark):
    """Build a wedge from 0° to 90° of longitude (bench spec §2 decision 7)."""
    result = benchmark(wedge, 0, 90)
    assert isinstance(result, BBox)
