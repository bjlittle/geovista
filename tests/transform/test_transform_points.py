# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.transform.transform_points`."""

from __future__ import annotations

import numpy as np
from pyproj import Transformer
from pyproj.exceptions import CRSError
import pytest

from geovista.crs import WGS84
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
    spy_from_crs = mocker.spy(Transformer, "from_crs")
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
    assert spy_from_crs.call_count == call_count
    assert spy_transform.call_count == call_count
    assert result.shape == shape
