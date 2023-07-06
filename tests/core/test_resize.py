"""Unit-tests for :func:`geovista.core.resize`."""
import operator

import numpy as np
from numpy.testing import assert_array_equal
import pytest
import pyvista as pv

from geovista.bridge import Transform
from geovista.common import (
    GV_FIELD_RADIUS,
    GV_FIELD_ZSCALE,
    RADIUS,
    ZLEVEL_SCALE,
    distance,
)
from geovista.core import resize


def test_projection_fail():
    """Test trap of mesh that is not spherical."""
    mesh = pv.Plane()
    emsg = "Cannot resize a mesh that has been projected"
    with pytest.raises(ValueError, match=emsg):
        _ = resize(mesh)


@pytest.mark.parametrize("lfric", ["c48", "c96", "c192"], indirect=True)
def test_no_resize(lfric):
    """Test resize not performed due to no radius difference."""
    result = resize(lfric)
    assert id(result) == id(lfric)
    assert_array_equal(result.points, lfric.points)


@pytest.mark.parametrize("inplace", [False, True])
@pytest.mark.parametrize(
    "radius",
    (np.round(value, decimals=1) for value in np.linspace(RADIUS / 10, 2 * RADIUS, 20)),
)
def test_resize(lfric, radius, inplace):
    """Test resize mesh by new radius."""
    result = resize(lfric, radius=radius, inplace=inplace)
    compare = operator.eq if inplace or np.isclose(radius, RADIUS) else operator.ne
    assert compare(id(result), id(lfric))
    assert np.isclose(distance(result), radius)


@pytest.mark.parametrize("zlevel", range(-10, 11))
def test_resize__zlevel(lfric, zlevel):
    """Test resize mesh by new zlevel."""
    result = resize(lfric, zlevel=zlevel)
    expected = RADIUS + RADIUS * zlevel * ZLEVEL_SCALE
    compare = operator.eq if np.isclose(expected, RADIUS) else operator.ne
    assert compare(id(result), id(lfric))
    actual = distance(result)
    assert np.isclose(actual, expected)


@pytest.mark.parametrize("zscale", np.linspace(-1, 1))
def test_resize__zscale(lfric, zscale):
    """Test resize mesh by new zscale."""
    result = resize(lfric, zlevel=1, zscale=zscale)
    expected = RADIUS + RADIUS * zscale or RADIUS
    compare = operator.eq if np.isclose(expected, RADIUS) else operator.ne
    assert compare(id(result), id(lfric))
    actual = distance(result)
    assert np.isclose(actual, expected)


def test_resize_cloud__inject_metadata(lam_uk):
    """Test inclusion of field data metadata."""
    cloud = pv.PolyData(lam_uk.points)
    assert GV_FIELD_RADIUS not in cloud.field_data
    assert GV_FIELD_ZSCALE not in cloud.field_data
    result = resize(cloud)
    assert GV_FIELD_RADIUS in result.field_data
    assert GV_FIELD_ZSCALE in result.field_data
    assert id(cloud) != id(result)
    assert np.isclose(result[GV_FIELD_RADIUS], RADIUS)
    assert np.isclose(result[GV_FIELD_ZSCALE], ZLEVEL_SCALE)


@pytest.mark.parametrize("zlevel", range(1, 11))
def test_resize_cloud__zlevel(lam_uk_sample, zlevel):
    """Test resize cloud points by new zlevel."""
    lons, lats = lam_uk_sample
    zscale = 1
    cloud = Transform.from_points(lons, lats, zscale=zscale)
    assert np.isclose(cloud[GV_FIELD_RADIUS], RADIUS)
    assert np.isclose(cloud[GV_FIELD_ZSCALE], zscale)
    result = resize(cloud, zlevel=zlevel)
    assert np.isclose(distance(result), RADIUS + zlevel * zscale)
    assert id(cloud) != id(result)


@pytest.mark.parametrize("zscale", np.linspace(-1, 1))
def test_resize_cloud__zscale(lam_uk_cloud, zscale):
    """Test resize cloud points by new zscale."""
    zlevel = 1
    assert np.isclose(lam_uk_cloud[GV_FIELD_RADIUS], RADIUS)
    assert np.isclose(lam_uk_cloud[GV_FIELD_ZSCALE], ZLEVEL_SCALE)
    result = resize(lam_uk_cloud, zlevel=zlevel, zscale=zscale)
    assert np.isclose(distance(result), RADIUS + zlevel * zscale)
    assert np.isclose(result[GV_FIELD_RADIUS], RADIUS)
    assert np.isclose(result[GV_FIELD_ZSCALE], zscale)
    assert id(lam_uk_cloud) != id(result)


@pytest.mark.parametrize("radius", np.linspace(0.5, 1.5))
def test_resize_cloud__radius(lam_uk_cloud, radius):
    """Test resize cloud points by new radius."""
    assert np.isclose(lam_uk_cloud[GV_FIELD_RADIUS], RADIUS)
    assert np.isclose(lam_uk_cloud[GV_FIELD_ZSCALE], ZLEVEL_SCALE)
    result = resize(lam_uk_cloud, radius=radius)
    assert np.isclose(distance(result), radius)
    assert np.isclose(result[GV_FIELD_RADIUS], radius)
    assert np.isclose(result[GV_FIELD_ZSCALE], ZLEVEL_SCALE)
