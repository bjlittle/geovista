# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.core.combine`."""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

from geovista.core import combine


def test_single_mesh_fail():
    """Test trap of a single mesh that is not a :class:`~pyvista.PolyData`."""
    emsg = "Can only combine 'pyvista.PolyData' meshes, input mesh #1 has type"
    with pytest.raises(TypeError, match=emsg):
        _ = combine(pv.ImageData(dimensions=(2, 2, 2)))


def test_mesh_fail():
    """Test trap of a mesh that is not a :class:`~pyvista.PolyData`."""
    emsg = "Can only combine 'pyvista.PolyData' meshes, input mesh #2 has type"
    with pytest.raises(TypeError, match=emsg):
        _ = combine(pv.Sphere(), pv.ImageData(dimensions=(2, 2, 2)))


def test_single_mesh_pass_thru():
    """Test a single :class:`~pyvista.PolyData` is returned as it is."""
    mesh = pv.Sphere()
    assert combine(mesh) is mesh


@pytest.mark.parametrize(
    "meshes",
    [(pv.MultiBlock(),), (pv.MultiBlock(), pv.Sphere())],
    ids=["single", "first"],
)
def test_multiblock_fail(meshes):
    """Test trap of a :class:`~pyvista.MultiBlock`, which is not a dataset."""
    emsg = "Can only combine 'pyvista.PolyData' meshes, input mesh #1 has type"
    with pytest.raises(TypeError, match=emsg):
        _ = combine(*meshes)


def _spheres_with(association: str) -> tuple[pv.PolyData, pv.PolyData]:
    """Return two spheres whose point array shares its name with another array."""
    mesh = pv.Sphere()
    mesh.point_data["data"] = np.arange(mesh.n_points, dtype=float)
    if association == "cell":
        mesh.cell_data["data"] = -np.arange(mesh.n_cells, dtype=float)
    else:
        mesh.field_data["data"] = ["note"]
    return mesh, mesh.copy()


def test_point_and_cell_arrays_share_a_name():
    """Test a point array and a cell array of the same name are both combined."""
    meshes = _spheres_with("cell")
    n_points, n_cells = meshes[0].n_points, meshes[0].n_cells

    result = combine(*meshes)

    expected = np.tile(np.arange(n_points, dtype=float), 2)
    np.testing.assert_array_equal(result.point_data["data"], expected)
    expected = np.tile(-np.arange(n_cells, dtype=float), 2)
    np.testing.assert_array_equal(result.cell_data["data"], expected)


def test_point_and_field_arrays_share_a_name():
    """Test a point array and a field array of the same name are both combined."""
    meshes = _spheres_with("field")
    n_points = meshes[0].n_points

    result = combine(*meshes)

    expected = np.tile(np.arange(n_points, dtype=float), 2)
    np.testing.assert_array_equal(result.point_data["data"], expected)
    assert list(result.field_data["data"]) == ["note"]
