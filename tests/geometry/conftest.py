"""pytest fixture infra-structure for :mod:`geovista.geometry` unit-tests."""

import pytest

from geovista.crs import WGS84


@pytest.fixture(params=["110m", "50m", "10m"])
def resolution(request):
    """Fixture for testing each of the Natural Earth coastline resolutions."""
    return request.param


@pytest.fixture
def wgs84_wkt():
    """Fixture for generating WG284 CRS WKT as a string."""
    return WGS84.to_wkt()
