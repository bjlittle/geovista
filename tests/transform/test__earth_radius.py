# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.transform._earth_radius`."""

from __future__ import annotations

from pyproj import CRS
import pytest

from geovista.transform import _earth_radius

#: A local engineering CRS, which has no ellipsoid.
ENGINEERING = (
    'ENGCRS["local",EDATUM["site"],CS[Cartesian,2],'
    'AXIS["x",east,LENGTHUNIT["metre",1]],AXIS["y",north,LENGTHUNIT["metre",1]]]'
)


def test_needs_an_ellipsoid():
    """A CRS without an ellipsoid has no radius to scale a level by.

    No CRS that ``transform_mesh`` can reach lacks one, since ``pyproj`` refuses to
    transform to an engineering or a vertical CRS, so the guard is tested here directly.

    """
    with pytest.raises(ValueError, match="Cannot determine the radius of the Earth"):
        _ = _earth_radius(CRS.from_wkt(ENGINEERING))
