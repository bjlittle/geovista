# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.add_parallel`."""

from __future__ import annotations

import pytest

from geovista.geoplotter import GeoPlotter


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-60, "60S"),
        (-30, "30S"),
        (0, "0"),
        (30, "30N"),
        (60, "60N"),
    ],
)
@pytest.mark.parametrize("name", [None, "test"], ids=["no-name", "name"])
def test_parallel_actor_naming(name, value, expected):
    """Test parallel actor naming."""
    p = GeoPlotter()
    p.add_parallel(value, name=name, show_labels=True)
    actors = p.actors.keys()
    parallels = [actor.split("-") for actor in actors if "labels" not in actor]
    assert len(parallels) == 1
    (parallel,) = parallels
    assert len(actors) == 2

    expected_parallel_labels = f"{'-'.join(parallel)}-labels"
    assert expected_parallel_labels in actors

    assert parallel[1] == expected
