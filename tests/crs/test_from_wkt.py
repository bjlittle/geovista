# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-test for :func:`geovista.crs.from_wkt`."""

from __future__ import annotations

from pyproj import CRS
import pyvista as pv
from vtkmodules.vtkCommonCore import vtkStringArray

from geovista.common import GV_FIELD_CRS
from geovista.crs import WGS84, from_wkt


def test(lam_uk):
    """Test OGC WKT de-serialization of mesh CRS."""
    assert GV_FIELD_CRS in lam_uk.field_data
    crs = from_wkt(lam_uk)
    assert crs == WGS84


def test__no_crs():
    """Test mesh with no CRS to de-serialize."""
    mesh = pv.Plane()
    assert from_wkt(mesh) is None


def test__stored_before_escaping(sphere):
    """Test a mesh whose ASCII WKT was stored verbatim still reads.

    Meshes serialized before :issue:`2595` hold the WKT as it came from pyproj.

    """
    sphere.field_data[GV_FIELD_CRS] = [WGS84.to_wkt()]
    assert from_wkt(sphere) == WGS84


def test__stored_raw_by_vtk(sphere):
    """Test a mesh whose non-ASCII WKT was stored raw by VTK still reads.

    pyvista refuses such text, but VTK and other tools store it as it is.

    """
    crs = CRS.from_user_input("EPSG:3857")
    array = vtkStringArray()
    array.SetName(GV_FIELD_CRS)
    array.InsertNextValue(crs.to_wkt())
    sphere.GetFieldData().AddArray(array)
    assert from_wkt(sphere) == crs
