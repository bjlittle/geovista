# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.wrap`."""
from __future__ import annotations

import numpy as np
import pytest

from geovista.common import wrap

DTYPE = np.float64

# lons and expected result for (default) base=180, period=360
# giving the half-open interval [-180, 180)
params_base180 = [
    (180, np.array([-180])),
    (-180, np.array([-180])),
    (0, np.array([0])),
    ([0], np.array([0])),
    ([180], np.array([-180])),
    ([-180], np.array([-180])),
    (
        np.arange(0, 370, 10),
        np.concatenate([np.arange(0, 180, 10), np.arange(-180, 10, 10)]),
    ),
    (
        np.arange(-180, 190, 10),
        np.concatenate([np.arange(-180, 180, 10), np.array([-180])]),
    ),
]


# lons and expected result for (custom) base=0, period=360
# giving the half-interval [0, 360)
params_base0 = [
    (180, np.array([180])),
    (-180, np.array([180])),
    (360, np.array([0])),
    (-360, np.array([0])),
    (0, np.array([0])),
    ([0], np.array([0])),
    ([180], np.array([180])),
    ([-180], np.array([180])),
    ([360], np.array([0])),
    ([-360], np.array([0])),
    (
        np.arange(0, 370, 10),
        np.concatenate([np.arange(0, 360, 10), np.array([0])]),
    ),
    (
        np.arange(-180, 190, 10),
        np.concatenate([np.arange(180, 360, 10), np.arange(0, 190, 10)]),
    ),
]


@pytest.fixture(params=params_base180)
def base180(request):
    """Fixture for testing (default) base=-180, period=360."""
    return request.param


@pytest.fixture(params=params_base0)
def base0(request):
    """Fixure for testing (custom) base=0, period=360."""
    return request.param


def test_base180(base180):
    """Test expected defaults are honoured with default base and period."""
    lons, expected = base180
    result = wrap(lons)
    assert result.dtype == DTYPE
    np.testing.assert_array_equal(result, expected.astype(DTYPE))


@pytest.mark.parametrize("dtype", [None, np.float32, np.float64, np.int32, np.int64])
def test_base180__dtype(base180, dtype):
    """Test dtype with default base and period."""
    lons, expected = base180
    result = wrap(lons, dtype=dtype)
    if dtype is None:
        dtype = DTYPE
    np.testing.assert_array_equal(result, expected.astype(dtype))


def test_base0(base0):
    """Test custom base=0, period=360."""
    lons, expected = base0
    result = wrap(lons, base=0)
    assert result.dtype == DTYPE
    np.testing.assert_array_equal(result, expected.astype(DTYPE))


@pytest.mark.parametrize("dtype", [None, np.float32, np.float64, np.int32, np.int64])
def test_base0__dtype(base0, dtype):
    """Test dtype with default base and period."""
    lons, expected = base0
    result = wrap(lons, base=0, dtype=dtype)
    if dtype is None:
        dtype = DTYPE
    np.testing.assert_array_equal(result, expected.astype(dtype))


@pytest.mark.parametrize(
    ("delta", "expected"), [(1.0e-4, True), (1.0e-3, True), (2.0e-3, False)]
)
def test_base_period_tolerance(delta, expected):
    """Test the relative and absolute tolerance of the base + period value."""
    result = wrap(180 - delta)
    assert np.isclose(result, -180)[0] == expected


def test_custom_period():
    """Test custom interval period."""
    lons = np.arange(-180, 190, 10)
    expected = np.concatenate(
        [np.arange(-180, 0, 10), np.arange(-180, 0, 10), np.array([-180])]
    )
    result = wrap(lons, period=180)
    np.testing.assert_array_equal(result, expected.astype(DTYPE))


def test_custom_base():
    """Test custom interval base."""
    lons = np.arange(-180, 190, 10)
    expected = np.concatenate([np.arange(180, 360, 10), np.arange(0, 190, 10)])
    result = wrap(lons, base=0)
    np.testing.assert_array_equal(result, expected.astype(DTYPE))
