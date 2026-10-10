# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.nan_mask`."""

from __future__ import annotations

import numpy as np
from numpy import ma
import pytest

from geovista.common import nan_mask


def test_non_masked():
    """Test no-op on non-masked data."""
    data = np.array(10)
    result = nan_mask(data)
    assert result is data


def test_masked_to_nans():
    """Test masked values are converted to nans."""
    data = ma.arange(10)
    data[::2] = ma.masked
    count = np.sum(data.mask)
    result = nan_mask(data)
    assert np.sum(np.isnan(result)) == count


@pytest.mark.parametrize("dtype", [np.int8, np.int16, np.int32, np.int64, int])
def test_to_float(dtype):
    """Test data dtype coercion to float."""
    data = ma.arange(10, dtype=dtype)
    result = nan_mask(data)
    assert result.dtype == float
    assert ma.isMaskedArray(result) is False


def test_list():
    """A list comes back as the array its annotation promises (typing spec §3.3)."""
    result = nan_mask([1.0, 2.0])

    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, [1.0, 2.0])


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ([ma.masked_array([1.0, 2.0], mask=[False, True])], [[1.0, np.nan]]),
        ([ma.masked_array([1, 2], mask=[True, False])], [[np.nan, 2.0]]),
    ],
    ids=["float", "int"],
)
def test_list_keeps_its_mask(data, expected):
    """The masked arrays a list holds are filled with NaN, as an array would be."""
    result = nan_mask(data)

    assert isinstance(result, np.ndarray)
    assert not ma.isMaskedArray(result)
    np.testing.assert_array_equal(result, expected)
