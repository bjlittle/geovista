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


def _duplicated() -> pv.PolyData:
    """Return two triangles with 6 points, 4 of them distinct."""
    points = np.array(
        [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]],
        dtype=float,
    )
    return pv.PolyData(points, faces=[3, 0, 1, 2, 3, 3, 5, 4])


def test_single_mesh_is_a_new_mesh():
    """Test a single mesh is combined into a new mesh with its cells and data."""
    mesh = pv.Sphere()
    mesh.point_data["data"] = np.arange(mesh.n_points)

    result = combine(mesh)

    assert result is not mesh
    np.testing.assert_array_equal(result.points, mesh.points)
    np.testing.assert_array_equal(result.faces, mesh.faces)
    np.testing.assert_array_equal(result.point_data["data"], mesh.point_data["data"])


@pytest.mark.parametrize("meshes", [1, 2], ids=["single", "pair"])
def test_lines_fail(meshes):
    """Test trap of a mesh with lines, however many meshes are combined."""
    emsg = f"Can only combine meshes with cells, input mesh #{meshes} contains lines"
    with pytest.raises(TypeError, match=emsg):
        _ = combine(*[pv.Sphere()] * (meshes - 1), pv.Line())


@pytest.mark.parametrize("meshes", [1, 2], ids=["single", "pair"])
def test_vertices_fail(meshes):
    """Test trap of a point cloud, whose vertices pyvista counts as cells."""
    cloud = pv.PolyData(np.random.default_rng(0).random((5, 3)))
    emsg = f"Can only combine meshes with cells, input mesh #{meshes} contains vert"
    with pytest.raises(TypeError, match=emsg):
        _ = combine(*[pv.Sphere()] * (meshes - 1), cloud)


def test_single_mesh_clean():
    """Test a single mesh is cleaned, and the mesh given is left as it is."""
    mesh = _duplicated()

    result = combine(mesh, clean=True)

    assert result.n_points == 4
    assert mesh.n_points == 6


def test_single_mesh_no_data():
    """Test a single mesh combined without data carries none."""
    mesh = _duplicated()
    mesh.point_data["data"] = np.arange(mesh.n_points)

    result = combine(mesh, data=False)

    assert not result.point_data.keys()


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
