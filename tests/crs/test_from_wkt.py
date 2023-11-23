# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-test for :func:`geovista.crs.from_wkt`."""
from __future__ import annotations

import pyvista as pv

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
