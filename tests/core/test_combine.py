# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.core.combine`."""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

from geovista.bridge import Transform
from geovista.common import (
    GV_FIELD_CRS,
    GV_FIELD_GLOBE_RENDER_RADIUS,
    GV_FIELD_RADIUS,
)
from geovista.core import combine
from geovista.globe import Globe


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


def test_single_mesh_arrays_share_a_name():
    """Test a single mesh keeps a point array and a cell array of the same name."""
    mesh = pv.Plane(i_resolution=1, j_resolution=1)
    mesh.point_data["temperature"] = np.arange(mesh.n_points, dtype=float)
    mesh.cell_data["temperature"] = np.array([10.0])

    result = combine(mesh)

    np.testing.assert_array_equal(result.point_data["temperature"], [0, 1, 2, 3])
    np.testing.assert_array_equal(result.cell_data["temperature"], [10.0])


def test_point_and_field_arrays_share_a_name():
    """Test a point array and a field array of the same name are both combined."""
    meshes = _spheres_with("field")
    n_points = meshes[0].n_points

    result = combine(*meshes)

    expected = np.tile(np.arange(n_points, dtype=float), 2)
    np.testing.assert_array_equal(result.point_data["data"], expected)
    assert list(result.field_data["data"]) == ["note"]


def _strip() -> pv.PolyData:
    """Return a mesh of one triangle strip."""
    points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]], dtype=float)
    return pv.PolyData(points, strips=[4, 0, 1, 2, 3])


def _polygon_and_strip() -> pv.PolyData:
    """Return a mesh of one triangle and one triangle strip."""
    points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]], dtype=float)
    return pv.PolyData(points, faces=[3, 0, 1, 2], strips=[4, 0, 1, 2, 3])


@pytest.mark.parametrize(
    ("meshes", "position"),
    [
        ((_strip(),), 1),
        ((_polygon_and_strip(),), 1),
        ((pv.Sphere(), _strip()), 2),
    ],
    ids=["single", "mixed", "pair"],
)
def test_strips_fail(meshes, position):
    """Test trap of a mesh with strips, which only its faces would be copied of."""
    emsg = f"Can only combine meshes with cells, input mesh #{position} contains strips"
    with pytest.raises(TypeError, match=emsg):
        _ = combine(*meshes)


def _plane_with_wind() -> pv.PolyData:
    """Return a plane with active normals, texture coordinates and vectors."""
    mesh = pv.Plane(i_resolution=1, j_resolution=1)
    mesh.point_data["wind"] = np.tile([1.0, 0.0, 0.0], (mesh.n_points, 1))
    mesh.set_active_vectors("wind")
    return mesh


@pytest.mark.parametrize("n_meshes", [1, 2], ids=["single", "pair"])
def test_roles_kept(n_meshes):
    """Test each array keeps the role it plays in the first mesh."""
    meshes = [_plane_with_wind() for _ in range(n_meshes)]

    result = combine(*meshes)

    assert result.point_data.active_vectors_name == "wind"
    assert result.point_data.active_normals_name == "Normals"
    assert result.point_data.active_texture_coordinates_name == "TextureCoordinates"


def _plane_with_ids(offset: float, start: int) -> pv.PolyData:
    """Return a one-cell plane whose points and cell carry global ids from `start`."""
    mesh = pv.Plane(center=(offset, 0, 0), i_resolution=1, j_resolution=1)
    mesh.point_data["point_ids"] = np.arange(start, start + mesh.n_points)
    mesh.cell_data["cell_ids"] = np.array([start])
    mesh.point_data.SetActiveAttribute("point_ids", mesh.point_data.GLOBALIDS)
    mesh.cell_data.SetActiveAttribute("cell_ids", mesh.cell_data.GLOBALIDS)
    return mesh


@pytest.mark.parametrize("clean", [False, True])
@pytest.mark.parametrize(
    ("starts", "point_ids", "cell_ids"),
    [
        ((100,), [100, 101, 102, 103], [100]),
        ((100, 200), [100, 101, 102, 103, 200, 201, 202, 203], [100, 200]),
    ],
    ids=["single", "pair"],
)
def test_global_ids_kept(starts, point_ids, cell_ids, clean):
    """Test global ids keep the values and the role they have in their meshes.

    The planes lie apart, so cleaning merges no point of one into the other, though
    it may reorder them, so each id is checked against the point it belongs to.

    """
    meshes = [_plane_with_ids(2.0 * i, start) for i, start in enumerate(starts)]
    owner = {
        tuple(point): pid
        for mesh in meshes
        for point, pid in zip(mesh.points, mesh.point_data["point_ids"], strict=True)
    }

    result = combine(*meshes, clean=clean)

    ids = result.point_data["point_ids"]
    np.testing.assert_array_equal(np.sort(ids), point_ids)
    assert [owner[tuple(point)] for point in result.points] == list(ids)
    np.testing.assert_array_equal(result.cell_data["cell_ids"], cell_ids)
    assert result.point_data.GetGlobalIds().GetName() == "point_ids"
    assert result.cell_data.GetGlobalIds().GetName() == "cell_ids"


def _pair(
    second: Globe | None = None, *, crs: bool = True
) -> tuple[pv.PolyData, pv.PolyData]:
    """Return two surfaces over neighbouring longitudes, the second as asked."""
    first = Transform.from_1d([0.0, 10.0, 20.0], [0.0, 10.0])
    other = Transform.from_1d([20.0, 30.0, 40.0], [0.0, 10.0], globe=second)
    if not crs:
        del other.field_data[GV_FIELD_CRS]
    return first, other


@pytest.mark.parametrize("data", [True, False])
def test_refuses_a_different_globe(data):
    """Test meshes on different globes are refused, naming the input and why."""
    with pytest.raises(ValueError, match=r"input mesh #2.*globe"):
        _ = combine(*_pair(Globe(render_radius=2)), data=data)


def test_refuses_a_different_crs():
    """Test meshes in different CRSs are refused, naming the CRS."""
    with pytest.raises(ValueError, match=r"input mesh #2.*CRS"):
        _ = combine(*_pair(crs=False))


def test_names_the_crs_and_globe():
    """Test meshes differing in both are refused, naming both."""
    with pytest.raises(ValueError, match="CRS and globe"):
        _ = combine(*_pair(Globe(render_radius=2), crs=False))


def test_records_the_shared_globe(legacy):
    """Test the combined mesh records the shared globe, and no retired field."""
    first, second = _pair()
    result = combine(legacy(first), second)
    assert GV_FIELD_GLOBE_RENDER_RADIUS in result.field_data
    assert Globe.from_mesh(result) == Globe()
    assert GV_FIELD_RADIUS not in result.field_data
