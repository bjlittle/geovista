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
    GV_POINT_ZLEVEL,
    RETIRED_FIELDS,
    RetiredField,
    distance,
    from_cartesian,
    sanitize,
    sanitize_legacy,
)
from geovista.core import resize
from geovista.crs import WGS84
from geovista.globe import Globe
from geovista.transform import transform_mesh

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


def _cloud() -> pv.PolyData:
    """Build a cloud with heights, on a render radius of 2."""
    return Transform.from_points(
        [0, 10, 20], [0, 10, 20], radius=2, zlevel=[1, 2, 3], zscale=0.1
    )


def _cleaned(mesh: pv.PolyData) -> pv.PolyData:
    """Return a copy of the mesh, cleaned of its retired fields."""
    mesh = mesh.copy()
    sanitize_legacy(mesh)
    return mesh


def test_a_cleaned_cloud_keeps_its_heights():
    """Test that a cloud cleaned by sanitize reads back at the same heights."""
    cloud = _cloud()
    sanitize(cloud)
    assert GV_FIELD_RADIUS not in cloud.field_data
    np.testing.assert_allclose(from_cartesian(cloud)[:, 2], [1, 2, 3])


def test_distance_snaps_to_a_cleaned_radius():
    """Test that the mean distance snaps to a radius held by the globe."""
    mesh = Transform.from_1d(LONS, LATS, radius=2)
    mesh.points = mesh.points * (1 + 1e-7)
    expected = distance(mesh)
    sanitize_legacy(mesh)
    assert distance(mesh) == expected == 2


@pytest.mark.parametrize(
    "kwargs", [{}, {"radius": 3}, {"zscale": 0.2}, {"zlevel": 1}], ids=str
)
def test_resizing_a_cleaned_cloud(kwargs):
    """Test that a cloud cleaned then resized is one resized then cleaned."""
    expected = _cleaned(resize(_cloud(), **kwargs))
    result = resize(_cleaned(_cloud()), **kwargs)
    np.testing.assert_allclose(result.points, expected.points)
    np.testing.assert_allclose(from_cartesian(result), from_cartesian(expected))
    assert result.gv.globe == expected.gv.globe
    assert GV_FIELD_RADIUS not in result.field_data


@pytest.mark.parametrize("zlevel", [None, 1, "each"])
def test_resizing_a_cleaned_surface(zlevel):
    """Test that a surface cleaned then resized is one resized then cleaned."""
    mesh = Transform.from_1d(LONS, LATS, radius=2)
    if zlevel == "each":
        zlevel = np.arange(mesh.n_points) % 3
    expected = _cleaned(resize(mesh, radius=3, zlevel=zlevel))
    result = resize(_cleaned(mesh), radius=3, zlevel=zlevel)
    np.testing.assert_allclose(result.points, expected.points)
    assert result.gv.globe == expected.gv.globe
    assert GV_FIELD_RADIUS not in result.field_data


def test_projecting_a_cleaned_cloud():
    """Test that a cleaned cloud projects, and comes back, at its heights."""
    expected = transform_mesh(_cloud(), "+proj=eqc")
    result = transform_mesh(_cleaned(_cloud()), "+proj=eqc")
    np.testing.assert_allclose(result[GV_POINT_ZLEVEL], [1, 2, 3])
    np.testing.assert_allclose(result.points, expected.points)
    back = transform_mesh(result, WGS84)
    np.testing.assert_allclose(back.points, transform_mesh(expected, WGS84).points)
    assert back.gv.globe == Globe(render_radius=2)
    assert GV_FIELD_RADIUS not in back.field_data
