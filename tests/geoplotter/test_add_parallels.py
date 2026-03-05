# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.add_parallels`."""

from __future__ import annotations

import pytest

from geovista.geoplotter import GeoPlotter


@pytest.mark.parametrize("name", [None, "test"], ids=["no-name", "name"])
def test_parallels_actor_naming(name):
    """Test parallel actor naming."""
    p = GeoPlotter()
    p.add_parallels(name=name, show_labels=True)
    actors = p.actors.keys()
    parallels = [actor.split("-") for actor in actors if "labels" not in actor]
    assert len(parallels) == 5

    if name is None:
        expected_parallel_labels = "parallel-labels"
    else:
        expected_parallel_labels = f"parallel-{name}-labels"

    assert expected_parallel_labels in actors
    expected_parallels = {"60S", "30S", "0", "30N", "60N"}
    assert {label[1] for label in parallels} == expected_parallels
