# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter` creation."""

from __future__ import annotations

import warnings

import pytest
import pyvista as pv

from geovista.common import GV_FIELD_CRS
from geovista.geoplotter import GeoPlotter


def test_no_crs_warn(lfric):
    """Test warning for populated mesh with no attached CRS."""
    mesh = lfric.copy(deep=True)
    assert GV_FIELD_CRS in mesh.field_data
    del mesh.field_data[GV_FIELD_CRS]
    p = GeoPlotter()
    wmsg = "geovista found no coordinate reference system"
    with pytest.warns(UserWarning, match=wmsg):
        _ = p.add_mesh(mesh)


def test_crs_no_warn(lfric):
    """Test no warning for populated mesh with attached CRS."""
    mesh = lfric.copy(deep=True)
    assert GV_FIELD_CRS in mesh.field_data
    p = GeoPlotter()
    with warnings.catch_warnings(record=True) as warn:
        warnings.simplefilter("always")
        _ = p.add_mesh(mesh)
    assert len(warn) == 0


def test_no_crs_no_warn():
    """Test no warning for empty mesh with no attached CRS."""
    empty = pv.PolyData()
    assert GV_FIELD_CRS not in empty.field_data
    p = GeoPlotter()
    with warnings.catch_warnings(record=True) as warn:
        warnings.simplefilter("always")
        emsg = "Empty meshes cannot be plotted."
        with pytest.raises(ValueError, match=emsg):
            _ = p.add_mesh(empty)
    assert len(warn) == 0
