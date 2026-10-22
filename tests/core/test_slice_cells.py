# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.core.slice_cells`."""

from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv
from pyvista import ImageData

from geovista.bridge import Transform
from geovista.common import point_cloud
from geovista.core import slice_cells


def test_mesh_fail():
    """Test trap of mesh instance type."""
    ugrid = ImageData()
    emsg = f"Require a {str(pv.PolyData)!r} mesh"
    with pytest.raises(TypeError, match=emsg):
        _ = slice_cells(ugrid)


def test_point_cloud_pass_thru(lam_uk):
    """Test point-cloud nop."""
    cloud = pv.PolyData(lam_uk.points)
    assert point_cloud(cloud)
    result = slice_cells(cloud)
    assert result is cloud
    assert result == cloud


@pytest.fixture
def grid():
    """Return a global grid of 8 by 4 cells, with a cell array and a point array."""
    mesh = Transform.from_1d(np.linspace(-180, 180, 9), np.linspace(-90, 90, 5))
    mesh.point_data["points"] = np.arange(mesh.n_points, dtype=float)
    mesh.cell_data["cells"] = np.arange(mesh.n_cells, dtype=float)
    return mesh


#: A meridian that bisects cells, and the antimeridian, which follows cell edges.
SEAMS = pytest.mark.parametrize(
    "seam", [{"meridian": 20}, {"antimeridian": True}], ids=["bisect", "edge"]
)


@SEAMS
def test_point_and_cell_arrays_share_a_name(grid, seam):
    """Test a point array and a cell array of the same name both survive."""
    grid.rename_array("points", "data")
    grid.rename_array("cells", "data")

    result = slice_cells(grid, **seam)

    assert result.point_data["data"].size == result.n_points
    assert result.cell_data["data"].size == result.n_cells


@SEAMS
def test_no_vtk_arrays(grid, seam):
    """Test the arrays VTK adds as it extracts and removes cells are purged."""
    result = slice_cells(grid, **seam)

    names = [*result.point_data, *result.cell_data]
    assert not [name for name in names if name.startswith("vtk")]
    assert {"points", "cells"} <= set(names)


@SEAMS
@pytest.mark.parametrize("association", ["point", "cell"])
def test_active_vtk_ids(grid, seam, association):
    """Test a mesh whose active scalars are VTK's ids is sliced, without them.

    The ids are purged, so the result has no active scalars to restore.

    """
    mesh = grid.extract_surface(algorithm="dataset_surface")
    name = f"vtkOriginal{association.capitalize()}Ids"
    mesh.set_active_scalars(name, preference=association)

    result = slice_cells(mesh, **seam)

    assert result.active_scalars_name is None
    assert name not in [*result.point_data, *result.cell_data]
