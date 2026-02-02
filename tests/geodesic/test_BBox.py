# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.geodesic.BBox`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.common import (
    GV_FIELD_CRS,
    GV_FIELD_RADIUS,
    RADIUS,
    ZLEVEL_SCALE,
    distance,
)
from geovista.crs import WGS84, from_wkt
from geovista.geodesic import (
    BBOX_OUTSIDE,
    BBOX_TOLERANCE,
    PANEL_IDX_BY_NAME,
    PREFERENCE,
    BBox,
    EnclosedPreference,
    panel,
)
from geovista.transform import transform_points

from .conftest import ANTARCTIC_CORNER_CIDS as CIDS

# cell-ids of the C48 SST cubed-sphere antarctic panel
ANTARCTIC_CIDS = np.arange(CIDS[0], CIDS[-1] + 1)

# C48 cubed-sphere panel shape
C48 = (48, 48)


@pytest.mark.parametrize("active", [False, True])
@pytest.mark.parametrize("outside", [False, True])
@pytest.mark.parametrize(
    "preference", ["point", EnclosedPreference.POINT, EnclosedPreference("point")]
)
@pytest.mark.parametrize("proj", [pytest.param(None, id="WGS84"), "moll", "stere"])
def test_enclosed_point(
    antarctic_corners, lfric_sst, active, outside, preference, proj
):
    """Test enclosed points of antarctic cubed-sphere panel."""
    if not active:
        lfric_sst.active_scalars_name = None
    active_scalars_name = lfric_sst.active_scalars_name
    lons, lats = antarctic_corners
    if proj:
        crs = f"+proj={proj}"
        xy = transform_points(xs=lons, ys=lats, src_crs=WGS84, tgt_crs=crs)
        xs, ys = xy[:, 0], xy[:, 1]
    else:
        crs = WGS84
        xs, ys = lons, lats
    bbox = BBox(xs, ys, crs=crs)
    region = bbox.enclosed(lfric_sst, outside=outside, preference=preference)
    if outside:
        cids = np.arange(lfric_sst.n_cells)
        antarctic = ANTARCTIC_CIDS.reshape(C48)
        antarctic = antarctic[1:-1][:, 1:-1]
        expected = np.setdiff1d(cids, antarctic)
    else:
        expected = ANTARCTIC_CIDS
    np.testing.assert_array_equal(region.cell_data["cids"], expected)
    assert region.active_scalars_name == active_scalars_name


@pytest.mark.parametrize("active", [False, True])
@pytest.mark.parametrize("outside", [False, True])
@pytest.mark.parametrize(
    "preference", ["cell", EnclosedPreference.CELL, EnclosedPreference("cell")]
)
@pytest.mark.parametrize("proj", [pytest.param(None, id="WGS84"), "moll", "stere"])
def test_enclosed_cell(antarctic_corners, lfric_sst, active, outside, preference, proj):
    """Test enclosed cells of antarctic cubed-sphere panel."""
    if not active:
        lfric_sst.active_scalars_name = None
    active_scalars_name = lfric_sst.active_scalars_name
    lons, lats = antarctic_corners
    if proj:
        crs = f"+proj={proj}"
        xy = transform_points(xs=lons, ys=lats, src_crs=WGS84, tgt_crs=crs)
        xs, ys = xy[:, 0], xy[:, 1]
    else:
        crs = WGS84
        xs, ys = lons, lats
    bbox = BBox(xs, ys, crs=crs)
    region = bbox.enclosed(lfric_sst, outside=outside, preference=preference)
    if outside:
        cids = np.arange(lfric_sst.n_cells)
        expected = np.setdiff1d(cids, ANTARCTIC_CIDS)
    else:
        expected = ANTARCTIC_CIDS.reshape(C48)
        expected = np.ravel(expected[1:-1][:, 1:-1])
    np.testing.assert_array_equal(region.cell_data["cids"], expected)
    assert region.active_scalars_name == active_scalars_name


@pytest.mark.parametrize("active", [False, True])
@pytest.mark.parametrize("outside", [False, True])
@pytest.mark.parametrize(
    "preference",
    [None, "center", EnclosedPreference.CENTER, EnclosedPreference("center")],
)
def test_enclosed_center(lfric_sst, active, outside, preference):
    """Test enclosed centers of antarctic cubed-sphere panel."""
    if not active:
        lfric_sst.active_scalars_name = None
    active_scalars_name = lfric_sst.active_scalars_name
    bbox = panel("antarctic")
    region = bbox.enclosed(lfric_sst, outside=outside, preference=preference)
    if outside:
        cids = np.arange(lfric_sst.n_cells)
        expected = np.setdiff1d(cids, ANTARCTIC_CIDS)
    else:
        expected = ANTARCTIC_CIDS
    np.testing.assert_array_equal(region.cell_data["cids"], expected)
    assert region.active_scalars_name == active_scalars_name


def test_preference_invalid_fail(lfric_sst):
    """Test trap of invalid preference."""
    bbox = panel("africa")
    emsg = "Expected a preference of 'cell' or 'center' or 'point'"
    with pytest.raises(ValueError, match=emsg):
        _ = bbox.enclosed(lfric_sst, preference="invalid")


@pytest.mark.parametrize("name", PANEL_IDX_BY_NAME)
def test_mesh_field_data(name):
    """Test expected metadata populated within field-data."""
    bbox = panel(name)
    result = bbox.mesh
    assert GV_FIELD_CRS in result.field_data
    assert GV_FIELD_RADIUS in result.field_data
    assert from_wkt(result) == WGS84
    expected = distance(result)
    assert np.isclose(result.field_data[GV_FIELD_RADIUS], expected)


