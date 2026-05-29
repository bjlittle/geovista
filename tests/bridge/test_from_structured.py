# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.Transform.from_structured`."""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

from geovista.bridge import NAME_CELLS, NAME_POINTS, Transform
from geovista.common import GV_FIELD_CRS, RADIUS

# ── Shared fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def lons_1d():
    """1-D longitude array (4 points) for rectilinear tests."""
    return np.linspace(-10.0, 10.0, 4)


@pytest.fixture
def lats_1d():
    """1-D latitude array (3 points) for rectilinear tests."""
    return np.linspace(-5.0, 5.0, 3)


@pytest.fixture
def depth_1d():
    """Depth levels in metres, positive = downward."""
    return np.array([0.0, 100.0, 500.0, 1000.0])


@pytest.fixture
def lons_2d(lons_1d, lats_1d):
    """Curvilinear 2-D lon array with shape (ny, nx)."""
    return np.broadcast_to(lons_1d[None, :], (len(lats_1d), len(lons_1d))).copy()


@pytest.fixture
def lats_2d(lons_1d, lats_1d):
    """Curvilinear 2-D lat array with shape (ny, nx)."""
    return np.broadcast_to(lats_1d[:, None], (len(lats_1d), len(lons_1d))).copy()


# ── No-depth path: surface mesh delegation ─────────────────────────────────────


class TestFromStructuredNoDep:
    """Without depth, from_structured delegates to from_1d / from_2d."""

    def test_1d_returns_polydata(self, lons_1d, lats_1d):
        """1-D inputs without depth produce a surface PolyData."""
        result = Transform.from_structured(lons_1d, lats_1d)
        assert isinstance(result, pv.PolyData)

    def test_2d_returns_polydata(self, lons_2d, lats_2d):
        """2-D curvilinear inputs without depth produce a surface PolyData."""
        result = Transform.from_structured(lons_2d, lats_2d)
        assert isinstance(result, pv.PolyData)


# ── With depth: StructuredGrid shape ──────────────────────────────────────────


class TestFromStructuredShape:
    """Verify StructuredGrid dimensions for all broadcasting cases."""

    def test_1d_rectilinear(self, lons_1d, lats_1d, depth_1d):
        """1-D lon/lat/depth produces (nx*ny*nz) points and correct cells."""
        nx, ny, nz = len(lons_1d), len(lats_1d), len(depth_1d)
        result = Transform.from_structured(lons_1d, lats_1d, depth=depth_1d)
        assert isinstance(result, pv.StructuredGrid)
        assert result.n_points == nx * ny * nz
        assert result.n_cells == (nx - 1) * (ny - 1) * (nz - 1)

    def test_2d_curvilinear_1d_depth(self, lons_2d, lats_2d, depth_1d):
        """2-D curvilinear lon/lat with 1-D depth produces correct grid."""
        ny, nx = lons_2d.shape
        nz = len(depth_1d)
        result = Transform.from_structured(lons_2d, lats_2d, depth=depth_1d)
        assert isinstance(result, pv.StructuredGrid)
        assert result.n_points == nx * ny * nz
        assert result.n_cells == (nx - 1) * (ny - 1) * (nz - 1)

    def test_2d_curvilinear_3d_depth(self, lons_2d, lats_2d, depth_1d):
        """Terrain-following depth (nz, ny, nx) with 2-D lon/lat."""
        ny, nx = lons_2d.shape
        nz = len(depth_1d)
        depth_3d = np.broadcast_to(
            depth_1d[:, None, None], (nz, ny, nx)
        ).copy()
        result = Transform.from_structured(lons_2d, lats_2d, depth=depth_3d)
        assert isinstance(result, pv.StructuredGrid)
        assert result.n_points == nx * ny * nz

    def test_3d_fully_curvilinear(self, lons_2d, lats_2d, depth_1d):
        """Fully 3-D inputs (nz, ny, nx) for all arrays."""
        ny, nx = lons_2d.shape
        nz = len(depth_1d)
        lons_3d = np.broadcast_to(lons_2d[None], (nz, ny, nx)).copy()
        lats_3d = np.broadcast_to(lats_2d[None], (nz, ny, nx)).copy()
        depth_3d = np.broadcast_to(
            depth_1d[:, None, None], (nz, ny, nx)
        ).copy()
        result = Transform.from_structured(lons_3d, lats_3d, depth=depth_3d)
        assert isinstance(result, pv.StructuredGrid)
        assert result.n_points == nx * ny * nz


# ── Depth semantics ────────────────────────────────────────────────────────────


