# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.Transform.to_structured_grid`."""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

from geovista.bridge import NAME_CELLS, NAME_POINTS, Transform
from geovista.common import GV_FIELD_CRS, RADIUS

# ── Shared fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def simple_inputs():
    """Minimal lon/lat/depth arrays: 4x3x3 points giving 3x2x2 cells."""
    xs = np.linspace(-10.0, 10.0, 4)  # 4 lon points  -> 3 lon cells
    ys = np.linspace(-5.0, 5.0, 3)  # 3 lat points  -> 2 lat cells
    zs = np.array([0.0, -0.01, -0.02])  # 3 depth points -> 2 depth cells
    return xs, ys, zs


# ── Return type and basic shape ────────────────────────────────────────────────


class TestToStructuredGridBasics:
    """Verify basic output type and grid dimensions."""

    def test_returns_structured_grid(self, simple_inputs):
        """Return type must be StructuredGrid."""
        xs, ys, zs = simple_inputs
        result = Transform.to_structured_grid(xs, ys, zs)
        assert isinstance(result, pv.StructuredGrid)

    def test_crs_attached(self, simple_inputs, wgs84_wkt):
        """WGS84 CRS metadata must be attached to the output grid."""
        xs, ys, zs = simple_inputs
        result = Transform.to_structured_grid(xs, ys, zs)
        assert result[GV_FIELD_CRS] == wgs84_wkt

    def test_point_count(self, simple_inputs):
        """Point count must equal len(xs) * len(ys) * len(zs)."""
        xs, ys, zs = simple_inputs
        result = Transform.to_structured_grid(xs, ys, zs)
        assert result.n_points == len(xs) * len(ys) * len(zs)

    def test_cell_count(self, simple_inputs):
        """Cell count must equal (nx-1) * (ny-1) * (nz-1)."""
        xs, ys, zs = simple_inputs
        result = Transform.to_structured_grid(xs, ys, zs)
        expected = (len(xs) - 1) * (len(ys) - 1) * (len(zs) - 1)
        assert result.n_cells == expected

    def test_minimal_two_points_per_dim(self):
        """Two points per dimension produces exactly one cell."""
        xs = np.array([0.0, 1.0])
        ys = np.array([0.0, 1.0])
        zs = np.array([0.0, -0.01])
        result = Transform.to_structured_grid(xs, ys, zs)
        assert result.n_cells == 1


# ── Depth-to-radius mapping ────────────────────────────────────────────────────


