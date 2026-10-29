# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.crs._ellipsoidal_height`."""

from __future__ import annotations

import pytest

from geovista.crs import _ellipsoidal_height


def test_an_ellipsoidal_height():
    """WGS 84 in three dimensions has an ellipsoidal height."""
    assert _ellipsoidal_height("EPSG:4979")


@pytest.mark.parametrize(
    "crs", ["EPSG:4326", "EPSG:9705", "EPSG:4326+3855", "+proj=eqc"]
)
def test_no_ellipsoidal_height(crs):
    """A horizontal CRS, or one with a gravity-related height, has none."""
    assert not _ellipsoidal_height(crs)
