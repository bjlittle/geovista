# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.Transform._as_compatible_data`."""

from __future__ import annotations

import numpy as np
from numpy import ma
import pytest

from geovista.bridge import Transform

N_POINTS: int = 9
N_CELLS: int = 16


def test_none_data():
    """Test no-op on None data i.e., is passed-thru."""
    assert Transform._as_compatible_data(None, N_POINTS, N_CELLS) is None


def test_data_size_mismatch():
    """Test data size does not match required number of points or cells."""
    data = np.arange(10)
    emsg = f"Require mesh data with either '{N_POINTS}' points or '{N_CELLS}'"
    with pytest.raises(ValueError, match=emsg):
        _ = Transform._as_compatible_data(data, N_POINTS, N_CELLS)


@pytest.mark.parametrize("nans", [False, True])
@pytest.mark.parametrize("size", [N_POINTS, N_CELLS])
def test_data_size_match(size, nans):
    """Test data size match with number of points or cells."""
    if nans:
        data = ma.arange(size, dtype=float)
        data[0] = data[-1] = ma.masked
        count = np.sum(data.mask)
    else:
        data = np.arange(size)
        count = 0
    result = Transform._as_compatible_data(data, N_POINTS, N_CELLS)
    assert result.size == size
    assert np.sum(np.isnan(result)) == count


@pytest.mark.parametrize("square", [3, 4])
def test_data_ravel(square):
    """Test the data is flattened."""
    size = square**2
    data = np.arange(size).reshape(square, square)
    result = Transform._as_compatible_data(data, N_POINTS, N_CELLS)
    assert result.ndim == 1
    assert result.shape == (size,)
