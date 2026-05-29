# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Depth-extrusion tests for :meth:`geovista.Transform.from_unstructured`."""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

from geovista.bridge import NAME_CELLS, NAME_POINTS, Transform
from geovista.common import GV_FIELD_CRS, RADIUS

# ── Shared fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def triangle_mesh():
    """Minimal triangular mesh: 4 nodes, 2 faces."""
    lons = np.array([0.0, 1.0, 0.0, 1.0])
    lats = np.array([0.0, 0.0, 1.0, 1.0])
    conn = np.array([[0, 1, 2], [1, 3, 2]])
    return lons, lats, conn


@pytest.fixture
def quad_mesh():
    """Minimal quad mesh: 4 nodes, 1 face."""
    lons = np.array([0.0, 1.0, 1.0, 0.0])
    lats = np.array([0.0, 0.0, 1.0, 1.0])
    conn = np.array([[0, 1, 2, 3]])
    return lons, lats, conn


@pytest.fixture
def depth_levels():
    """Three depth levels → two extruded layers."""
    return np.array([0.0, 100.0, 500.0])


# ── No-depth: existing surface behaviour unchanged ────────────────────────────


class TestFromUnstructuredNoDepth:
    """Without depth, existing PolyData behaviour is unchanged."""

    def test_returns_polydata(self, triangle_mesh):
        """Triangular mesh without depth returns PolyData."""
        lons, lats, conn = triangle_mesh
        result = Transform.from_unstructured(lons, lats, connectivity=conn)
        assert isinstance(result, pv.PolyData)

    def test_quad_returns_polydata(self, quad_mesh):
        """Quad mesh without depth returns PolyData."""
        lons, lats, conn = quad_mesh
        result = Transform.from_unstructured(lons, lats, connectivity=conn)
        assert isinstance(result, pv.PolyData)


# ── With depth: UnstructuredGrid shape ───────────────────────────────────────


class TestFromUnstructuredDepthShape:
    """Verify cell and point counts for extruded meshes."""

    def test_triangle_cell_count(self, triangle_mesh, depth_levels):
        """Cell count equals nface * (nz - 1) for triangular extrusion."""
        lons, lats, conn = triangle_mesh
        nface = conn.shape[0]
        nz = len(depth_levels)
        result = Transform.from_unstructured(
            lons, lats, connectivity=conn, depth=depth_levels
        )
        assert isinstance(result, pv.UnstructuredGrid)
        assert result.n_cells == nface * (nz - 1)

    def test_triangle_point_count(self, triangle_mesh, depth_levels):
        """Point count equals nnode * nz for triangular extrusion."""
        lons, lats, conn = triangle_mesh
        nnode = len(lons)
        nz = len(depth_levels)
        result = Transform.from_unstructured(
            lons, lats, connectivity=conn, depth=depth_levels
        )
        assert result.n_points == nnode * nz

    def test_quad_cell_count(self, quad_mesh, depth_levels):
        """Cell count equals nface * (nz - 1) for quad extrusion."""
        lons, lats, conn = quad_mesh
        nface = conn.shape[0]
        nz = len(depth_levels)
        result = Transform.from_unstructured(
            lons, lats, connectivity=conn, depth=depth_levels
        )
        assert result.n_cells == nface * (nz - 1)

    def test_quad_point_count(self, quad_mesh, depth_levels):
        """Point count equals nnode * nz for quad extrusion."""
        lons, lats, conn = quad_mesh
        nnode = len(lons)
        nz = len(depth_levels)
        result = Transform.from_unstructured(
            lons, lats, connectivity=conn, depth=depth_levels
        )
        assert result.n_points == nnode * nz

    def test_returns_unstructured_grid(self, triangle_mesh, depth_levels):
        """Depth extrusion must return an UnstructuredGrid."""
        lons, lats, conn = triangle_mesh
        result = Transform.from_unstructured(
            lons, lats, connectivity=conn, depth=depth_levels
        )
        assert isinstance(result, pv.UnstructuredGrid)


# ── Cell types ────────────────────────────────────────────────────────────────


class TestFromUnstructuredCellTypes:
    """Verify correct VTK cell types are created."""

    def test_triangle_produces_wedge_cells(self, triangle_mesh, depth_levels):
        """Triangular faces must produce VTK_WEDGE (type 13) cells."""
        lons, lats, conn = triangle_mesh
        result = Transform.from_unstructured(
            lons, lats, connectivity=conn, depth=depth_levels
        )
        assert np.all(result.celltypes == 13)

    def test_quad_produces_hex_cells(self, quad_mesh, depth_levels):
        """Quad faces must produce VTK_HEXAHEDRON (type 12) cells."""
        lons, lats, conn = quad_mesh
        result = Transform.from_unstructured(
            lons, lats, connectivity=conn, depth=depth_levels
        )
        assert np.all(result.celltypes == 12)


# ── Depth semantics ───────────────────────────────────────────────────────────


