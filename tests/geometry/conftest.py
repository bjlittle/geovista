# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""pytest fixture infra-structure for :mod:`geovista.geometry` unit-tests."""

from __future__ import annotations

import pytest


@pytest.fixture(params=["110m", "50m", "10m"])
def resolution(request):
    """Fixture for testing each of the Natural Earth coastline resolutions."""
    return request.param
