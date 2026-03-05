# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.add_meridian`."""

from __future__ import annotations

import pytest

from geovista.geoplotter import GeoPlotter


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-180, "180"),
        (-135, "135W"),
        (-90, "90W"),
        (-45, "45W"),
        (0, "0"),
        (45, "45E"),
        (90, "90E"),
        (135, "135E"),
    ],
)
@pytest.mark.parametrize("name", [None, "test"], ids=["no-name", "name"])
def test_meridian_actor_naming(name, value, expected):
    """Test meridian actor naming."""
    p = GeoPlotter()
    p.add_meridian(value, name=name, show_labels=True)
    actors = p.actors.keys()
    meridians = [actor.split("-") for actor in actors if "labels" not in actor]
    assert len(meridians) == 1
    (meridian,) = meridians
    assert len(actors) == 2

    expected_meridian_labels = f"{'-'.join(meridian)}-labels"
    assert expected_meridian_labels in actors

    assert meridian[1] == expected