class TestDepthRadiusMapping:
    """Verify that zs values map correctly to sphere radii.

    The proportional model is: r = radius * (1 + zs_val)
    - zs_val = 0.0  -> r = RADIUS  (on the surface)
    - zs_val < 0.0  -> r < RADIUS  (below the surface, i.e. depth)
    - zs_val > 0.0  -> r > RADIUS  (above the surface, i.e. altitude)
    """

    def test_negative_zs_reduce_radius(self):
        """Depth levels (zs < 0) must produce radii smaller than RADIUS."""
        xs = np.array([-5.0, 0.0, 5.0])
        ys = np.array([-5.0, 0.0, 5.0])
        zs = np.array([-0.01, -0.02])
        result = Transform.to_structured_grid(xs, ys, zs)
        radii = np.linalg.norm(result.points, axis=1)
        assert np.all(radii < RADIUS)

    def test_positive_zs_increase_radius(self):
        """Altitude levels (zs > 0) must produce radii larger than RADIUS."""
        xs = np.array([-5.0, 0.0, 5.0])
        ys = np.array([-5.0, 0.0, 5.0])
        zs = np.array([0.01, 0.02])
        result = Transform.to_structured_grid(xs, ys, zs)
        radii = np.linalg.norm(result.points, axis=1)
        assert np.all(radii > RADIUS)

    def test_zs_zero_gives_surface_radius(self):
        """Points at zs=0 should lie exactly on the base sphere.

        All points on the same spherical shell have identical Euclidean
        distance from the origin, so we verify the unique radius values
        rather than relying on a particular point ordering.
        """
        xs = np.array([-5.0, 0.0, 5.0])
        ys = np.array([-5.0, 0.0, 5.0])
        zs = np.array([0.0, -0.01])
        result = Transform.to_structured_grid(xs, ys, zs)
        radii = np.linalg.norm(result.points, axis=1)
        # Expect exactly two shells: RADIUS and RADIUS*0.99
        unique_radii = np.sort(np.unique(radii.round(8)))[::-1]
        np.testing.assert_allclose(unique_radii[0], RADIUS, rtol=1e-6)

    def test_zs_values_are_honored_not_replaced(self):
        """REGRESSION: zs must be used as-is, not replaced by np.arange.

        If the bug where zs is replaced with np.arange is present, two grids
        with the same *shape* but different *values* will produce identical
        radii.  After the fix, deeper zs must yield strictly smaller radii.
        """
        xs = np.array([0.0, 1.0])
        ys = np.array([0.0, 1.0])

        grid_1pct = Transform.to_structured_grid(xs, ys, np.array([0.0, -0.01]))
        grid_10pct = Transform.to_structured_grid(xs, ys, np.array([0.0, -0.10]))

        min_r_1pct = np.linalg.norm(grid_1pct.points, axis=1).min()
        min_r_10pct = np.linalg.norm(grid_10pct.points, axis=1).min()

        assert min_r_10pct < min_r_1pct, (
            "Deeper zs must produce smaller radii. "
            "If both grids give the same min radius the bug is still present."
        )

    def test_absolute_radius_values(self):
        """The absolute radius at each depth level matches the analytic formula.

        All points on one spherical shell share the same Euclidean radius, so we
        compare sorted unique radii to the sorted expected values.
        """
        xs = np.array([0.0, 1.0])
        ys = np.array([0.0, 1.0])
        depths = np.array([0.0, -0.01, -0.05, -0.10])
        result = Transform.to_structured_grid(xs, ys, depths)

        unique_radii = np.sort(
            np.unique(np.linalg.norm(result.points, axis=1).round(8))
        )
        expected = np.sort([RADIUS * (1.0 + d) for d in depths])
        np.testing.assert_allclose(unique_radii, expected, rtol=1e-5)

    def test_monotonically_decreasing_radii_with_depth(self):
        """Monotonically decreasing zs must produce monotonically decreasing radii.

        Each distinct zs value maps to a unique spherical shell; checking the
        sorted unique radii avoids any dependency on PyVista's internal point
        ordering.
        """
        xs = np.array([0.0, 1.0])
        ys = np.array([0.0, 1.0])
        zs = np.array([0.0, -0.01, -0.05, -0.10])
        result = Transform.to_structured_grid(xs, ys, zs)

        unique_radii = np.sort(
            np.unique(np.linalg.norm(result.points, axis=1).round(8))
        )[::-1]  # largest first = surface first
        assert len(unique_radii) == len(zs), (
            "Each zs value must produce a distinct shell"
        )
        np.testing.assert_array_less(
            np.diff(unique_radii),
            0,
            err_msg="Unique radii must decrease monotonically with depth",
        )


# ── Input validation ───────────────────────────────────────────────────────────


