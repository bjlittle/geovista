# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.transform.transform_point`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.crs import WGS84
from geovista.transform import transform_point


@pytest.mark.parametrize(
    "bad",
    [np.array([]), np.empty(()), np.empty((3,)), np.empty((3, 1)), np.empty((2, 3))],
)
def test_shape_fail(mocker, bad):
    """Test trap for unexpected result shape."""
    src_crs = mocker.sentinel.src_crs
    tgt_crs = mocker.sentinel.tgt_crs
    x, y, z = mocker.sentinel.x, mocker.sentinel.y, mocker.sentinel.z
    trap = mocker.sentinel.trap
    _ = mocker.patch("geovista.transform.transform_points", return_value=bad)
    emsg = "Cannot transform point, got unexpected shape"
    with pytest.raises(AssertionError, match=emsg):
        _ = transform_point(src_crs=src_crs, tgt_crs=tgt_crs, x=x, y=y, z=z, trap=trap)
    from geovista.transform import transform_points

    transform_points.assert_called_once_with(
        src_crs=src_crs,
        tgt_crs=tgt_crs,
        xs=x,
        ys=y,
        zs=z,
        trap=trap,
    )


@pytest.mark.parametrize(
    "extract_xyz",
    [lambda arg: arg, lambda arg: arg.reshape(3, 1)],
)
def test_valid_pass_thru(extract_xyz):
    """Test transforming scalar spatial values."""
    expected = np.array([0, 1, 2], dtype=float)
    x, y, z = extract_xyz(expected)
    result = transform_point(src_crs=WGS84, tgt_crs=WGS84, x=x, y=y, z=z)
    assert result.shape == expected.shape
    np.testing.assert_array_equal(result, expected)
