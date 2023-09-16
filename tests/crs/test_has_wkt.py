"""Unit-test for :func:`geovista.crs.has_wkt`."""
from __future__ import annotations

import pytest

from geovista.crs import has_wkt


@pytest.mark.parametrize("mesh, expected", [("sphere", False), ("lfric", True)])
def test(mesh, expected, request):
    """Test mesh wkt serialization availability."""
    mesh = request.getfixturevalue(mesh)
    result = has_wkt(mesh)
    assert result is expected
