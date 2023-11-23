# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.sanitize_data`."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

if TYPE_CHECKING:
    import pyvista as pv

from geovista.common import VTK_CELL_IDS, VTK_POINT_IDS, sanitize_data


def test_meshes_fail():
    """Test trap of no meshes."""
    emsg = "Expected one or more meshes"
    with pytest.raises(ValueError, match=emsg):
        sanitize_data()


def test(lam_uk):
    """Test removed of VTK point and cell metadata."""

    def _available(mesh: pv.PolyData) -> bool:
        return VTK_CELL_IDS in mesh.cell_data or VTK_POINT_IDS in mesh.point_data

    assert not _available(lam_uk)
    lam_uk.cell_data[VTK_CELL_IDS] = np.arange(lam_uk.n_cells)
    lam_uk.point_data[VTK_POINT_IDS] = np.arange(lam_uk.n_points)
    meshes = [lam_uk.copy() for i in range(10)]
    for mesh in meshes:
        assert _available(mesh)
    sanitize_data(*meshes)
    for mesh in meshes:
        assert not _available(mesh)
