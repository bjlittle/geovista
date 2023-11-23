# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.crs.to_wkt`."""
from __future__ import annotations

from geovista.common import GV_FIELD_CRS
from geovista.crs import WGS84, from_wkt, to_wkt


def test(sphere):
    """Test OGC WKT serialization of CRS on mesh."""
    crs = WGS84
    to_wkt(sphere, crs)
    assert GV_FIELD_CRS in sphere.field_data
    wkt = WGS84.to_wkt()
    assert sphere.field_data[GV_FIELD_CRS] == wkt
    assert from_wkt(sphere) == WGS84