class TestFromStructuredDepthSemantics:
    """Verify that depth is placed below the sphere surface."""

    def test_positive_depth_below_surface(self, lons_1d, lats_1d):
        """Positive depth values must produce radii strictly less than RADIUS."""
        depth = np.array([100.0, 1000.0])
        result = Transform.from_structured(lons_1d, lats_1d, depth=depth, vexag=1.0)
        radii = np.linalg.norm(result.points, axis=1)
        assert np.all(radii < RADIUS)

    def test_zero_depth_on_surface(self, lons_1d, lats_1d):
        """Depth=0 nodes must lie exactly on the sphere surface."""
        depth = np.array([0.0, 0.0001])
        result = Transform.from_structured(lons_1d, lats_1d, depth=depth, vexag=1.0)
        nxy = len(lons_1d) * len(lats_1d)
        surface_pts = result.points[:nxy]
        radii = np.linalg.norm(surface_pts, axis=1)
        np.testing.assert_allclose(radii, RADIUS, rtol=1e-6)

    def test_vexag_scales_depth_extent(self, lons_1d, lats_1d):
        """Doubling vexag must double the radial depth extent."""
        depth = np.array([0.0, 1000.0])
        r1 = Transform.from_structured(lons_1d, lats_1d, depth=depth, vexag=100.0)
        r2 = Transform.from_structured(lons_1d, lats_1d, depth=depth, vexag=200.0)
        def _radial_extent(grid: pv.StructuredGrid) -> float:
            norms = np.linalg.norm(grid.points, axis=1)
            return float(norms.max() - norms.min())
        np.testing.assert_allclose(
            _radial_extent(r2), 2.0 * _radial_extent(r1), rtol=1e-6
        )

    def test_crs_attached(self, lons_1d, lats_1d, depth_1d, wgs84_wkt):
        """WGS84 CRS metadata must be attached to the output grid."""
        result = Transform.from_structured(lons_1d, lats_1d, depth=depth_1d)
        assert result[GV_FIELD_CRS] == wgs84_wkt


# ── Data attachment ────────────────────────────────────────────────────────────


class TestFromStructuredData:
    """Verify data arrays are correctly attached to the grid."""

    def test_cell_data_attached(self, lons_1d, lats_1d, depth_1d):
        """Named cell data is stored and retrievable from the grid."""
        nx, ny, nz = len(lons_1d), len(lats_1d), len(depth_1d)
        n_cells = (nx - 1) * (ny - 1) * (nz - 1)
        data = np.arange(n_cells, dtype=float).reshape(nz - 1, ny - 1, nx - 1)
        result = Transform.from_structured(
            lons_1d, lats_1d, depth=depth_1d, data=data, name="temp"
        )
        assert "temp" in result.array_names
        assert result["temp"].size == n_cells

    def test_point_data_attached(self, lons_1d, lats_1d, depth_1d):
        """Point data sized n_points is attached with the default name."""
        nx, ny, nz = len(lons_1d), len(lats_1d), len(depth_1d)
        n_pts = nx * ny * nz
        result = Transform.from_structured(
            lons_1d, lats_1d, depth=depth_1d, data=np.ones(n_pts)
        )
        assert result[NAME_POINTS].size == n_pts

    def test_default_name_cells(self, lons_1d, lats_1d, depth_1d):
        """Cell data without an explicit name gets the NAME_CELLS default."""
        nx, ny, nz = len(lons_1d), len(lats_1d), len(depth_1d)
        n_cells = (nx - 1) * (ny - 1) * (nz - 1)
        result = Transform.from_structured(
            lons_1d, lats_1d, depth=depth_1d, data=np.zeros(n_cells)
        )
        assert NAME_CELLS in result.array_names


# ── Error handling ────────────────────────────────────────────────────────────


class TestFromStructuredErrors:
    """Verify that invalid inputs raise clear errors."""

    def test_mismatched_2d_shapes_raises(self, lons_2d, depth_1d):
        """Mismatched 2-D lon/lat shapes must raise ValueError."""
        bad_lats = np.zeros((lons_2d.shape[0] + 1, lons_2d.shape[1]))
        with pytest.raises(ValueError, match="same shape"):
            Transform.from_structured(lons_2d, bad_lats, depth=depth_1d)

    def test_2d_lons_bad_depth_ndim_raises(self, lons_2d, lats_2d):
        """2-D depth paired with 2-D lon/lat must raise ValueError."""
        bad_depth = np.ones((2, 2))
        with pytest.raises(ValueError, match="depth must be"):
            Transform.from_structured(lons_2d, lats_2d, depth=bad_depth)

    def test_incompatible_shapes_raises(self, lons_2d, lats_2d):
        """3-D depth with incompatible spatial shape must raise ValueError."""
        wrong_depth = np.ones((3, lons_2d.shape[0] + 1, lons_2d.shape[1]))
        with pytest.raises(ValueError, match="depth must be"):
            Transform.from_structured(lons_2d, lats_2d, depth=wrong_depth)

    def test_unrecognised_ndim_raises(self):
        """4-D coordinate arrays must raise ValueError."""
        lons = np.zeros((2, 2, 2, 2))
        lats = np.zeros((2, 2, 2, 2))
        depth = np.array([0.0, 100.0])
        with pytest.raises(ValueError, match="Unrecognised"):
            Transform.from_structured(lons, lats, depth=depth)