@pytest.mark.parametrize("name", PANEL_IDX_BY_NAME)
def test_boundary_field_data(name):
    """Test expected metadata populated within field-data."""
    bbox = panel(name)
    result = bbox.boundary()
    assert GV_FIELD_CRS in result.field_data
    assert GV_FIELD_RADIUS in result.field_data
    assert from_wkt(result) == WGS84
    expected = RADIUS + RADIUS * ZLEVEL_SCALE
    assert np.isclose(result.field_data[GV_FIELD_RADIUS], expected)


def test_closed_geometry():
    """Test 5 corner points form closed geometry."""
    xs = [0, 10, 10, 0, 0]
    ys = [0, 0, 10, 10, 0]
    bbox = BBox(xs, ys)
    # We only keep the open geometry:
    assert len(bbox.xs) == len(bbox.ys) == 4


def test_closed_geometry_warn_not_close():
    """Test warning raised if 5 corner points do not form closed geometry."""
    xs = [0, 10, 10, 0, 1]
    ys = [0, 0, 10, 10, 0]
    emsg = "first and last values are not close enough to specify a closed geometry"
    with pytest.warns(UserWarning, match=emsg):
        bbox = BBox(xs, ys)
    # We only keep the open geometry:
    assert len(bbox.xs) == len(bbox.ys) == 4


def test___eq__():
    """Test equality operator for equality."""
    bbox1 = panel(name := "americas")
    bbox2 = panel(name)
    assert bbox1 == bbox2


@pytest.mark.parametrize("crs", ["moll", "merc"])
def test___eq__different_projections(crs):
    """Test equality operator for same BBox in different projections."""
    bbox1 = panel("americas")
    crs = f"+proj={crs}"
    xy = transform_points(xs=bbox1.lons, ys=bbox1.lats, src_crs=WGS84, tgt_crs=crs)
    bbox2 = BBox(xs=xy[:, 0], ys=xy[:, 1], crs=crs)
    assert bbox1 == bbox2


def test___eq___fail():
    """Test equality operator for inequality."""
    bbox1 = panel(name := "arctic")
    bbox2 = panel(name, c=32)
    # intentional usage instead of "!="
    assert not bbox1 == bbox2  # noqa: SIM201


def test___eq___fail_type():
    """Test equality operator with non-BBox."""
    bbox = panel("arctic")
    # intentional usage instead of "!="
    assert not bbox == "bbox"  # noqa: SIM201


def test___hash__():
    """Test that BBox is hashable."""
    bbox = panel("antarctic")
    actual = hash(bbox)
    assert isinstance(actual, int)
    expected = hash(
        (
            bbox.crs,
            bbox.ellps,
            bbox.c,
            bbox.triangulate,
            bbox.lons.tobytes(),
            bbox.lats.tobytes(),
        )
    )
    assert actual == expected


def test___ne__():
    """Test inequality operator for inequality."""
    bbox1 = panel("africa")
    bbox2 = panel("asia")
    assert bbox1 != bbox2


def test___ne___fail():
    """Test inequality operator for equality."""
    bbox1 = panel(name := "africa")
    bbox2 = panel(name)
    # intentional usage instead of "=="
    assert not bbox1 != bbox2  # noqa: SIM202


def test___ne___fail_type():
    """Test inequality operator with non-BBox."""
    bbox = panel("africa")
    assert bbox != "bbox"


def test_serialization():
    """Test string and representation serialization."""
    bbox = panel("antarctic")
    expected = (
        "geovista.BBox<crs=epsg:4326, ellps=WGS84, c=256, "
        "n_points=132098, n_cells=132096>"
    )
    assert repr(bbox) == expected
    assert str(bbox) == expected


def test_outside_default():
    """Test outside property default."""
    bbox = panel("africa")
    assert bbox.outside == BBOX_OUTSIDE


@pytest.mark.parametrize(
    ("outside", "expected"),
    [(None, BBOX_OUTSIDE), (not BBOX_OUTSIDE, not BBOX_OUTSIDE), (0, False), (1, True)],
)
def test_outside(outside, expected):
    """Test outside property getter/setter."""
    bbox = panel("africa")
    bbox.outside = outside
    assert bbox.outside == expected


def test_preference_default():
    """Test preference property default."""
    bbox = panel("africa")
    assert bbox.preference == EnclosedPreference(PREFERENCE)


@pytest.mark.parametrize(
    ("preference", "expected"),
    [
        (None, EnclosedPreference(PREFERENCE)),
        ("cell", EnclosedPreference("cell")),
        (EnclosedPreference("point"), EnclosedPreference("point")),
    ],
)
def test_preference(preference, expected):
    """Test preference property getter/setter."""
    bbox = panel("pacific")
    bbox.preference = preference
    assert bbox.preference == expected


def test_preference_fail():
    """Test preference property setter exception."""
    bbox = panel("asia")
    preference = "wibble"
    emsg = f"Expected a preference of .*, got '{preference}'."
    with pytest.raises(ValueError, match=emsg):
        bbox.preference = preference


def test_tolerance_default():
    """Test tolerance property default."""
    bbox = panel("americas")
    assert bbox.tolerance == pytest.approx(BBOX_TOLERANCE)


@pytest.mark.parametrize(
    ("tolerance", "expected"),
    [(None, BBOX_TOLERANCE), (1.23, 1.23), ("4.56", 4.56)],
)
def test_tolerance(tolerance, expected):
    """Test tolerance property getter/setter."""
    bbox = panel("arctic")
    bbox.tolerance = tolerance
    assert bbox.tolerance == pytest.approx(expected)
