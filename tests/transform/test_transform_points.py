# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.transform.transform_points`."""

from __future__ import annotations

import warnings

import numpy as np
from pyproj import CRS, Transformer
from pyproj.enums import WktVersion
from pyproj.exceptions import CRSError, ProjError
from pyproj.transformer import TransformerGroup
import pytest

from geovista.common import wrap
from geovista.crs import WGS84
import geovista.transform
from geovista.transform import transform_points


@pytest.mark.parametrize(
    ("src_crs", "tgt_crs"), [(None, WGS84), (WGS84, None), (None, None)]
)
def test_crs_fail(src_crs, tgt_crs):
    """Test trap of invalid source and/or target CRSs."""
    data = np.empty(1)
    emsg = "Invalid projection"
    with pytest.raises(CRSError, match=emsg):
        _ = transform_points(src_crs=src_crs, tgt_crs=tgt_crs, xs=data, ys=data)


@pytest.mark.parametrize(
    ("xbad", "ybad"),
    [
        (True, False),
        (False, True),
        (True, True),
    ],
)
def test_xy_dimension_fail(xbad, ybad):
    """Test trap of non-compliant xs and/or ys dimensionality."""
    xs = np.arange(size := 24)
    ys = np.arange(size)
    if xbad:
        xs = xs.reshape((2, 3, 4))
    if ybad:
        ys = ys.reshape((2, 3, 4))
    bad = xbad or ybad
    if bad:
        emsg = "Cannot transform points, 'xs' and 'ys' must be 1D or 2D only"
        with pytest.raises(ValueError, match=emsg):
            _ = transform_points(src_crs=WGS84, tgt_crs=WGS84, xs=xs, ys=ys)


@pytest.mark.parametrize(
    ("xs", "ys"),
    [(np.arange(10), np.arange(20)), (np.arange(10), np.arange(20).reshape(10, 2))],
)
def test_xy_size_fail(xs, ys):
    """Test trap of unequal number of x-axis and y-axis samples."""
    emsg = "Cannot transform points, 'xs' and 'ys' require same length"
    with pytest.raises(ValueError, match=emsg):
        _ = transform_points(src_crs=WGS84, tgt_crs=WGS84, xs=xs, ys=ys)


def test_z_dimension_fail():
    """Test trap of non-compliant zs dimensionality."""
    data = np.empty(1)
    zs = np.empty(1).reshape(1, 1, 1)
    emsg = "Cannot transform points, 'zs' must be 1D or 2D"
    with pytest.raises(ValueError, match=emsg):
        _ = transform_points(src_crs=WGS84, tgt_crs=WGS84, xs=data, ys=data, zs=zs)


def test_z_size_fail():
    """Test trap of unequal number of z-axis samples."""
    data = np.empty(1)
    zs = np.empty(2)
    emsg = "Cannot transform points, 'xs' and 'zs' require same length"
    with pytest.raises(ValueError, match=emsg):
        _ = transform_points(src_crs=WGS84, tgt_crs=WGS84, xs=data, ys=data, zs=zs)


@pytest.mark.parametrize(
    "y",
    [-90, 90],
)
def test_transform_to_wgs84_poles(y):
    """Test poles to WGS84 have zero longitudes."""
    xs = np.arange(0, 370, 10)
    ys = np.ones_like(xs) * y
    result = transform_points(src_crs=WGS84, tgt_crs=WGS84, xs=xs, ys=ys)
    zeros = np.zeros_like(xs)
    expected = np.vstack([zeros, ys, zeros]).T
    np.testing.assert_array_equal(result, expected)


def test_transform_to_wgs84_interval():
    """Test longitudes transformed to WGS84 are in [-180, 180)."""
    xs = np.arange(0, 370, 10)
    ys = np.zeros_like(xs)
    result = transform_points(src_crs=WGS84, tgt_crs=WGS84, xs=xs, ys=ys)
    expected = np.vstack([wrap(xs), ys, np.zeros_like(xs)]).T
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize("zoffset", [None, 100])
@pytest.mark.parametrize("reshape", [False, True])
@pytest.mark.parametrize("roundtrip", [False, True])
def test_transform(mocker, zoffset, reshape, roundtrip):
    """Test transformation with identical and different CRSs."""
    xs = np.arange(size := 10, dtype=float)
    ys = np.arange(size, dtype=float) + 10
    zs = np.arange(size, dtype=float) + zoffset if zoffset is not None else zoffset
    if reshape:
        shape = (2, 5)
        xs, ys = xs.reshape(shape), ys.reshape(shape)
        if zs is not None:
            zs = zs.reshape(shape)
    else:
        shape = (size,)
    shape = (*shape, 3)
    spy_transformer = mocker.spy(geovista.transform, "_transformer")
    spy_transform = mocker.spy(Transformer, "transform")
    if roundtrip:
        points = transform_points(
            src_crs=WGS84, tgt_crs="+proj=eqc", xs=xs, ys=ys, zs=zs
        )
        result = transform_points(
            src_crs="+proj=eqc",
            tgt_crs=WGS84,
            xs=points[..., 0],
            ys=points[..., 1],
            zs=points[..., 2],
        )
    else:
        result = transform_points(src_crs=WGS84, tgt_crs=WGS84, xs=xs, ys=ys, zs=zs)
    if zoffset is None:
        zs = np.zeros_like(xs)
    expected = np.vstack([xs.flatten(), ys.flatten(), zs.flatten()]).T
    if reshape:
        expected = expected.reshape(shape)
    np.testing.assert_array_almost_equal(result, expected)
    call_count = 2 if roundtrip else 0
    assert spy_transformer.call_count == call_count
    assert spy_transform.call_count == call_count
    assert result.shape == shape


