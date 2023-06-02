"""Unit-tests for :func:`geovista.common.from_cartesian`."""
import numpy as np
import pytest
import pyvista as pv

from geovista.bridge import Transform
from geovista.common import (
    GV_FIELD_RADIUS,
    GV_FIELD_ZSCALE,
    GV_REMESH_POINT_IDS,
    REMESH_SEAM,
    ZLEVEL_SCALE,
    from_cartesian,
    wrap,
)


def test_defaults(lam_uk_sample, lam_uk):
    """Test expected defaults are honoured for a mesh."""
    sample_lons, sample_lats = lam_uk_sample
    lonlats = from_cartesian(lam_uk)
    np.testing.assert_allclose(lonlats[:, 0], sample_lons)
    np.testing.assert_allclose(lonlats[:, 1], sample_lats)
    assert np.sum(lonlats[:, 2]) == 0


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
    assert GV_FIELD_RADIUS in cloud.field_data
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
