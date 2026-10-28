# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.add_parallels`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.common import ZLEVEL_SCALE, distance
from geovista.geoplotter import GeoPlotter
from geovista.globe import Globe
from geovista.gridlines import GRATICULE_ZLEVEL


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


def _lines(p: GeoPlotter) -> list:
    """Return each mesh of lines the scene draws."""
    return [
        actor.mapper.dataset
        for actor in p.actors.values()
        if getattr(actor, "mapper", None) is not None
        and getattr(actor.mapper, "dataset", None) is not None
        and actor.mapper.dataset.n_lines
    ]


@pytest.mark.parametrize("radius", [1.0, 6378137.0])
def test_at_the_scenes_globe(radius):
    """The lines are lifted above the scene's globe, and record it."""
    p = GeoPlotter(globe=Globe(render_radius=radius))
    p.add_parallels()
    lines = _lines(p)
    assert lines
    for mesh in lines:
        np.testing.assert_allclose(
            distance(mesh, mean=False),
            radius * (1 + GRATICULE_ZLEVEL * ZLEVEL_SCALE),
            rtol=1e-12,
        )
        assert Globe.from_mesh(mesh) == p.globe


@pytest.mark.parametrize("radius", [1.0, 6378137.0])
def test_a_zlevel_lifts_the_lines_once(mocker, radius):
    """A z-level lifts the lines once, to their labels (call 9 of the plan)."""
    p = GeoPlotter(globe=Globe(render_radius=radius))
    labels = mocker.spy(p, "add_point_labels")
    p.add_parallels(zlevel=5, show_labels=True)
    expected = radius * (1 + 5 * ZLEVEL_SCALE)
    for mesh in _lines(p):
        np.testing.assert_allclose(distance(mesh, mean=False), expected, rtol=1e-12)
    points = np.asarray(labels.call_args.args[0])
    np.testing.assert_allclose(np.linalg.norm(points, axis=1), expected, rtol=1e-12)


def test_radius_is_gone():
    """The radius keyword is refused."""
    with pytest.raises(TypeError, match="radius"):
        GeoPlotter().add_parallels(radius=1.0)