#: A planar target CRS.
PLANAR = "+proj=eqc"

#: An orthographic projection, which cannot reach the far side of the globe.
ORTHO = "+proj=ortho +lat_0=0 +lon_0=0"


@pytest.mark.parametrize("zs", [None, [1.0, 2.0]], ids=["xy", "xyz"])
def test_lists(zs):
    """Lists are accepted wherever arrays are (typing spec §3.3)."""
    xs, ys = [0.0, 90.0], [10.0, 20.0]
    expected = transform_points(
        src_crs=WGS84,
        tgt_crs=PLANAR,
        xs=np.array(xs),
        ys=np.array(ys),
        zs=None if zs is None else np.array(zs),
    )

    result = transform_points(src_crs=WGS84, tgt_crs=PLANAR, xs=xs, ys=ys, zs=zs)

    np.testing.assert_array_equal(result, expected)


def test_nested_lists():
    """Nested lists keep their 2D shape, as arrays do."""
    xs, ys = [[0.0, 90.0], [10.0, 20.0]], [[10.0, 20.0], [30.0, 40.0]]
    expected = transform_points(
        src_crs=WGS84, tgt_crs=PLANAR, xs=np.array(xs), ys=np.array(ys)
    )

    result = transform_points(src_crs=WGS84, tgt_crs=PLANAR, xs=xs, ys=ys)

    assert result.shape == (2, 2, 3)
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize("trap", [None, False])
def test_untrapped_point_is_inf(trap):
    """With the trap off, a point the projection cannot reach comes back inf."""
    result = transform_points(
        src_crs=WGS84, tgt_crs=ORTHO, xs=[180.0], ys=[0.0], trap=trap
    )

    assert np.isinf(result[0, :2]).all()


def test_trapped_point_raises():
    """With the trap on, a point the projection cannot reach raises."""
    with pytest.raises(ProjError, match="outside of projection domain"):
        _ = transform_points(
            src_crs=WGS84, tgt_crs=ORTHO, xs=[180.0], ys=[0.0], trap=True
        )


#: Longitudes along 52°N either side of 2.01°E, where the grid of the 1 m operation
#: from WGS84 to the British National Grid ends.
GRID_EDGE_LONS = np.array([1.75, 2.0, 2.125, 2.25])

#: The British National Grid's projection alone, with no datum shift.
BNG_PROJECTION = (
    "+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad "
    "+step +proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 +x_0=400000 +y_0=-100000 "
    "+ellps=airy"
)


def test_one_datum_operation_across_a_grid_edge():
    """Points either side of a datum grid's edge take one operation.

    Chosen point by point, those east of the grid fell back to no datum shift, a step
    of 129 m. No operation's area of use covers them all, so the most accurate one that
    can take every point is used, with a warning. See :issue:`2714`.

    """
    lats = np.full(GRID_EDGE_LONS.shape, 52.0)

    with pytest.warns(UserWarning, match="area of use"):
        result = transform_points(
            src_crs=WGS84, tgt_crs="EPSG:27700", xs=GRID_EDGE_LONS, ys=lats
        )

    x, _ = Transformer.from_pipeline(BNG_PROJECTION).transform(GRID_EDGE_LONS, lats)
    shift = result[:, 0] - np.asarray(x)
    # the OSGB36 datum shift is about 125 m east here, for every point alike
    assert np.all(shift > 100)
    assert np.ptp(shift) < 10


def test_one_datum_operation_from_a_grid_edge():
    """Points of a national grid either side of its datum grid's edge take one too."""
    lats = np.full(GRID_EDGE_LONS.shape, 52.0)
    xs, ys = Transformer.from_pipeline(BNG_PROJECTION).transform(GRID_EDGE_LONS, lats)

    with pytest.warns(UserWarning, match="area of use"):
        result = transform_points(
            src_crs="EPSG:27700", tgt_crs=WGS84, xs=np.asarray(xs), ys=np.asarray(ys)
        )

    # undoing the projection alone leaves the datum shift, the same for every point
    shift = result[:, 0] - GRID_EDGE_LONS
    assert np.all(np.abs(shift) > 1e-3)
    assert np.ptp(shift) < 1e-4


def test_most_accurate_datum_operation_inside_its_area():
    """Points inside the area of the most accurate operation take it, unwarned."""
    lons = np.array([-2.0, -1.0, 0.0, 1.0])
    lats = np.full(lons.shape, 52.0)

    result = transform_points(src_crs=WGS84, tgt_crs="EPSG:27700", xs=lons, ys=lats)

    best = Transformer.from_crs(WGS84, "EPSG:27700", always_xy=True)
    x, y = best.transform(lons, lats)
    np.testing.assert_allclose(result[:, 0], x, atol=1e-6)
    np.testing.assert_allclose(result[:, 1], y, atol=1e-6)


