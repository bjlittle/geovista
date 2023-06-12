"""Unit-tests for :class:`geovista.geodesic.BBox`."""
import numpy as np
import pytest

from geovista.geodesic import BBox, Preference, panel

from .conftest import CIDS

# cell-ids of the C48 SST cubed-sphere antarctic panel
ANTARCTIC_CIDS = np.arange(CIDS[0], CIDS[-1] + 1)

# C48 cubed-sphere panel shape
C48 = (48, 48)


@pytest.mark.parametrize("outside", [False, True])
@pytest.mark.parametrize("preference", ["point", Preference.POINT, Preference("point")])
def test_enclosed_point(antarctic_corners, lfric_sst, outside, preference):
    """Test enclosed points of antarctic cubed-sphere panel."""
    lons, lats = antarctic_corners
    bbox = BBox(lons, lats)
    region = bbox.enclosed(lfric_sst, outside=outside, preference=preference)
    if outside:
        cids = np.arange(lfric_sst.n_cells)
        antarctic = ANTARCTIC_CIDS.reshape(C48)
        antarctic = antarctic[1:-1][:, 1:-1]
        expected = np.setdiff1d(cids, antarctic)
    else:
        expected = ANTARCTIC_CIDS
    np.testing.assert_array_equal(region.cell_data["cids"], expected)


@pytest.mark.parametrize("outside", [False, True])
@pytest.mark.parametrize("preference", ["cell", Preference.CELL, Preference("cell")])
def test_enclosed_cell(antarctic_corners, lfric_sst, outside, preference):
    """Test enclosed cells of antarctic cubed-sphere panel."""
    lons, lats = antarctic_corners
    bbox = BBox(lons, lats)
    region = bbox.enclosed(lfric_sst, outside=outside, preference=preference)
    if outside:
        cids = np.arange(lfric_sst.n_cells)
        expected = np.setdiff1d(cids, ANTARCTIC_CIDS)
    else:
        expected = ANTARCTIC_CIDS.reshape(C48)
        expected = np.ravel(expected[1:-1][:, 1:-1])
    np.testing.assert_array_equal(region.cell_data["cids"], expected)


@pytest.mark.parametrize("outside", [False, True])
@pytest.mark.parametrize(
    "preference", [None, "center", Preference.CENTER, Preference("center")]
)
def test_enclosed_center(lfric_sst, outside, preference):
    """Test enclosed centers of antarctic cubed-sphere panel."""
    bbox = panel("antarctic")
    region = bbox.enclosed(lfric_sst, outside=outside, preference=preference)
    if outside:
        cids = np.arange(lfric_sst.n_cells)
        expected = np.setdiff1d(cids, ANTARCTIC_CIDS)
    else:
        expected = ANTARCTIC_CIDS
    np.testing.assert_array_equal(region.cell_data["cids"], expected)


def test_preference_invalid_fail(lfric_sst):
    """Test trap of invalid preference."""
    bbox = panel("africa")
    emsg = "Expected a preference of 'cell' or 'center' or 'point'"
    with pytest.raises(ValueError, match=emsg):
        _ = bbox.enclosed(lfric_sst, preference="invalid")
