# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the heights and depths of ``mesh.gv``."""

from __future__ import annotations

import numpy as np
import pint
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
    result = mesh.gv.height.m_as("m")
    assert result.dtype == np.float64
    np.testing.assert_array_equal(result[:3], [100.0, -4000.0, np.nan])
    np.testing.assert_array_equal(result[3:], 0.0)


@pytest.mark.parametrize(("name", "sign"), [("height", 1.0), ("depth", -1.0)])
def test_a_quantity_in_metres(name, sign):
    """Heights and depths read back as quantities of the application registry.

    Holds scene spec §2 decision 8.
    """
    mesh = _with_heights([100.0, -4000.0])
    result = getattr(mesh.gv, name)
    assert isinstance(result, pint.Quantity)
    assert result._REGISTRY is pint.application_registry.get()
    assert result.units == pint.application_registry.get().m
    assert result.magnitude.dtype == np.float64
    np.testing.assert_array_equal(result.magnitude[:2], [sign * 100.0, sign * -4000.0])


def test_none_without_heights():
    """A mesh without heights has neither a height nor a depth."""
    mesh = pv.Sphere()
    assert mesh.gv.height is None
    assert mesh.gv.depth is None


def test_depth_is_the_negation():
    """A depth is the negation of a height, and a missing one stays missing.

    Holds heights spec §2 decision 2.
    """
    mesh = _with_heights([100.0, -4000.0, np.nan])
    np.testing.assert_array_equal(mesh.gv.depth.m_as("m")[:3], [-100.0, 4000.0, np.nan])


@pytest.mark.parametrize("name", ["height", "depth"])
def test_cannot_be_set(name):
    """Neither can be set, since heights say where the points are drawn."""
    mesh = _with_heights([100.0])
    with pytest.raises(AttributeError, match="cannot be set"):
        setattr(mesh.gv, name, np.zeros(mesh.n_points))


@pytest.mark.parametrize("name", ["height", "depth"])
def test_cannot_be_written(name):
    """The quantities returned cannot be written, so the mesh never changes."""
    mesh = _with_heights([100.0])
    expected = np.array(mesh.point_data[GV_POINT_HEIGHT])
    result = getattr(mesh.gv, name)
    with pytest.raises(ValueError, match="read-only"):
        result[0] = 1.0 * result.units
    with pytest.raises(ValueError, match="read-only"):
        result.magnitude[0] = 1.0
    np.testing.assert_array_equal(mesh.point_data[GV_POINT_HEIGHT], expected)


def test_heights_stay_out_of_equality():
    """Two meshes that differ only in their heights are described alike."""
    one, two = _with_heights([100.0]), _with_heights([-4000.0])
    for mesh in (one, two):
        Globe().to_mesh(mesh)
    assert one.gv == two.gv