def test_same_datum_needs_no_operation_chosen():
    """A target on the source's datum is only projected, wherever the points are.

    UTM zone 30N has an area of use of 6°W to 0°, but it changes no datum, so points
    far outside that area are projected without a warning.

    """
    lons, lats = np.array([20.0, 25.0]), np.array([40.0, 45.0])

    result = transform_points(src_crs=WGS84, tgt_crs="EPSG:32630", xs=lons, ys=lats)

    x, y = Transformer.from_crs(WGS84, "EPSG:32630", always_xy=True).transform(
        lons, lats
    )
    np.testing.assert_allclose(result[:, 0], x, atol=1e-6)
    np.testing.assert_allclose(result[:, 1], y, atol=1e-6)


def test_same_datum_by_another_name_needs_no_operation_chosen():
    """A projection on WGS84 by another name than EPSG:4326's is only projected.

    A GeoTIFF's UTM CRS names the WGS84 datum, not EPSG:4326's ensemble of it, and
    PROJ offers only the projection's inverse between them, which changes no datum.
    Points beyond the UTM zone are not warned about.

    """
    # a GeoTIFF's CRS, as GDAL writes EPSG:32618 in WKT1
    utm = CRS.from_wkt(CRS.from_epsg(32618).to_wkt(WktVersion.WKT1_GDAL))
    xs, ys = np.array([1_500_000.0, 1_600_000.0]), np.array([4_500_000.0, 4_600_000.0])

    result = transform_points(src_crs=utm, tgt_crs=WGS84, xs=xs, ys=ys)

    lons, lats = Transformer.from_crs(utm, WGS84, always_xy=True).transform(xs, ys)
    np.testing.assert_allclose(result[:, 0], lons, atol=1e-9)
    np.testing.assert_allclose(result[:, 1], lats, atol=1e-9)


@pytest.mark.usefixtures("no_network")
def test_most_accurate_available_datum_operation():
    """An operation whose grid is not installed is passed over, unwarned.

    pyproj's wheels have neither PROJ's grids nor its network access, so the 1 m
    operation to the British National Grid is unavailable, and the 2 m one is the
    most accurate there is, as PROJ itself would take. PROJ's warning that the best
    is missing was raised before one could be taken.

    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        group = TransformerGroup(WGS84, "EPSG:27700", always_xy=True)
    # the 1 m operation's grid is missing, else this tests nothing
    assert not group.best_available
    lons = np.array([-2.0, -1.0, 0.0, 1.0])
    lats = np.full(lons.shape, 52.0)

    result = transform_points(src_crs=WGS84, tgt_crs="EPSG:27700", xs=lons, ys=lats)

    best = Transformer.from_crs(WGS84, "EPSG:27700", always_xy=True)
    x, y = best.transform(lons, lats)
    np.testing.assert_allclose(result[:, 0], x, atol=1e-6)
    np.testing.assert_allclose(result[:, 1], y, atol=1e-6)


@pytest.mark.parametrize("src_crs", ["EPSG:4807", "EPSG:27572"])
def test_datum_operation_area_in_degrees_from_greenwich(src_crs):
    """Points are located in degrees from Greenwich, to test an area of use.

    NTF (Paris) measures in grads from the Paris meridian, and its point at 2°E 48°N
    is 53.3 grad north, which was compared with the 51.1° northern edge of France,
    and so warned about as outside it. Its Lambert zone II is located through it.

    """
    lon, lat = 2.0, 48.0
    to_src = Transformer.from_crs(WGS84, src_crs, always_xy=True)
    x, y = to_src.transform(lon, lat)

    result = transform_points(src_crs=src_crs, tgt_crs=WGS84, xs=[x], ys=[y])

    expected = Transformer.from_crs(src_crs, WGS84, always_xy=True).transform(x, y)
    np.testing.assert_allclose(result[0, :2], expected, atol=1e-9)


@pytest.mark.parametrize(
    ("src_crs", "tgt_crs"),
    [("EPSG:4326", "EPSG:27700"), ("EPSG:27700", "EPSG:4326")],
    ids=["geographic", "projected"],
)
def test_datum_operation_area_of_a_crs_declared_in_radians(
    in_radians, src_crs, tgt_crs
):
    """Points of a CRS whose geographic axes are in radians are located in degrees.

    ``pyproj`` gives and takes the coordinates of such a CRS in degrees, which were
    scaled as if they were radians, and so warned about as outside Great Britain.

    """
    src_crs = in_radians(src_crs)
    to_src = Transformer.from_crs(WGS84, src_crs, always_xy=True)
    x, y = to_src.transform(-2.0, 52.0)

    result = transform_points(src_crs=src_crs, tgt_crs=tgt_crs, xs=[x], ys=[y])

    expected = Transformer.from_crs(src_crs, tgt_crs, always_xy=True).transform(x, y)
    np.testing.assert_allclose(result[0, :2], expected, atol=1e-6)
