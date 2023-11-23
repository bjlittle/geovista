# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-test for :func:`geovista.crs.has_wkt`."""
from __future__ import annotations

import pytest

from geovista.crs import has_wkt


@pytest.mark.parametrize(("mesh", "expected"), [("sphere", False), ("lfric", True)])
def test(mesh, expected, request):
    """Test mesh wkt serialization availability."""
    mesh = request.getfixturevalue(mesh)
    result = has_wkt(mesh)
    assert result is expected
