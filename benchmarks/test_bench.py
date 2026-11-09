# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""CodSpeed performance benchmarks of the core ``geovista`` operations."""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

import geovista as gv
from geovista.common import from_cartesian
from geovista.core import slice_cells, slice_mesh
from geovista.crs import WGS84
from geovista.geodesic import BBox, line, npoints
from geovista.gridlines import create_meridians, create_parallels
from geovista.search import KDTree, find_nearest_cell
from geovista.transform import transform_mesh, transform_points

#: A selection of target projections, as PROJ strings.
PROJECTIONS = ["+proj=robin", "+proj=moll", "+proj=eqc"]


def test_bridge_from_1d(benchmark, lons, lats, data):
    """Build a rectilinear mesh from 1D contiguous bounds."""
    # "name" is passed through a closure, as it clashes with the benchmark fixture
    result = benchmark(lambda: gv.Transform.from_1d(lons, lats, data=data, name="data"))
    assert result.n_cells == data.size


def test_bridge_from_2d(benchmark, lons_2d, lats_2d, data):
    """Build a curvilinear mesh from 2D nodes."""
    result = benchmark(gv.Transform.from_2d, lons_2d, lats_2d, data=data)
    assert result.n_cells == data.size


def test_bridge_from_points(benchmark, lons_2d, lats_2d):
    """Build a point-cloud mesh."""
    result = benchmark(gv.Transform.from_points, lons_2d, lats_2d)
    assert result.n_points == lons_2d.size


def test_bridge_from_unstructured(benchmark, mesh):
    """Build a mesh from unstructured nodes and face connectivity."""
    xyz = from_cartesian(mesh)
    faces = mesh.regular_faces
    result = benchmark(
        gv.Transform.from_unstructured, xyz[:, 0], xyz[:, 1], connectivity=faces
    )
    assert result.n_cells == mesh.n_cells


def test_from_cartesian(benchmark, mesh):
    """Convert the cartesian points of a mesh to geographic coordinates."""
    result = benchmark(from_cartesian, mesh)
    assert result.shape == (mesh.n_points, 3)


@pytest.mark.parametrize("projection", PROJECTIONS)
def test_transform_points(benchmark, projection, lons_2d, lats_2d):
    """Project geographic points to a target CRS."""
    result = benchmark(transform_points, WGS84, projection, lons_2d, lats_2d)
    assert result.shape == (*lons_2d.shape, 3)


@pytest.mark.parametrize("projection", PROJECTIONS)
def test_transform_mesh(benchmark, projection, mesh):
    """Project a global mesh, slicing it along the antimeridian."""
    result = benchmark(transform_mesh, mesh, projection)
    assert result.n_cells >= mesh.n_cells


def test_slice_mesh(benchmark, mesh):
    """Cut a global mesh along the antimeridian."""
    result = benchmark(slice_mesh, mesh)
    assert result.n_cells >= mesh.n_cells


def test_slice_cells_meridian(benchmark, mesh):
    """Cut a global mesh along an arbitrary meridian, remeshing bisected cells."""
    result = benchmark(slice_cells, mesh, meridian=45.5)
    assert result.n_cells >= mesh.n_cells


def test_kdtree_build(benchmark, mesh):
    """Build a kd-tree over the points of a mesh."""
    result = benchmark(KDTree, mesh)
    assert result.n_points == mesh.n_points


def test_kdtree_query(benchmark, mesh):
    """Query a kd-tree for the nearest neighbours of many points."""
    tree = KDTree(mesh)
    rng = np.random.default_rng(seed=0)
    xs = rng.uniform(-180, 180, size=1_000)
    ys = rng.uniform(-90, 90, size=1_000)
    _distances, indices = benchmark(tree.query, xs, ys, k=4)
    assert indices.shape == (xs.size, 4)


def test_find_nearest_cell(benchmark, mesh):
    """Find the cell of a mesh nearest to a point-of-interest."""
    result = benchmark(find_nearest_cell, mesh, 12.3, 45.6)
    assert result is not None


def test_geodesic_line(benchmark):
    """Build a geodesic line through several waypoints."""
    lons = [-170, -90, 0, 90, 170]
    lats = [-60, 30, 0, 45, 60]
    result = benchmark(line, lons, lats)
    assert result.n_points > len(lons)


def test_geodesic_npoints(benchmark):
    """Compute equally spaced points along a geodesic."""
    result = benchmark(npoints, -120.0, -45.0, 150.0, 60.0, npts=10_000)
    assert len(result[0]) == 10_000


def test_bbox_enclosed(benchmark, mesh):
    """Extract the region of a mesh enclosed by a geodesic bounding-box."""
    bbox = BBox([-30, 30, 30, -30], [-20, -20, 40, 40])
    result = benchmark(bbox.enclosed, mesh)
    assert result.n_cells > 0


def test_gridlines(benchmark):
    """Create the graticule meridians and parallels."""

    def graticule() -> tuple[object, object]:
        return create_meridians(), create_parallels()

    meridians, parallels = benchmark(graticule)
    assert meridians.blocks
    assert parallels.blocks


def test_mesh_combine(benchmark, mesh):
    """Combine several meshes into one."""
    meshes = [mesh.copy() for _ in range(4)]
    result = benchmark(gv.core.combine, *meshes)
    assert isinstance(result, pv.PolyData)
