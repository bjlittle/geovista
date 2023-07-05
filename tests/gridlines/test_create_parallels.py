"""Unit-tests for :func:`geovista.gridlines.create_parallels`."""
import numpy as np
import pytest

from geovista.common import (
    GV_FIELD_CRS,
    RADIUS,
    ZLEVEL_SCALE,
    distance,
    from_cartesian,
)
from geovista.crs import WGS84, from_wkt
from geovista.gridlines import (
    GRATICULE_ZLEVEL,
    LATITUDE_N_SAMPLES,
    LATITUDE_START,
    LATITUDE_STEP,
    LATITUDE_STOP,
    LONGITUDE_START,
    LONGITUDE_STEP,
    LONGITUDE_STOP,
    create_parallel_labels,
    create_parallels,
)


@pytest.mark.parametrize("step", [-1, 0])
def test_step_fail(step):
    """Test trap of invalid step value."""
    emsg = "Require a non-zero positive value"
    with pytest.raises(ValueError, match=emsg):
        _ = create_parallels(step=step)


@pytest.mark.parametrize("lon_step", [-1, 0])
def test_lon_step_fail(lon_step):
    """Test trap of invalid longitude step value."""
    emsg = "Require a non-zero positive value"
    with pytest.raises(ValueError, match=emsg):
        _ = create_parallels(lon_step=lon_step)


@pytest.mark.parametrize(
    "n_samples", [LATITUDE_N_SAMPLES // 2, LATITUDE_N_SAMPLES, 2 * LATITUDE_N_SAMPLES]
)
@pytest.mark.parametrize("zlevel", [None, 1, 10])
@pytest.mark.parametrize("poles_label", [False, True])
def test_core(n_samples, zlevel, poles_label):
    """Test core behaviour of parallel generation."""
    result = create_parallels(
        n_samples=n_samples, poles_label=poles_label, zlevel=zlevel
    )
    # purge the poles by default
    parallel_lats = np.arange(
        LATITUDE_START, LATITUDE_STOP + LATITUDE_STEP, LATITUDE_STEP
    )[1:-1]
    parallels = [str(lat) for lat in parallel_lats]
    # check the parallel latitudes
    assert result.blocks.keys() == parallels
    # check the parallel meshes (blocks)
    for parallel in parallels:
        mesh = result.blocks[parallel]
        assert mesh.n_points == n_samples
        assert mesh.n_cells == n_samples
        assert mesh.n_lines == n_samples
        lonlat = from_cartesian(mesh)
        lats = np.unique(lonlat[:, 1])
        assert lats.size == 1
        assert np.isclose(lats, float(parallel))
        if zlevel is None:
            zlevel = GRATICULE_ZLEVEL
        expected_radius = RADIUS + (RADIUS * ZLEVEL_SCALE * zlevel)
        assert np.isclose(distance(mesh), expected_radius)
        assert GV_FIELD_CRS in mesh.field_data
        assert from_wkt(mesh) == WGS84
    # check the parallel label points (lonlat)
    label_lons = np.arange(LONGITUDE_START, LONGITUDE_STOP, LONGITUDE_STEP) + (
        LONGITUDE_STEP / 2
    )
    n_lons, n_lats = label_lons.size, parallel_lats.size
    n_points = n_lons * n_lats
    if poles_label:
        label_lons = np.sort(np.concatenate([label_lons, [0]]))
        parallel_lats = np.sort(np.concatenate([parallel_lats, [90.0, -90]]))
        n_points += 2
    assert result.lonlat.shape == (n_points, 2)
    np.testing.assert_array_equal(np.unique(result.lonlat[:, 0]), label_lons)
    np.testing.assert_array_equal(np.unique(result.lonlat[:, 1]), parallel_lats)
    # check the parallel labels (labels)
    actual_labels = np.unique(result.labels)
    expected_labels = create_parallel_labels(list(parallel_lats), poles_parallel=True)
    np.testing.assert_array_equal(actual_labels, np.sort(expected_labels))


@pytest.mark.parametrize("lon_step", [None, 15, 30, 60])
def test_lon_step(lon_step):
    """Test parallel label generation over different lon_step's."""
    result = create_parallels(lon_step=lon_step)
    if lon_step is None:
        lon_step = LONGITUDE_STEP
    parallel_lats = np.arange(
        LATITUDE_START, LATITUDE_STOP + LATITUDE_STEP, LATITUDE_STEP
    )[1:-1]
    # check the parallel label points (lonlat)
    label_lons = np.arange(LONGITUDE_START, LONGITUDE_STOP, lon_step) + (lon_step / 2)
    n_lons, n_lats = label_lons.size, parallel_lats.size
    n_points = n_lons * n_lats
    # assumes poles_label=True by default
    label_lons = np.sort(np.concatenate([label_lons, [0]]))
    parallel_lats = np.sort(np.concatenate([parallel_lats, [90.0, -90]]))
    n_points += 2
    assert result.lonlat.shape == (n_points, 2)
    np.testing.assert_array_equal(np.unique(result.lonlat[:, 0]), label_lons)
    np.testing.assert_array_equal(np.unique(result.lonlat[:, 1]), parallel_lats)
    # check the parallel labels (labels)
    actual_labels = np.unique(result.labels)
    expected_labels = create_parallel_labels(list(parallel_lats), poles_parallel=True)
    np.testing.assert_array_equal(actual_labels, np.sort(expected_labels))


def test_poles_parallel():
    """Test parallel generation including poles."""
    result = create_parallels(poles_parallel=True)
    # retain the poles
    parallel_lats = np.arange(
        LATITUDE_START, LATITUDE_STOP + LATITUDE_STEP, LATITUDE_STEP
    )
    parallels = [str(lat) for lat in parallel_lats]
    # check the parallel latitudes
    assert result.blocks.keys() == parallels
    # check the parallel meshes (blocks)
    for parallel in parallels:
        mesh = result.blocks[parallel]
        assert mesh.n_points == LATITUDE_N_SAMPLES
        assert mesh.n_cells == LATITUDE_N_SAMPLES
        assert mesh.n_lines == LATITUDE_N_SAMPLES
        lonlat = from_cartesian(mesh)
        lats = np.unique(lonlat[:, 1])
        assert lats.size == 1
        assert np.isclose(lats, float(parallel))
        assert GV_FIELD_CRS in mesh.field_data
        assert from_wkt(mesh) == WGS84
    # check the parallel label points (lonlat)
    label_lons = np.arange(LONGITUDE_START, LONGITUDE_STOP, LONGITUDE_STEP) + (
        LONGITUDE_STEP / 2
    )
    n_lons, n_lats = label_lons.size, parallel_lats.size
    n_points = n_lons * n_lats
    assert result.lonlat.shape == (n_points, 2)
    np.testing.assert_array_equal(np.unique(result.lonlat[:, 0]), label_lons)
    np.testing.assert_array_equal(np.unique(result.lonlat[:, 1]), parallel_lats)
    # # check the parallel labels (labels)
    actual_labels = np.unique(result.labels)
    expected_labels = create_parallel_labels(list(parallel_lats), poles_parallel=True)
    np.testing.assert_array_equal(actual_labels, np.sort(expected_labels))
