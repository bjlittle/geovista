# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.core.add_texture_coords`."""

from __future__ import annotations

import pyvista as pv

from geovista.common import point_cloud
from geovista.core import add_texture_coords


def test_point_cloud_pass_thru(lam_uk):
    """Test point-cloud nop."""
    cloud = pv.PolyData(lam_uk.points)
    assert point_cloud(cloud)
    result = add_texture_coords(cloud)
    assert result is cloud
    assert result == cloud