class TestToStructuredGridValidation:
    """Verify that invalid inputs raise informative errors."""

    @pytest.mark.parametrize(
        ("xs", "ys", "zs"),
        [
            (np.array([0.0]), np.array([0.0, 1.0]), np.array([0.0, 1.0])),
            (np.array([0.0, 1.0]), np.array([0.0]), np.array([0.0, 1.0])),
            (np.array([0.0, 1.0]), np.array([0.0, 1.0]), np.array([0.0])),
        ],
        ids=["too-few-xs", "too-few-ys", "too-few-zs"],
    )
    def test_raises_on_too_few_points(self, xs, ys, zs):
        """Fewer than 2 points in any dimension must raise ValueError."""
        with pytest.raises(ValueError, match="at least two points"):
            Transform.to_structured_grid(xs, ys, zs)

    @pytest.mark.parametrize(
        ("xs", "ys", "zs"),
        [
            (np.array([[0.0, 1.0]]), np.array([0.0, 1.0]), np.array([0.0, 1.0])),
            (np.array([0.0, 1.0]), np.array([[0.0, 1.0]]), np.array([0.0, 1.0])),
            (np.array([0.0, 1.0]), np.array([0.0, 1.0]), np.array([[0.0, 1.0]])),
        ],
        ids=["2d-xs", "2d-ys", "2d-zs"],
    )
    def test_raises_on_non_1d_inputs(self, xs, ys, zs):
        """Non-1D inputs must raise ValueError."""
        with pytest.raises(ValueError, match="all-1D"):
            Transform.to_structured_grid(xs, ys, zs)

    def test_raises_on_non_wgs84_crs(self):
        """Non-WGS84 CRS is not yet supported and should raise."""
        xs = np.linspace(-180.0, 180.0, 4)
        ys = np.linspace(-90.0, 90.0, 3)
        zs = np.array([0.0, -0.01])
        with pytest.raises(ValueError, match="WGS84"):
            Transform.to_structured_grid(xs, ys, zs, crs="+proj=eqc")


# ── Data attachment ────────────────────────────────────────────────────────────


class TestToStructuredGridData:
    """Verify data can be attached to cells or points."""

    def test_attach_cell_data(self, simple_inputs):
        """Cell-sized data is attached under NAME_CELLS."""
        xs, ys, zs = simple_inputs
        ref = Transform.to_structured_grid(xs, ys, zs)
        data = np.arange(ref.n_cells, dtype=float)
        result = Transform.to_structured_grid(xs, ys, zs, data=data)
        assert NAME_CELLS in result.cell_data
        np.testing.assert_array_equal(result[NAME_CELLS], data)

    def test_attach_point_data(self, simple_inputs):
        """Point-sized data is attached under NAME_POINTS."""
        xs, ys, zs = simple_inputs
        ref = Transform.to_structured_grid(xs, ys, zs)
        data = np.arange(ref.n_points, dtype=float)
        result = Transform.to_structured_grid(xs, ys, zs, data=data)
        assert NAME_POINTS in result.point_data
        np.testing.assert_array_equal(result[NAME_POINTS], data)

    def test_named_data(self, simple_inputs):
        """Explicitly named data is stored under the given key."""
        xs, ys, zs = simple_inputs
        ref = Transform.to_structured_grid(xs, ys, zs)
        data = np.arange(ref.n_cells, dtype=float)
        result = Transform.to_structured_grid(xs, ys, zs, data=data, name="temperature")
        assert "temperature" in result.cell_data


# ── Custom radius ──────────────────────────────────────────────────────────────


class TestToStructuredGridRadius:
    """Verify that a custom radius is honoured."""

    def test_custom_radius_scales_output(self):
        """Providing radius=2.0 should scale all point distances from origin."""
        xs = np.array([-5.0, 0.0, 5.0])
        ys = np.array([-5.0, 0.0, 5.0])
        zs = np.array([0.0, -0.01])
        r = 2.0
        result = Transform.to_structured_grid(xs, ys, zs, radius=r)

        unique_radii = np.sort(
            np.unique(np.linalg.norm(result.points, axis=1).round(8))
        )[::-1]
        # Surface shell: r * (1 + 0) = 2.0
        np.testing.assert_allclose(unique_radii[0], r, rtol=1e-6)
        # Depth shell: r * (1 - 0.01) = 1.98
        np.testing.assert_allclose(unique_radii[1], r * (1.0 - 0.01), rtol=1e-5)
