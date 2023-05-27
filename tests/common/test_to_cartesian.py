"""Unit-tests for :func:`geovista.common.to_cartesian`."""
import numpy as np
import numpy.typing as npt
import pytest

from geovista.common import DISTANCE_DECIMALS, RADIUS, ZLEVEL_SCALE, to_cartesian


def _distance(
    pts: npt.ArrayLike, stacked: bool = True, decimals: int = DISTANCE_DECIMALS
) -> float:
    """Calculate the mean distance to the xyz-cartesian `pts` from the origin."""
    if np.ma.isMaskedArray(pts):
        pts = pts.data
    if not stacked:
        pts = np.transpose(pts)
    nrow, ncol = pts.shape
    result = np.round(
        np.sqrt(np.sum(pts.T @ pts * np.identity(ncol)) / nrow), decimals=decimals
    )
    return result


def test_shape_fail():
    """Test trap of longitude and latitude shape mismatch."""
    lons, lats = np.arange(10), np.arange(10).reshape(5, 2)
    emsg = "Require longitudes and latitudes with same shape"
    with pytest.raises(ValueError, match=emsg):
        _ = to_cartesian(lons, lats)


def test_ndim_fail():
    """Test trap of longitude and latitude dimension."""
    lons = lats = np.array([0]).reshape(-1, 1, 1, 1)
    emsg = "Require at most 3-D"
    with pytest.raises(ValueError, match=emsg):
        _ = to_cartesian(lons, lats)


def test_zlevel_broadcast_fail():
    """Test trap of zlevel shape can't broadcast with longitude/latitude."""
    lons, lats = np.arange(10), np.arange(10)
    zlevel = np.arange(2)
    emsg = "Cannot broadcast zlevel"
    with pytest.raises(ValueError, match=emsg):
        _ = to_cartesian(lons, lats, zlevel=zlevel)


@pytest.mark.parametrize("stacked", [True, False])
def test_defaults(lam_uk_sample, stacked):
    """Test expected defaults are honoured."""
    result = to_cartesian(*lam_uk_sample, stacked=stacked)
    assert _distance(result, stacked=stacked) == RADIUS


@pytest.mark.parametrize("zlevel", range(-5, 6))
def test_zlevel__scalar(lam_uk_sample, zlevel):
    """Test spherical z-control with zlevel."""
    result = to_cartesian(*lam_uk_sample, zlevel=zlevel)
    actual = _distance(result)
    expected = RADIUS + RADIUS * zlevel * ZLEVEL_SCALE
    assert np.isclose(actual, expected)


@pytest.mark.parametrize(
    "xy_reshape, z_reshape", [((-1,), (-1, 1)), ((1, 5, 5), (-1, 1, 1))]
)
@pytest.mark.parametrize("n_levels", range(3, 11))
def test_zlevel__broadcast(lam_uk_sample, xy_reshape, z_reshape, n_levels):
    """Test spherical z-control with zlevel broadcast."""
    lons, lats = lam_uk_sample
    (npts,) = lons.shape
    vlons = np.vstack([lons[:].reshape(*xy_reshape)] * n_levels)
    vlats = np.vstack([lats[:].reshape(*xy_reshape)] * n_levels)
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
