# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.pantry.data.name_reykjanes`."""

from __future__ import annotations

import pytest

from geovista.pantry.data import name_reykjanes


@pytest.fixture
def sample(mocker):
    """Load the sample afresh, failing should it geocode over the network."""
    _ = mocker.patch(
        "geopy.geocoders.Nominatim.geocode",
        side_effect=AssertionError("the sample geocoded over the network"),
    )
    name_reykjanes.cache_clear()
    yield name_reykjanes()
    name_reykjanes.cache_clear()


def test_poi(sample):
    """Test the point-of-interest is the release location the sample records.

    The file gives it as "22.3840W   63.8820N". A geocoder asked for those
    coordinates answers with the nearest named place instead, which is the
    town of Grindavik, some 4.8 km away.

    """
    assert sample.poi.longitude == pytest.approx(-22.3840)
    assert sample.poi.latitude == pytest.approx(63.8820)


def test_grid(sample):
    """Test the sample carries its structured grid and payload."""
    assert sample.data.shape == (
        len(sample.zs) - 1,
        len(sample.ys) - 1,
        len(sample.xs) - 1,
    )
    assert sample.name
    assert sample.units
