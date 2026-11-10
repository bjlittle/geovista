# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.core.MeridianSlice`."""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

from geovista.bridge import Transform
from geovista.common import GV_CELL_IDS, GV_POINT_IDS
from geovista.core import MeridianSlice


@pytest.mark.parametrize("preference", ["cell", "point"])
def test_active_scalars_kept(preference):
    """Test the active scalars keep their association when both share a name."""
    mesh = Transform.from_1d([-10, 0, 10, 20], [-10, 0, 10])
    mesh.point_data["data"] = range(mesh.n_points)
    mesh.cell_data["data"] = range(mesh.n_cells)
    mesh.set_active_scalars("data", preference=preference)
    expected = mesh.active_scalars_info
    _ = MeridianSlice(mesh, 5)
    assert mesh.active_scalars_info == expected
    assert expected.association == pv.FieldAssociation[preference.upper()]


def _arrays(mesh: pv.PolyData) -> tuple[list[str], list[str], object]:
    """Return the names of a mesh's cell and point arrays, and its active scalars."""
    return sorted(mesh.cell_data), sorted(mesh.point_data), mesh.active_scalars_info


def test_the_given_mesh_is_unchanged():
    """Test slicing a mesh adds no arrays to it (#2937)."""
    mesh = Transform.from_1d([-10, 0, 10, 20], [-10, 0, 10], data=range(6))
    expected = _arrays(mesh)
    _ = MeridianSlice(mesh, 5)
    assert _arrays(mesh) == expected


def test_the_ids_are_its_own_mesh_s():
    """Test the slicer carries each id array on its own mesh, by its association."""
    mesh = Transform.from_1d([-10, 0, 10, 20], [-10, 0, 10], data=range(6))
    slicer = MeridianSlice(mesh, 5)
    assert slicer.mesh is not mesh
    assert list(slicer.mesh.cell_data[GV_CELL_IDS]) == list(range(mesh.n_cells))
    assert list(slicer.mesh.point_data[GV_POINT_IDS]) == list(range(mesh.n_points))


def test_the_ids_keep_their_association_when_the_counts_match():
    """Test each id lands on its own association, with as many cells as points."""
    # a tetrahedron's surface on the unit sphere: four points and four faces
    points = np.array(
        [[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]], dtype=float
    ) / np.sqrt(3)
    faces = np.hstack([[3, 0, 1, 2], [3, 0, 3, 1], [3, 0, 2, 3], [3, 1, 3, 2]])
    mesh = pv.PolyData(points, faces=faces)
    assert mesh.n_cells == mesh.n_points
    slicer = MeridianSlice(mesh, 0)
    assert GV_CELL_IDS in slicer.mesh.cell_data
    assert GV_POINT_IDS in slicer.mesh.point_data
