# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.accessor.GeoVistaAccessor`."""

from __future__ import annotations

import copy
import pickle
import re

import numpy as np
import pytest
import pyvista as pv

from geovista.accessor import GeoVistaAccessor
from geovista.bridge import Transform
from geovista.common import GV_FIELD_CRS, GV_FIELD_GLOBE_RADIUS
from geovista.crs import from_wkt
from geovista.globe import Globe

LONS = np.linspace(-180, 180, 9)
LATS = np.linspace(-90, 90, 5)

#: A render radius of 1, and of the Earth's radius (scene spec §6).
RADII = [1.0, 6378137.0]


@pytest.mark.parametrize(
    "mesh",
    [pv.PolyData(), pv.UnstructuredGrid(), pv.StructuredGrid(), pv.ImageData()],
    ids=lambda mesh: type(mesh).__name__,
)
def test_every_mesh_has_the_namespace(mesh):
    """Test that every pyvista mesh has mesh.gv."""
    assert isinstance(mesh.gv, GeoVistaAccessor)


@pytest.mark.parametrize("render_radius", RADII)
def test_reads_what_the_mesh_records(render_radius):
    """Test that the namespace reads the mesh's CRS and globe."""
    mesh = Transform.from_1d(LONS, LATS, globe=Globe(render_radius=render_radius))
    assert mesh.gv.crs == from_wkt(mesh)
    assert mesh.gv.crs is not None
    assert mesh.gv.globe == Globe(render_radius=render_radius)


def test_follows_a_change_to_its_field_data():
    """Test that each read follows the mesh, never a value read before."""
    mesh = Transform.from_1d(LONS, LATS)
    assert mesh.gv.globe == Globe()
    Globe(exaggeration=20).to_mesh(mesh)
    assert mesh.gv.globe == Globe(exaggeration=20)
    assert mesh.gv.crs is not None
    del mesh.field_data[GV_FIELD_CRS]
    assert mesh.gv.crs is None


@pytest.mark.parametrize(
    "duplicate",
    [
        lambda mesh: mesh.copy(),
        lambda mesh: mesh.copy(deep=False),
        copy.copy,
        copy.deepcopy,
        lambda mesh: pickle.loads(pickle.dumps(mesh)),  # noqa: S301
    ],
    ids=["copy", "shallow-copy", "copy.copy", "copy.deepcopy", "pickle"],
)
def test_a_copy_reads_its_own_record(duplicate):
    """Test that a copy's namespace reads the copy, never the original."""
    mesh = Transform.from_1d(LONS, LATS)
    assert mesh.gv.globe == Globe()
    other = duplicate(mesh)
    Globe(render_radius=2).to_mesh(other)
    assert other.gv.globe == Globe(render_radius=2)
    assert mesh.gv.globe == Globe()


def test_reading_leaves_the_mesh_unchanged():
    """Test that reading the namespace never changes the mesh."""
    mesh = Transform.from_1d(LONS, LATS)
    before = mesh.copy()
    names = list(mesh.field_data)
    _ = mesh.gv.globe, mesh.gv.crs, repr(mesh.gv)
    assert mesh == before
    assert list(mesh.field_data) == names


def test_the_globe_cannot_be_set():
    """Test that setting the globe names resize, which moves the points."""
    mesh = Transform.from_1d(LONS, LATS)
    with pytest.raises(AttributeError, match=re.escape("resize(mesh, globe=...)")):
        mesh.gv.globe = Globe()


def test_the_crs_cannot_be_set():
    """Test that setting the CRS names transform_mesh, which moves the points."""
    mesh = Transform.from_1d(LONS, LATS)
    with pytest.raises(AttributeError, match="transform_mesh"):
        mesh.gv.crs = None


def test_equal_when_the_crs_and_globe_are():
    """Test that namespaces compare CRSs and globes, never geometry."""
    mesh = Transform.from_1d(LONS, LATS)
    assert mesh.gv == Transform.from_1d(LONS[:5], LATS).gv
    other = Transform.from_1d(LONS, LATS)
    Globe(render_radius=2).to_mesh(other)
    assert mesh.gv != other.gv
    other = Transform.from_1d(LONS, LATS)
    del other.field_data[GV_FIELD_CRS]
    assert mesh.gv != other.gv
    assert (mesh.gv == object()) is False


def test_is_unhashable():
    """Test that the namespace is unhashable, as it follows a mutable mesh."""
    with pytest.raises(TypeError):
        hash(pv.PolyData().gv)


def test_the_repr_names_geovista():
    """Test that the repr names geovista, even for a globe that cannot be read."""
    mesh = Transform.from_1d(LONS, LATS)
    assert "geovista" in repr(mesh.gv)
    assert "WGS 84" in repr(mesh.gv)
    Globe().to_mesh(mesh)
    del mesh.field_data[GV_FIELD_GLOBE_RADIUS]
    text = repr(mesh.gv)
    assert "geovista" in text
    assert "gvGlobeRadius" in text


def test_the_docstring_names_geovista():
    """Test that help(mesh.gv) names geovista."""
    assert "geovista" in (pv.PolyData.gv.__doc__ or "")
