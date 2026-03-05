# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.add_graticule`."""

from __future__ import annotations

import pytest

from geovista.geoplotter import GeoPlotter


@pytest.mark.parametrize("name", [None, "test"])
def test_actor_naming(name):
    """Test graticule actor naming."""
    p = GeoPlotter()
    p.add_graticule(name=name, show_labels=True)
    actors = p.actors.keys()
    meridians = [
        actor.split("-")
        for actor in actors
        if actor.startswith("meridian")
        if "labels" not in actor
    ]
    parallels = [
        actor.split("-")
        for actor in actors
        if actor.startswith("parallel")
        if "labels" not in actor
    ]
    assert len(meridians) == 8
    assert len(parallels) == 5

    if name is None:
        expected_meridian_labels = "meridian-labels"
        expected_parallel_labels = "parallel-labels"
    else:
        expected_meridian_labels = f"meridian-{name}-labels"
        expected_parallel_labels = f"parallel-{name}-labels"

    assert expected_meridian_labels in actors
    assert expected_parallel_labels in actors

    expected_meridians = {"180", "135W", "90W", "45W", "0", "45E", "90E", "135E"}
    expected_parallels = {"60S", "30S", "0", "30N", "60N"}

    assert {label[1] for label in meridians} == expected_meridians
    assert {label[1] for label in parallels} == expected_parallels
