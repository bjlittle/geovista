# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotterBase.add_coastlines`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.common import ZLEVEL_SCALE, distance
from geovista.geoplotter import GeoPlotter
from geovista.globe import Globe


@pytest.mark.parametrize("radius", [1.0, 6378137.0])
def test_a_lifted_layer_keeps_its_lift(radius):
    """The coastlines are lifted above the scene's globe, and record it."""
    p = GeoPlotter(globe=Globe(render_radius=radius))
    drawn = p.add_coastlines().mapper.dataset
    np.testing.assert_allclose(
        distance(drawn, mean=False), radius * (1 + ZLEVEL_SCALE), rtol=1e-6
    )
    assert Globe.from_mesh(drawn) == p.globe


def test_radius_is_gone():
    """The radius keyword is refused."""
    with pytest.raises(TypeError, match="radius"):
        GeoPlotter().add_coastlines(radius=1.0)
