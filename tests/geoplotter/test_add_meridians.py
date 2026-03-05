# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.add_meridians`."""

from __future__ import annotations

import pytest

from geovista.geoplotter import GeoPlotter


@pytest.mark.parametrize("name", [None, "test"], ids=["no-name", "name"])
def test_meridians_actor_naming(name):
    """Test meridian actor naming."""
    p = GeoPlotter()
    p.add_meridians(name=name, show_labels=True)
    actors = p.actors.keys()
    meridians = [actor.split("-") for actor in actors if "labels" not in actor]
    assert len(meridians) == 8

    if name is None:
        expected_meridian_labels = "meridian-labels"
    else:
        expected_meridian_labels = f"meridian-{name}-labels"

    assert expected_meridian_labels in actors
    expected_meridians = {"180", "135W", "90W", "45W", "0", "45E", "90E", "135E"}
    assert {label[1] for label in meridians} == expected_meridians
