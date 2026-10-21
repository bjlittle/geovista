# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.raster.wrap_texture`."""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

from geovista.raster import wrap_texture


@pytest.fixture
def image():
    """Create a small RGB image, two pixels high and four wide."""
    return np.arange(2 * 4 * 3, dtype=np.uint8).reshape(2, 4, 3)


@pytest.mark.parametrize("meridian", [None, 0, 360])
def test_no_wrap(image, meridian):
    """Test a texture centred on the prime meridian is returned as it is."""
    texture = pv.Texture(image)
    assert wrap_texture(texture, central_meridian=meridian) is texture


@pytest.mark.parametrize(("meridian", "shift"), [(90, -1), (180, 2), (-90, 1)])
def test_wrap(image, meridian, shift):
    """Test a texture is re-centred on the meridian."""
    result = wrap_texture(pv.Texture(image), central_meridian=meridian)
    np.testing.assert_array_equal(result.to_array(), np.roll(image, shift, axis=1))