class TestFromUnstructuredDepthSemantics:
    """Verify depth values map nodes to the correct sphere radius."""

    def test_positive_depth_below_surface(self, triangle_mesh):
        """All nodes at positive depth must have radius < RADIUS."""
        lons, lats, conn = triangle_mesh
        depth = np.array([100.0, 1000.0])
        result = Transform.from_unstructured(
            lons, lats, connectivity=conn, depth=depth, vexag=1.0
        )
        radii = np.linalg.norm(result.points, axis=1)
        assert np.all(radii < RADIUS)

    def test_zero_depth_on_surface(self, triangle_mesh):
        """Nodes at depth=0 must lie exactly on the sphere surface."""
        lons, lats, conn = triangle_mesh
        depth = np.array([0.0, 100.0])
        result = Transform.from_unstructured(
            lons, lats, connectivity=conn, depth=depth, vexag=1.0
        )
        nnode = len(lons)
        surface_radii = np.linalg.norm(result.points[:nnode], axis=1)
        np.testing.assert_allclose(surface_radii, RADIUS, rtol=1e-6)

    def test_crs_attached(self, triangle_mesh, depth_levels, wgs84_wkt):
        """WGS84 CRS metadata must be attached to the extruded grid."""
        lons, lats, conn = triangle_mesh
        result = Transform.from_unstructured(
            lons, lats, connectivity=conn, depth=depth_levels
        )
        assert result[GV_FIELD_CRS] == wgs84_wkt


# ── Data attachment ───────────────────────────────────────────────────────────


class TestFromUnstructuredDepthData:
    """Verify data is correctly attached to extruded meshes."""

    def test_cell_data_attached(self, triangle_mesh, depth_levels):
        """Named cell data sized n_cells is stored and retrievable."""
        lons, lats, conn = triangle_mesh
        nface = conn.shape[0]
        nz = len(depth_levels)
        n_cells = nface * (nz - 1)
        result = Transform.from_unstructured(
            lons, lats, connectivity=conn, depth=depth_levels,
            data=np.arange(n_cells, dtype=float), name="sal",
        )
        assert "sal" in result.array_names
        assert result["sal"].size == n_cells

    def test_point_data_attached(self, triangle_mesh, depth_levels):
        """Point data sized n_points is attached with the default name."""
        lons, lats, conn = triangle_mesh
        nnode = len(lons)
        nz = len(depth_levels)
        n_pts = nnode * nz
        result = Transform.from_unstructured(
            lons, lats, connectivity=conn, depth=depth_levels,
            data=np.ones(n_pts),
        )
        assert result[NAME_POINTS].size == n_pts

    def test_default_name_cells(self, triangle_mesh, depth_levels):
        """Cell data without a name gets the NAME_CELLS default."""
        lons, lats, conn = triangle_mesh
        nface, nz = conn.shape[0], len(depth_levels)
        result = Transform.from_unstructured(
            lons, lats, connectivity=conn, depth=depth_levels,
            data=np.zeros(nface * (nz - 1)),
        )
        assert NAME_CELLS in result.array_names


# ── Error handling ────────────────────────────────────────────────────────────


class TestFromUnstructuredDepthErrors:
    """Verify invalid depth inputs raise clear errors."""

    def test_2d_depth_raises(self, triangle_mesh):
        """2-D depth array must raise ValueError."""
        lons, lats, conn = triangle_mesh
        with pytest.raises(ValueError, match="1D"):
            Transform.from_unstructured(
                lons, lats, connectivity=conn, depth=np.ones((2, 3))
            )

    def test_single_depth_level_raises(self, triangle_mesh):
        """A depth array with fewer than 2 levels must raise ValueError."""
        lons, lats, conn = triangle_mesh
        with pytest.raises(ValueError, match="at least 2"):
            Transform.from_unstructured(
                lons, lats, connectivity=conn, depth=np.array([100.0])
            )

    def test_masked_connectivity_raises(self, depth_levels):
        """Masked (mixed-face) connectivity with depth must raise ValueError."""
        lons = np.array([0.0, 1.0, 0.0, 1.0])
        lats = np.array([0.0, 0.0, 1.0, 1.0])
        conn = np.ma.array(
            [[0, 1, 2, -1], [1, 3, 2, -1]],
            mask=[[0, 0, 0, 1], [0, 0, 0, 1]],
        )
        with pytest.raises(ValueError, match=r"[Mm]asked"):
            Transform.from_unstructured(
                lons, lats, connectivity=conn, depth=depth_levels
            )

    def test_pentagon_connectivity_raises(self, depth_levels):
        """Pentagon faces (5 vertices) with depth must raise ValueError."""
        lons = np.array([0.0, 1.0, 2.0, 1.0, 0.5])
        lats = np.array([0.0, 0.0, 1.0, 2.0, 1.0])
        conn = np.array([[0, 1, 2, 3, 4]])
        with pytest.raises(ValueError, match="triangular"):
            Transform.from_unstructured(
                lons, lats, connectivity=conn, depth=depth_levels
            )
