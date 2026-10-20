# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.core.MeridianSlice`."""

from __future__ import annotations

import pytest
import pyvista as pv

from geovista.bridge import Transform
from geovista.core import MeridianSlice


@pytest.mark.parametrize("preference", ["cell", "point"])
def test_active_scalars_kept(preference):
    """Test the active scalars keep their association when both share a name."""
    mesh = Transform.from_1d([-10, 0, 10, 20], [-10, 0, 10])
    mesh.point_data["data"] = range(mesh.n_points)
    mesh.cell_data["data"] = range(mesh.n_cells)
    mesh.set_active_scalars("data", preference=preference)
    expected = mesh.active_scalars_info
    _ = MeridianSlice(mesh, 5)
    assert mesh.active_scalars_info == expected
    assert expected.association == pv.FieldAssociation[preference.upper()]
