# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.globe.Globe.to_mesh`."""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

from geovista.bridge import Transform
from geovista.common import (
    GV_FIELD_GLOBE_EXAGGERATION_ABOVE,
    GV_FIELD_GLOBE_EXAGGERATION_BELOW,
    GV_FIELD_GLOBE_RADIUS,
    GV_FIELD_GLOBE_RENDER_RADIUS,
    GV_FIELD_RADIUS,
)
from geovista.globe import Globe

LONS = np.linspace(-180, 180, 9)
LATS = np.linspace(-90, 90, 5)

#: The four fields a mesh records its globe in.
FIELDS = [
    GV_FIELD_GLOBE_RADIUS,
    GV_FIELD_GLOBE_RENDER_RADIUS,
    GV_FIELD_GLOBE_EXAGGERATION_ABOVE,
    GV_FIELD_GLOBE_EXAGGERATION_BELOW,
]


def test_the_field_names():
    """Test that each field is named for a reader of the file."""
    assert FIELDS == [
        "gvGlobeRadius",
        "gvGlobeRenderRadius",
        "gvGlobeExaggerationAbove",
        "gvGlobeExaggerationBelow",
    ]


def test_writes_four_float64_fields_and_no_gvradius():
    """Test that a globe is written as four float64 values, replacing gvRadius."""
    mesh = Transform.from_1d(LONS, LATS)
    assert GV_FIELD_RADIUS in mesh.field_data
    Globe(exaggeration=20, exaggeration_below=100).to_mesh(mesh)
    for name, value in zip(FIELDS, [6378137.0, 1.0, 20.0, 100.0], strict=True):
        assert mesh.field_data[name].dtype == np.float64
        assert mesh.field_data[name].tolist() == [value]
    assert GV_FIELD_RADIUS not in mesh.field_data


def test_writes_over_a_recorded_globe():
    """Test that a second globe replaces the first."""
    mesh = Transform.from_1d(LONS, LATS)
    Globe(exaggeration=20).to_mesh(mesh)
    Globe(render_radius=2).to_mesh(mesh)
    assert [mesh.field_data[name].tolist() for name in FIELDS] == [
        [6378137.0],
        [2.0],
        [1.0],
        [1.0],
    ]


@pytest.mark.usefixtures("reordered_fields")
def test_each_value_is_written_to_its_field_by_name():
    """Test that the order of the field names does not decide where a value goes."""
    mesh = pv.PolyData()
    Globe(
        radius=6371000, render_radius=2, exaggeration=20, exaggeration_below=100
    ).to_mesh(mesh)
    assert [mesh.field_data[name].tolist() for name in FIELDS] == [
        [6371000.0],
        [2.0],
        [20.0],
        [100.0],
    ]
