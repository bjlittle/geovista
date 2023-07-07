"""Unit-tests for :func:`geovista.crs.to_wkt`."""
from __future__ import annotations

import pyvista as pv

from geovista.common import GV_FIELD_CRS
from geovista.crs import WGS84, from_wkt, to_wkt


def test():
    """Test OGC WKT serialization of CRS on mesh."""
    mesh = pv.Sphere()
    crs = WGS84
    to_wkt(mesh, crs)
    assert GV_FIELD_CRS in mesh.field_data
    wkt = WGS84.to_wkt()
    assert mesh.field_data[GV_FIELD_CRS] == wkt
    assert from_wkt(mesh) == WGS84
