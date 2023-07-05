"""Unit-tests for :func:`geovista.gridlines.create_meridians`."""
import numpy as np
import pytest

from geovista.common import (
    GV_FIELD_CRS,
    GV_REMESH_POINT_IDS,
    RADIUS,
    REMESH_SEAM,
    ZLEVEL_SCALE,
    distance,
    from_cartesian,
)
from geovista.crs import WGS84, from_wkt
from geovista.gridlines import (
    GRATICULE_ZLEVEL,
    LATITUDE_START,
    LATITUDE_STEP,
    LATITUDE_STOP,
    LONGITUDE_N_SAMPLES,
    LONGITUDE_START,
    LONGITUDE_STEP,
    LONGITUDE_STOP,
    create_meridian_labels,
    create_meridians,
)


@pytest.mark.parametrize("step", [-1, 0])
def test_step_fail(step):
    """Test trap of invalid step value."""
    emsg = "Require a non-zero positive value"
    with pytest.raises(ValueError, match=emsg):
        _ = create_meridians(step=step)


@pytest.mark.parametrize("lat_step", [-1, 0])
def test_lat_step_fail(lat_step):
    """Test trap of invalid latitude step value."""
    emsg = "Require a non-zero positive value"
    with pytest.raises(ValueError, match=emsg):
        _ = create_meridians(lat_step=lat_step)


@pytest.mark.parametrize(
    "n_samples",
    [LONGITUDE_N_SAMPLES // 2, LONGITUDE_N_SAMPLES, 2 * LONGITUDE_N_SAMPLES],
)
@pytest.mark.parametrize("zlevel", [None, 1, 10])
@pytest.mark.parametrize("step", [None, 15, 30])
def test_core(n_samples, zlevel, step):
    """Test core behaviour of meridian generation."""
    result = create_meridians(step=step, n_samples=n_samples, zlevel=zlevel)
    if step is None:
        step = LONGITUDE_STEP
    meridian_lons = np.arange(LONGITUDE_START, LONGITUDE_STOP, step)
    meridians = [str(lon) for lon in meridian_lons]
    # check the meridian longitudes
    assert result.blocks.keys() == meridians
    # check the meridian meshes (blocks)
    for meridian in meridians:
        mesh = result.blocks[meridian]
        assert mesh.n_points == n_samples
        assert mesh.n_cells == (n_lines := n_samples - 1)
        assert mesh.n_lines == n_lines
        lonlat = from_cartesian(mesh)
        lons = np.unique(lonlat[:, 0])
        assert lons.size == 1
        assert np.isclose(lons, float(meridian))
        if zlevel is None:
            zlevel = GRATICULE_ZLEVEL
        expected_radius = RADIUS + (RADIUS * ZLEVEL_SCALE * zlevel)
        assert np.isclose(distance(mesh, mean=True), expected_radius)
        assert GV_FIELD_CRS in mesh.field_data
        assert from_wkt(mesh) == WGS84
    # check the meridian label points (lonlat)
    label_lats = np.arange(LATITUDE_START, LATITUDE_STOP, LATITUDE_STEP) + (
        LATITUDE_STEP / 2
    )
    n_lons, n_lats = meridian_lons.size, label_lats.size
    assert result.lonlat.shape == (n_lons * n_lats, 2)
    np.testing.assert_array_equal(np.unique(result.lonlat[:, 0]), meridian_lons)
    np.testing.assert_array_equal(np.unique(result.lonlat[:, 1]), label_lats)
    # check the meridian labels (labels)
    actual_labels = np.unique(result.labels)
    expected_labels = create_meridian_labels(list(meridian_lons))
    np.testing.assert_array_equal(actual_labels, np.sort(expected_labels))


@pytest.mark.parametrize("lat_step", [None, 15, 30])
def test_lat_step(lat_step):
    """Test meridian label generation over different lat_step's."""
    result = create_meridians(lat_step=lat_step)
    if lat_step is None:
        lat_step = LATITUDE_STEP
    meridian_lons = np.arange(LONGITUDE_START, LONGITUDE_STOP, LONGITUDE_STEP)
    # check the meridian label points (lonlat)
    label_lats = np.arange(LATITUDE_START, LATITUDE_STOP, lat_step) + (lat_step / 2)
    n_lons, n_lats = meridian_lons.size, label_lats.size
    assert result.lonlat.shape == (n_lons * n_lats, 2)
    np.testing.assert_array_equal(np.unique(result.lonlat[:, 0]), meridian_lons)
    np.testing.assert_array_equal(np.unique(result.lonlat[:, 1]), label_lats)
    # check the meridian labels (labels)
    actual_labels = np.unique(result.labels)
    expected_labels = create_meridian_labels(list(meridian_lons))
    np.testing.assert_array_equal(actual_labels, np.sort(expected_labels))


def test_closed_interval():
    """Test the treatment of meridian closed intervals."""
    result = create_meridians(closed_interval=True)
    meridian_lons = np.arange(
        LONGITUDE_START, LONGITUDE_STOP + LONGITUDE_STEP, LONGITUDE_STEP
    )
    meridians = [str(lon) for lon in meridian_lons]
    # check the meridian longitudes
    assert result.blocks.keys() == meridians
    boundary = str(float(180))
    assert boundary in result.blocks.keys()
    for meridian in meridians:
        mesh = result.blocks[meridian]
        if meridian == boundary:
            assert GV_REMESH_POINT_IDS in mesh.point_data
            assert np.isclose(np.unique(mesh[GV_REMESH_POINT_IDS]), REMESH_SEAM)
        else:
            assert GV_REMESH_POINT_IDS not in mesh.point_data
