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
    p.add_graticule(name=name)
    if name is None:
        name = "graticule"
    expected = {
        f"{name}-meridian",
        f"{name}-parallel",
        f"{name}-meridian-labels",
        f"{name}-parallel-labels",
    }
    assert set(p.actors.keys()) == expected
