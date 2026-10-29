# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.from_cartesian`."""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

from geovista.bridge import Transform
from geovista.common import (
    GV_FIELD_GLOBE_RENDER_RADIUS,
    GV_FIELD_ZSCALE,
    GV_REMESH_POINT_IDS,
    REMESH_SEAM,
    ZLEVEL_SCALE,
    from_cartesian,
    to_cartesian,
    wrap,
)
from geovista.globe import Globe, _record_heights
from geovista.pantry.meshes import lfric_orog


def test_defaults(lam_uk_sample, lam_uk):
    """Test expected defaults are honoured for a mesh."""
    sample_lons, sample_lats = lam_uk_sample
    lonlats = from_cartesian(lam_uk)
    np.testing.assert_allclose(lonlats[:, 0], sample_lons)
    np.testing.assert_allclose(lonlats[:, 1], sample_lats)
    assert np.sum(lonlats[:, 2]) == 0


def test_surface_at_uneven_radii():
    """Test each point of a surface is read at its own radius, not their mean.

    See :issue:`2670`.

    """
    lons = np.array([-30.0, 0.0, 30.0, 30.0, 0.0, -30.0])
    lats = np.array([0.0, 0.0, 0.0, 45.0, 45.0, 45.0])
    xyz = to_cartesian(lons, lats, zlevel=np.linspace(0, 1, 6), zscale=1)
    mesh = pv.PolyData(xyz, faces=[4, 0, 1, 4, 5, 4, 1, 2, 3, 4])

    lonlats = from_cartesian(mesh)

    np.testing.assert_allclose(lonlats[:, 0], lons, atol=1e-12)
    np.testing.assert_allclose(lonlats[:, 1], lats, atol=1e-12)
    assert np.sum(lonlats[:, 2]) == 0


@pytest.mark.parametrize("dtype", [np.int32, np.int64])
def test_integer_points(dtype):
    """Test a surface whose points pyvista keeps as integers is read."""
    mesh = pv.PolyData(np.eye(3, dtype=dtype), faces=[3, 0, 1, 2], force_float=False)
    assert mesh.points.dtype == dtype

    lonlats = from_cartesian(mesh)

    np.testing.assert_allclose(lonlats[:, 0], [0, 90, 0])
    np.testing.assert_allclose(lonlats[:, 1], [0, 0, 90])


def test_cloud_defaults__no_field_data(lam_uk_sample, lam_uk):
    """Test expected defaults are honoured for a point-cloud."""
    sample_lons, sample_lats = lam_uk_sample
    cloud = pv.PolyData(lam_uk.points)
    lonlats = from_cartesian(cloud)
    np.testing.assert_allclose(lonlats[:, 0], sample_lons)
    np.testing.assert_allclose(lonlats[:, 1], sample_lats)
    assert np.sum(lonlats[:, 2]) == 0


def test_cloud_defaults__with_field_data(lam_uk_sample, lam_uk):
    """Test expected defaults are honoured for a point-cloud with field data."""
    sample_lons, sample_lats = lam_uk_sample
    cloud = pv.PolyData(lam_uk.points)
    cloud.copy_attributes(lam_uk)
    cloud.field_data[GV_FIELD_ZSCALE] = np.array([ZLEVEL_SCALE])
    assert GV_FIELD_GLOBE_RENDER_RADIUS in cloud.field_data
    assert GV_FIELD_ZSCALE in cloud.field_data
    lonlats = from_cartesian(cloud)
    np.testing.assert_allclose(lonlats[:, 0], sample_lons)
    np.testing.assert_allclose(lonlats[:, 1], sample_lats)
    assert np.isclose(np.sum(lonlats[:, 2]), 0)


@pytest.mark.parametrize("repeats", range(1, 11))
def test_cloud_levels(lam_uk_sample, repeats):
    """Test multiple point-cloud levels."""
    sample_lons, sample_lats = lam_uk_sample
    size = sample_lons.size
    lons = np.atleast_2d(sample_lons).repeat(repeats=repeats, axis=0)
    lats = np.atleast_2d(sample_lats).repeat(repeats=repeats, axis=0)
    zlevel = np.arange(repeats).reshape(-1, 1)
    cloud = Transform.from_points(lons, lats, zlevel=zlevel, zscale=1)
    lonlats = from_cartesian(cloud)
    for i in range(repeats):
        repeat = slice(i * size, (i + 1) * size)
        np.testing.assert_allclose(lonlats[repeat, 0], sample_lons)
        np.testing.assert_allclose(lonlats[repeat, 1], sample_lats)
        assert np.isclose(np.sum(lonlats[repeat, 2]), i * size)


