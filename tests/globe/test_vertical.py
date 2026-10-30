# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the vertical mapping of a globe, and heights on a mesh."""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

from geovista.common import GV_POINT_HEIGHT
from geovista.globe import (
    Globe,
    _carried_heights,
    _mapped,
    _on_globe,
    _record_heights,
    _subtended,
)

#: A render radius of 1, and the Earth's radius.
RADII = [1.0, 6378137.0]

#: A height above sea level, one at it, a depth, and a missing height.
HEIGHTS = [1000.0, 0.0, -4000.0, np.nan]


def test_mapped():
    """A height is exaggerated above sea level, and a depth below it."""
    globe = Globe(exaggeration=20, exaggeration_below=100)
    expected = np.array([20000.0, 0.0, -400000.0, 0.0])
    np.testing.assert_array_equal(_mapped(globe, HEIGHTS), expected)
    np.testing.assert_allclose(
        _subtended(globe, HEIGHTS), expected / 6378137.0, rtol=1e-15
    )


@pytest.mark.parametrize("radius", RADII)
def test_on_globe(radius, at_heights):
    """Each point lies at s (R + V(h)), with a missing height at sea level."""
    globe = Globe(render_radius=radius, exaggeration=20, exaggeration_below=100)
    lons, lats = [0.0, 90.0, -170.0, 45.0], [0.0, 30.0, -60.0, 89.0]
    result = _on_globe(globe, lons, lats, HEIGHTS)
    assert result.shape == (4, 3)
    np.testing.assert_allclose(
        result, at_heights(lons, lats, HEIGHTS, globe), rtol=1e-12, atol=1e-12 * radius
    )


def test_recorded_never_active():
    """Heights are recorded as float64, and never become the active scalars."""
    mesh = pv.PolyData(np.eye(4, 3))
    _record_heights(mesh, [1, 2, 3, 4])
    assert mesh.active_scalars_name is None
    assert mesh.point_data[GV_POINT_HEIGHT].dtype == np.float64

    mesh = pv.PolyData(np.eye(4, 3))
    mesh.point_data["data"] = np.arange(4.0)
    mesh.set_active_scalars("data")
    _record_heights(mesh, [1, 2, 3, 4])
    assert mesh.active_scalars_name == "data"


def test_carried():
    """A mesh without heights carries none, and one with them carries float64."""
    assert _carried_heights(pv.Sphere()) is None
    mesh = pv.PolyData(np.eye(4, 3))
    _record_heights(mesh, [1, 2, 3, 4])
    result = _carried_heights(mesh)
    assert result is not None
    assert result.dtype == np.float64
    np.testing.assert_array_equal(result, [1.0, 2.0, 3.0, 4.0])
