# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.to_cartesian`."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pytest

from geovista.common import RADIUS, ZLEVEL_SCALE, to_cartesian
from geovista.globe import Globe

#: A render radius of 1, and the Earth's radius.
RADII = [1.0, 6378137.0]


def _distance(pts: npt.ArrayLike, stacked: bool = True) -> float:  # noqa: FBT001
    """Calculate the mean distance to the xyz-cartesian `pts` from the origin."""
    if np.ma.isMaskedArray(pts):
        pts = pts.data
    if not stacked:
        pts = np.transpose(pts)
    nrow, ncol = pts.shape

    return np.sqrt(np.sum(pts.T @ pts * np.identity(ncol)) / nrow)


def test_shape_fail():
    """Test trap of longitude and latitude shape mismatch."""
    lons, lats = np.arange(10), np.arange(10).reshape(5, 2)
    emsg = "Require longitudes and latitudes with same shape"
    with pytest.raises(ValueError, match=emsg):
        _ = to_cartesian(lons, lats)


def test_ndim_fail():
    """Test trap of longitude and latitude dimension."""
    lons = lats = np.array([0]).reshape(-1, 1, 1, 1)
    emsg = "Require at most 3D"
    with pytest.raises(ValueError, match=emsg):
        _ = to_cartesian(lons, lats)


def test_zlevel_broadcast_fail():
    """Test trap of zlevel shape can't broadcast with longitude/latitude."""
    lons, lats = np.arange(10), np.arange(10)
    zlevel = np.arange(2)
    emsg = "Cannot broadcast zlevel"
    with pytest.raises(ValueError, match=emsg):
        _ = to_cartesian(lons, lats, zlevel=zlevel)


def test_scalar():
    """Test scalar and single element mixture of lons/lats."""
    expected = np.array([[0.0, 0.0, 1.0]])
    np.testing.assert_array_equal(to_cartesian(0, 90), expected)
    np.testing.assert_array_equal(to_cartesian(0, [90]), expected)
    np.testing.assert_array_equal(to_cartesian([0], 90), expected)
    np.testing.assert_array_equal(to_cartesian([0], [90]), expected)


@pytest.mark.parametrize("stacked", [True, False])
def test_defaults(lam_uk_sample, stacked):
    """Test expected defaults are honoured."""
    result = to_cartesian(*lam_uk_sample, stacked=stacked)
    assert np.isclose(_distance(result, stacked=stacked), RADIUS)


@pytest.mark.parametrize("zlevel", range(-5, 6))
def test_zlevel__scalar(lam_uk_sample, zlevel):
    """Test spherical z-control with zlevel."""
    result = to_cartesian(*lam_uk_sample, zlevel=zlevel)
    actual = _distance(result)
    expected = RADIUS + RADIUS * zlevel * ZLEVEL_SCALE
    assert np.isclose(actual, expected)


@pytest.mark.parametrize(
    ("xy_reshape", "z_reshape"), [((-1,), (-1, 1)), ((1, 5, 5), (-1, 1, 1))]
)
@pytest.mark.parametrize("n_levels", range(3, 11))
def test_zlevel__broadcast(lam_uk_sample, xy_reshape, z_reshape, n_levels):
    """Test spherical z-control with zlevel broadcast."""
    lons, lats = lam_uk_sample
    (npts,) = lons.shape
    vlons = np.vstack([lons.reshape(*xy_reshape)] * n_levels)
    vlats = np.vstack([lats.reshape(*xy_reshape)] * n_levels)
    mid = n_levels // 2
    zlevel = np.arange(-mid, n_levels - mid)
    result = to_cartesian(vlons, vlats, zlevel=zlevel.reshape(*z_reshape))
    assert result.ndim == 2
    assert result.shape[0] == n_levels * npts
    for i in range(n_levels):
        actual = _distance(result[i * npts : (i + 1) * npts])
        expected = RADIUS + RADIUS * zlevel[i] * ZLEVEL_SCALE
        assert np.isclose(actual, expected)


@pytest.mark.parametrize("zlevel", [0, 1])
@pytest.mark.parametrize("zscale", np.linspace(-1, 1, num=5))
def test_zscale(lam_uk_sample, zlevel, zscale):
    """Test spherical z-control with zscale."""
    lons, lats = lam_uk_sample
    (npts,) = lons.shape
    result = to_cartesian(lons, lats, zlevel=zlevel, zscale=zscale)
    assert result.ndim == 2
    assert result.shape[0] == npts
    actual = _distance(result)
    expected = RADIUS + RADIUS * zlevel * zscale
    assert np.isclose(actual, expected)


@pytest.mark.parametrize("radius", RADII)
def test_the_globe_sets_the_radius(lam_uk_sample, radius):
    """Test the points lie at the render radius of the globe given."""
    result = to_cartesian(*lam_uk_sample, globe=Globe(render_radius=radius))
    np.testing.assert_allclose(np.linalg.norm(result, axis=1), radius, rtol=1e-12)


def test_a_number_is_not_a_globe():
    """Test a number given as the globe is refused."""
    with pytest.raises(TypeError, match=r"globe must be a geovista\.Globe"):
        _ = to_cartesian([0], [0], globe=2.0)


def test_radius_is_gone():
    """Test the radius keyword is refused."""
    with pytest.raises(TypeError, match="radius"):
        _ = to_cartesian([0], [0], radius=2.0)
