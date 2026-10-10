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
    assert result.dtype == np.dtype(dtype)
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
    assert result.dtype == np.dtype(dtype)
    np.testing.assert_array_equal(result, expected.astype(dtype))


@pytest.mark.parametrize(
    ("dtype", "expected"),
    [
        ("f4", np.float32),
        ("float64", np.float64),
        (float, np.float64),
        ("i4", np.int32),
        (int, np.int_),
        (np.dtype(np.int64), np.int64),
    ],
)
def test_dtype_like(dtype, expected):
    """Test any data-type that numpy understands gives the result its dtype."""
    result = wrap([179, 180, 181], dtype=dtype)
    assert result.dtype == np.dtype(expected)
    np.testing.assert_array_equal(result, [179, -180, -179])


@pytest.mark.parametrize("dtype", [int, np.int32, np.int64])
def test_integer_dtype_wraps_before_it_converts(dtype):
    """Test an integer dtype converts the wrapped longitudes, not the input.

    Converting first would truncate 179.999 to 179, which no longer snaps to the
    wrap meridian, and 181.5 to 181, which wraps to a different longitude.

    """
    result = wrap([179.0, 179.999, 180.0, 181.5], dtype=dtype)
    assert result.dtype == np.dtype(dtype)
    np.testing.assert_array_equal(result, [179, -180, -180, -178])


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_floating_dtype_wraps_in_that_dtype(dtype):
    """Test a floating dtype is the dtype the longitudes are wrapped in."""
    lons = np.array([179.0, 179.999, 180.0, 181.5], dtype=dtype)
    result = wrap(lons, dtype=dtype)
    assert result.dtype == np.dtype(dtype)
    np.testing.assert_array_equal(result, np.array([179, -180, -180, -178.5], dtype))


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


def test_scalar_is_1d():
    """A scalar longitude comes back as a 1D array of one."""
    result = wrap(180)

    assert result.shape == (1,)
    np.testing.assert_array_equal(result, [-180.0])


def test_0d_array_stays_0d():
    """A 0D array passes the check for an iterable, so it keeps its dimension."""
    result = wrap(np.array(180.0))

    assert isinstance(result, np.ndarray)
    assert result.shape == ()
    np.testing.assert_array_equal(result, -180.0)


def test_0d_array_snaps_to_the_base():
    """A 0D array within tolerance of the end of the period snaps to the base."""
    result = wrap(np.array(179.99999999))

    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, -180.0)
