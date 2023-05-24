"""Unit-tests for :func:`geovista.geodesic.line`."""
import numpy as np
import pytest

from geovista.common import RADIUS, ZLEVEL_SCALE, distance, to_spherical
from geovista.geodesic import GEODESIC_NPTS, line


@pytest.mark.parametrize(
    "lons, lats",
    [(range(10), range(20)), (list(range(10)), list(range(20)))],
)
def test_lons_lats__size_unequal_fail(lons, lats):
    """Test trap of lons and lats containing different number of points each."""
    emsg = "Require the same number"
    with pytest.raises(ValueError, match=emsg):
        _ = line(lons, lats)


@pytest.mark.parametrize(
    "lons, lats",
    [(0, 1), ([0], [1])],
)
def test_lons_lats__size_minimal_fail(lons, lats):
    """Test trap of not enough points to render a line."""
    emsg = "containing at least 2 longitude/latitude"
    with pytest.raises(ValueError, match=emsg):
        _ = line(lons, lats)


def test_lons_lats__loop_minimal_fail():
    """Test trap of a closed line (loop) not containing enough points."""
    lons = lats = [0, 0]
    emsg = "containing at least 3 longitude/latitude"
    with pytest.raises(ValueError, match=emsg):
        _ = line(lons, lats)


@pytest.mark.parametrize(
    "nsamples, npts",
    [(2, None), (2, 64), (3, 128), (4, 256), (8, 512)],
)
def test_npts(nsamples, npts):
    """Test line containing various number of segments at increasing resolution."""
    lons = lats = range(nsamples)
    result = line(lons, lats, npts=npts)
    if npts is None:
        npts = GEODESIC_NPTS
    n_points = (nsamples - 1) * npts + 1
    assert result.n_points == n_points


@pytest.mark.parametrize(
    "nsamples",
    range(2, 11),
)
def test_contains_sample_points(lfric_sst, nsamples):
    """Test resulting line must contain the original sample points."""
    lons = lats = range(nsamples)
    result = line(lons, lats)
    radius = RADIUS + RADIUS * ZLEVEL_SCALE
    xyz = to_spherical(lons, lats, radius=radius)
    np.testing.assert_array_equal(xyz, result.points[::GEODESIC_NPTS])
    result = line(lons, lats, surface=lfric_sst)
    np.testing.assert_array_equal(xyz, result.points[::GEODESIC_NPTS])


@pytest.mark.parametrize(
    "lons, lats",
    [
        (0, [90, 0, -90]),
        ([0], (90, 45, 0, -45, -90)),
        ([0, 90, 180], 0),
        ([0, 45, 90, 135, 180], [0]),
    ],
)
def test_auto_repeat(lons, lats):
    """Test the auto-repeat convenience for lons or lats generation."""
    result = line(lons, lats)
    lons, lats = np.asanyarray(lons), np.asanyarray(lats)
    n_samples = np.max([lons.size, lats.size])
    n_points = (n_samples - 1) * GEODESIC_NPTS + 1
    assert result.n_points == n_points


@pytest.mark.parametrize("lons", range(0, 405, 45))
@pytest.mark.parametrize("zlevel", range(-10, 11))
def test_zlevel(lons, zlevel):
    """Test line z-control with zlevel."""
    result = line(lons, [90, 0, -90], zlevel=zlevel)
    actual = distance(result)
    expected = RADIUS + RADIUS * zlevel * ZLEVEL_SCALE
    assert np.isclose(actual, expected)


@pytest.mark.parametrize("lons", range(0, 405, 45))
@pytest.mark.parametrize("zscale", np.linspace(-1, 1))
def test_zscale(lons, zscale):
    """Test line z-control with zscale."""
    result = line(180, [90, 0, -90], zscale=zscale)
    actual = distance(result)
    expected = RADIUS + RADIUS * zscale
    assert np.isclose(actual, expected)
