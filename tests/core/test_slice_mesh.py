# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.core.slice_mesh`."""

from __future__ import annotations

import numpy as np

from geovista.bridge import Transform
from geovista.common import GV_CELL_IDS, GV_POINT_IDS
from geovista.core import slice_mesh


def test_the_given_mesh_is_unchanged():
    """Test slicing a mesh at the antimeridian adds no arrays to it (#2937)."""
    mesh = Transform.from_1d(np.arange(-180, 181, 10.0), np.arange(-90, 91, 10.0))
    mesh.cell_data["data"] = np.arange(mesh.n_cells)
    expected = (sorted(mesh.cell_data), sorted(mesh.point_data))
    result = slice_mesh(mesh)
    assert (sorted(mesh.cell_data), sorted(mesh.point_data)) == expected
    # the result still carries the ids the slice is traced by
    assert GV_CELL_IDS in result.cell_data
    assert GV_POINT_IDS in result.point_data
