# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.globe.Globe.from_mesh`."""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

from geovista.bridge import Transform
from geovista.common import (
    GV_FIELD_GLOBE_RADIUS,
    GV_FIELD_GLOBE_RENDER_RADIUS,
    GV_FIELD_RADIUS,
)
from geovista.globe import Globe
from geovista.pantry.meshes import lfric_orog

LONS = np.linspace(-180, 180, 9)
LATS = np.linspace(-90, 90, 5)

#: A render radius of 1, and of the Earth's radius (scene spec §6).
RADII = [1.0, 6378137.0]


def sphere(radius: float = 1.0, *, record: bool = True) -> pv.PolyData:
    """Build a mesh on a sphere, with a gvRadius unless asked for none."""
    mesh = Transform.from_1d(LONS, LATS, radius=radius)
    if not record:
        del mesh.field_data[GV_FIELD_RADIUS]
    return mesh


@pytest.mark.parametrize("render_radius", RADII)
def test_the_four_fields_give_the_globe(render_radius):
    """Test that a recorded globe reads back equal."""
    globe = Globe(
        radius=6371000,
        render_radius=render_radius,
        exaggeration=20,
        exaggeration_below=100,
    )
    mesh = pv.PolyData()
    globe.to_mesh(mesh)
    assert Globe.from_mesh(mesh) == globe


def test_the_four_fields_win_over_gvradius():
    """Test that a recorded globe wins over a gvRadius beside it."""
    mesh = sphere()
    Globe(render_radius=2).to_mesh(mesh)
    mesh.field_data[GV_FIELD_RADIUS] = np.array([3.0])
    assert Globe.from_mesh(mesh) == Globe(render_radius=2)


def test_a_partial_record_is_refused():
    """Test that a mesh with some of the four fields is refused, naming the rest."""
    mesh = sphere()
    Globe().to_mesh(mesh)
    del mesh.field_data["gvGlobeExaggerationAbove"]
    del mesh.field_data["gvGlobeExaggerationBelow"]
    with pytest.raises(ValueError, match="gvGlobeExaggerationAbove"):
        Globe.from_mesh(mesh)


def test_a_recorded_field_is_one_number():
    """Test that a field of two values is refused, naming it."""
    mesh = sphere()
    Globe().to_mesh(mesh)
    mesh.field_data[GV_FIELD_GLOBE_RADIUS] = np.array([1.0, 2.0])
    with pytest.raises(ValueError, match="gvGlobeRadius"):
        Globe.from_mesh(mesh)


def test_a_recorded_field_is_a_number():
    """Test that a field holding a string is refused, naming it."""
    mesh = sphere()
    Globe().to_mesh(mesh)
    mesh.field_data[GV_FIELD_GLOBE_RADIUS] = ["6371 km"]
    with pytest.raises(ValueError, match="gvGlobeRadius"):
        Globe.from_mesh(mesh)


def test_a_recorded_value_is_checked():
    """Test that a recorded value is checked as a globe's."""
    mesh = sphere()
    Globe().to_mesh(mesh)
    mesh.field_data[GV_FIELD_GLOBE_RENDER_RADIUS] = np.array([0.0])
    with pytest.raises(ValueError, match="render_radius must be finite and positive"):
        Globe.from_mesh(mesh)


@pytest.mark.parametrize("render_radius", RADII)
def test_gvradius_gives_the_render_radius(render_radius):
    """Test that a gvRadius is read as the render radius (scene spec §4.4 item 1)."""
    mesh = sphere(render_radius)
    assert Globe.from_mesh(mesh) == Globe(render_radius=render_radius)


@pytest.mark.parametrize("render_radius", RADII)
def test_a_sphere_reads_at_its_radius(render_radius):
    """Test that points at one radius give it (scene spec §4.4 item 2)."""
    mesh = sphere(render_radius, record=False)
    assert Globe.from_mesh(mesh) == Globe(render_radius=render_radius)


@pytest.mark.parametrize("render_radius", [0.5, *RADII])
@pytest.mark.parametrize("resolution", [30, 100])
def test_a_float32_sphere_reads_at_its_radius(render_radius, resolution):
    """Test that a sphere of float32 points reads at its radius, exactly.

    The mean radius of its points is not exactly its radius, as that of
    ``pv.Sphere()``, at 0.5, is 0.50000000018.
    """
    mesh = pv.Sphere(
        radius=render_radius, theta_resolution=resolution, phi_resolution=resolution
    )
    assert mesh.points.dtype == np.float32
    assert Globe.from_mesh(mesh) == Globe(render_radius=render_radius)


def test_a_flat_mesh_has_no_globe():
    """Test that a flat mesh has no globe."""
    assert Globe.from_mesh(pv.Plane()) is None


def test_a_warped_mesh_has_no_globe():
    """Test that a mesh warped by its heights has no globe (scene spec §3.4)."""
    mesh = lfric_orog()
    del mesh.field_data[GV_FIELD_RADIUS]
    assert Globe.from_mesh(mesh) == Globe()
    mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
    mesh.warp_by_scalar(inplace=True, factor=2e-5)
    assert Globe.from_mesh(mesh) is None


def test_a_degenerate_mesh_has_no_globe():
    """Test that a mesh with no points, or none away from the origin, has none."""
    assert Globe.from_mesh(pv.PolyData()) is None
    assert Globe.from_mesh(pv.PolyData(np.zeros((3, 3)))) is None
    mesh = sphere(record=False)
    mesh.points[0] = np.nan
    assert Globe.from_mesh(mesh) is None


@pytest.mark.parametrize("record", [True, False])
def test_reading_leaves_the_mesh_unchanged(record):
    """Test that reading a globe never changes the mesh."""
    mesh = sphere(record=record)
    before = mesh.copy()
    names = list(mesh.field_data)
    Globe.from_mesh(mesh)
    assert mesh == before
    assert list(mesh.field_data) == names
