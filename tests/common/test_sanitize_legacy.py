# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.sanitize_legacy`."""

from __future__ import annotations

import warnings

import numpy as np
import pytest
import pyvista as pv

from geovista.bridge import Transform
from geovista.common import (
    GV_FIELD_RADIUS,
    RETIRED_FIELDS,
    RetiredField,
    sanitize_legacy,
)
from geovista.globe import Globe

LONS = np.linspace(-180, 180, 9)
LATS = np.linspace(-90, 90, 5)

#: A render radius of 1, and of the Earth's radius (scene spec §6).
RADII = [1.0, 6378137.0]


def test_the_table_lists_gvradius():
    """Test that gvRadius is a retired field, last written by 0.5.3."""
    (entry,) = [e for e in RETIRED_FIELDS if e.name == GV_FIELD_RADIUS]
    assert (entry.association, entry.last_written) == ("field", "0.5.3")
    assert "gvGlobeRenderRadius" in entry.replacement
    assert len({e.name for e in RETIRED_FIELDS}) == len(RETIRED_FIELDS)
    assert all(isinstance(e, RetiredField) for e in RETIRED_FIELDS)


def test_an_entry_cannot_be_changed():
    """Test that an entry of the table is immutable."""
    with pytest.raises(AttributeError):
        RETIRED_FIELDS[0].name = "gvOther"


@pytest.mark.parametrize("render_radius", RADII)
def test_translates_and_removes_gvradius(render_radius):
    """Test that a gvRadius becomes the globe it gives, and the points stay."""
    mesh = Transform.from_1d(LONS, LATS, radius=render_radius)
    points = mesh.points.copy()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        sanitize_legacy(mesh)
    assert GV_FIELD_RADIUS not in mesh.field_data
    assert Globe.from_mesh(mesh) == Globe(render_radius=render_radius)
    assert np.array_equal(mesh.points, points)


def test_cleans_every_mesh():
    """Test that each mesh given is cleaned."""
    meshes = [Transform.from_1d(LONS, LATS, radius=r) for r in RADII]
    sanitize_legacy(*meshes)
    assert not any(GV_FIELD_RADIUS in m.field_data for m in meshes)


def test_keeps_a_recorded_globe():
    """Test that a recorded globe wins over a gvRadius beside it."""
    mesh = Transform.from_1d(LONS, LATS)
    Globe(render_radius=2).to_mesh(mesh)
    mesh.field_data[GV_FIELD_RADIUS] = np.array([3.0])
    sanitize_legacy(mesh)
    assert Globe.from_mesh(mesh) == Globe(render_radius=2)
    assert GV_FIELD_RADIUS not in mesh.field_data


def test_a_mesh_with_no_retired_field_is_unchanged():
    """Test that a mesh with no retired field gains no field."""
    mesh = pv.Sphere()
    sanitize_legacy(mesh)
    assert list(mesh.field_data) == []


def test_needs_a_mesh():
    """Test trap of no meshes."""
    with pytest.raises(ValueError, match="Expected one or more meshes to sanitize"):
        sanitize_legacy()
