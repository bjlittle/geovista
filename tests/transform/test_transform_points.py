"""Unit-tests for :func:`geovista.transform.transform_points`."""
from __future__ import annotations

import numpy as np
from pyproj.exceptions import CRSError
import pytest

from geovista.crs import WGS84
from geovista.transform import transform_points


@pytest.mark.parametrize(
    "src_crs, tgt_crs", [(None, WGS84), (WGS84, None), (None, None)]
)
def test_crs_fail(src_crs, tgt_crs):
    """Test trap of invalid source and/or target CRSs."""
    data = np.empty(1)
    emsg = "Invalid projection"
    with pytest.raises(CRSError, match=emsg):
        _ = transform_points(src_crs=src_crs, tgt_crs=tgt_crs, xs=data, ys=data)


@pytest.mark.parametrize(
    "xbad, ybad",
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
        emsg = "Cannot transform points, 'xs' and 'ys' must be 1-D or 2-D only"
        with pytest.raises(ValueError, match=emsg):
            _ = transform_points(src_crs=WGS84, tgt_crs=WGS84, xs=xs, ys=ys)


@pytest.mark.parametrize(
    "xs, ys",
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
    emsg = "Cannot transform points, 'zs' must be 1-D or 2-D"
    with pytest.raises(ValueError, match=emsg):
        _ = transform_points(src_crs=WGS84, tgt_crs=WGS84, xs=data, ys=data, zs=zs)


def test_z_size_fail():
    """Test trap of unequal number of z-axis samples."""
    data = np.empty(1)
    zs = np.empty(2)
    emsg = "Cannot transform points, 'xs' and 'zs' require same length"
    with pytest.raises(ValueError, match=emsg):
        _ = transform_points(src_crs=WGS84, tgt_crs=WGS84, xs=data, ys=data, zs=zs)
