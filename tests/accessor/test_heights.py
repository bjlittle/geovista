# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the heights and depths of ``mesh.gv``."""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

from geovista.common import GV_POINT_HEIGHT
from geovista.globe import Globe, _record_heights


def _with_heights(heights: list[float]) -> pv.PolyData:
    """Return a sphere whose first points carry the heights, and the rest 0."""
    mesh = pv.Sphere()
    values = np.zeros(mesh.n_points)
    values[: len(heights)] = heights
    _record_heights(mesh, values)
    return mesh


def test_height_reads_back():
    """The heights a mesh carries read back as float64."""
    mesh = _with_heights([100.0, -4000.0, np.nan])
    result = mesh.gv.height
    assert result.dtype == np.float64
    np.testing.assert_array_equal(result[:3], [100.0, -4000.0, np.nan])
    np.testing.assert_array_equal(result[3:], 0.0)


def test_none_without_heights():
    """A mesh without heights has neither a height nor a depth."""
    mesh = pv.Sphere()
    assert mesh.gv.height is None
    assert mesh.gv.depth is None


def test_depth_is_the_negation():
    """A depth is the negation of a height, and a missing one stays missing."""
    mesh = _with_heights([100.0, -4000.0, np.nan])
    np.testing.assert_array_equal(mesh.gv.depth[:3], [-100.0, 4000.0, np.nan])


@pytest.mark.parametrize("name", ["height", "depth"])
def test_cannot_be_set(name):
    """Neither can be set, since heights say where the points are drawn."""
    mesh = _with_heights([100.0])
    with pytest.raises(AttributeError, match="cannot be set"):
        setattr(mesh.gv, name, np.zeros(mesh.n_points))


@pytest.mark.parametrize("name", ["height", "depth"])
def test_cannot_be_written(name):
    """The arrays returned cannot be written, so the mesh never changes."""
    mesh = _with_heights([100.0])
    expected = np.array(mesh.point_data[GV_POINT_HEIGHT])
    with pytest.raises(ValueError, match="read-only"):
        getattr(mesh.gv, name)[0] = 1.0
    np.testing.assert_array_equal(mesh.point_data[GV_POINT_HEIGHT], expected)


def test_heights_stay_out_of_equality():
    """Two meshes that differ only in their heights are described alike."""
    one, two = _with_heights([100.0]), _with_heights([-4000.0])
    for mesh in (one, two):
        Globe().to_mesh(mesh)
    assert one.gv == two.gv
