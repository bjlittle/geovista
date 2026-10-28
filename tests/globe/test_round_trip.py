# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for a mesh keeping its CRS and globe through a file.

This is the round trip of crs spec §6, as scene spec §4.3 has it.
"""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

from geovista.bridge import Transform
from geovista.crs import from_wkt
from geovista.globe import Globe

LONS = np.linspace(-180, 180, 9)
LATS = np.linspace(-90, 90, 5)

#: A render radius of 1, and of the Earth's radius (scene spec §6).
RADII = [1.0, 6378137.0]


@pytest.mark.parametrize("suffix", [".vtk", ".vtp", ".vtu", ".vtkhdf"])
@pytest.mark.parametrize("render_radius", RADII)
def test_the_crs_and_globe_survive_a_file(tmp_path, suffix, render_radius):
    """Test that a saved mesh reads back with its CRS, globe and points."""
    mesh = Transform.from_1d(LONS, LATS, globe=Globe(render_radius=render_radius))
    globe = Globe(
        radius=6371000,
        render_radius=render_radius,
        exaggeration=20,
        exaggeration_below=100,
    )
    globe.to_mesh(mesh)
    if suffix == ".vtu":
        mesh = mesh.cast_to_unstructured_grid()
    path = tmp_path / f"mesh{suffix}"
    mesh.save(path)  # binary, by default
    back = pv.read(path)
    assert from_wkt(back) == from_wkt(mesh)
    assert Globe.from_mesh(back) == globe
    assert back.points.dtype == mesh.points.dtype
    assert np.array_equal(back.points, mesh.points)