@pytest.mark.parametrize("closed_interval", [False, True])
@pytest.mark.parametrize("n_lons", [10, 45, 90, 180, 270, 360])
@pytest.mark.parametrize("sign", [-1, 1])
def test_polar_quad_mesh_unfold(sign, n_lons, closed_interval):
    """Test unfolding of polar quad cells with two singularity polar points."""
    lats = np.array([90, 89]) * sign
    lons = np.linspace(-180, 180, n_lons)
    mesh = Transform.from_1d(lons, lats)
    if not closed_interval:
        lons = wrap(lons)
    else:
        remesh = np.zeros(2 * n_lons)
        remesh[[n_lons - 1, 2 * n_lons - 1]] = REMESH_SEAM
        mesh.point_data[GV_REMESH_POINT_IDS] = remesh
    lonlats = from_cartesian(mesh, closed_interval=closed_interval)
    expected = np.concatenate([lons, lons])
    np.testing.assert_allclose(lonlats[:, 0], expected)
    expected = np.concatenate([np.ones(n_lons) * lats[0], np.ones(n_lons) * lats[1]])
    np.testing.assert_allclose(lonlats[:, 1], expected)
    assert np.isclose(np.sum(lonlats[:, 2]), 0)


@pytest.mark.parametrize("closed_interval", [False, True])
@pytest.mark.parametrize(
    ("lonlat", "pids"),
    [
        (
            np.array([[170, 10], [180, 10], [-180, 0], [-170, 0]]),
            np.array([[0, 1], [2, 3]]),
        ),
        (
            np.array([[170, 0], [180, 0], [-170, 0]]),
            np.array([[0, 1], [1, 2]]),
        ),
        (
            np.array([[170, 0], [180, 0], [-180, 0], [-170, 0]]),
            np.array([[0, 1], [2, 3]]),
        ),
    ],
)
def test_lines_closed_interval(closed_interval, lonlat, pids):
    """Test antimeridian closed interval wrapping of line meshes."""
    nlines = pids.shape[0]
    lines = np.full((nlines, 3), 2, dtype=int)
    lines[:, 1:] = pids
    points = to_cartesian(lonlat[:, 0], lonlat[:, 1])
    mesh = pv.PolyData()
    mesh.points = points
    mesh.lines = lines
    result = from_cartesian(mesh, closed_interval=closed_interval)
    assert np.all(np.isclose(result[:, :-1], lonlat)) == closed_interval


def test_convert_edges_pole_cell_unfold():
    """Test edges with no polar cell associated with polar point."""
    mesh = lfric_orog()
    _, edges = mesh.contour_banded(3)
    result = from_cartesian(edges)
    assert result.shape == (edges.n_points, 3)


def test_a_cloud_decodes_from_its_globe(legacy):
    """Test a cloud's z-levels decode from the render radius it records."""
    cloud = Transform.from_points(
        [0.0, 10.0, 20.0],
        [0.0, 10.0, 20.0],
        globe=Globe(render_radius=2),
        zlevel=[1, 2, 3],
        zscale=0.1,
    )
    np.testing.assert_allclose(from_cartesian(cloud)[:, 2], [1, 2, 3])
    np.testing.assert_allclose(from_cartesian(legacy(cloud))[:, 2], [1, 2, 3])


@pytest.mark.parametrize("radius", [1.0, 6378137.0])
def test_a_small_lift_of_float32_points(radius):
    """Test a surface lifted less than the globe tolerance is read where it lies.

    A float32 surface lifted by a fraction of a z-level lies close enough to the
    globe it records for that render radius to pass for its own, which near a pole
    moves each point by hundredths of a degree. Float32 points there carry an
    error of a few thousandths of a degree of their own.

    """
    lats = [89.94, 89.95]
    mesh = Transform.from_1d(
        [0, 10, 20], lats, globe=Globe(render_radius=radius), zlevel=1, zscale=5e-7
    )
    mesh.points = mesh.points.astype(np.float32)

    lonlats = from_cartesian(mesh)

    np.testing.assert_allclose(lonlats[:, 1], np.repeat(lats, 3), atol=1e-2)


def test_a_mesh_with_heights_reports_no_level():
    """A cloud with heights carries no z-level, whatever its radii encode."""
    cloud = Transform.from_points(
        [0.0, 10.0, 20.0], [0.0, 10.0, 20.0], zlevel=[1, 2, 3]
    )
    _record_heights(cloud, [100.0, 200.0, 300.0])
    np.testing.assert_array_equal(from_cartesian(cloud)[:, 2], 0.0)
