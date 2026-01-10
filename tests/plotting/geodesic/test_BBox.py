# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geodesic.BBox`."""

from __future__ import annotations

import pytest

import geovista as gv
from geovista.geodesic import panel


@pytest.mark.image
def test_outline(plot_nodeid, verify_image_cache):
    """Test edge outline of bounding-box manifold."""
    verify_image_cache.test_name = plot_nodeid
    p = gv.GeoPlotter()
    bbox = panel("arctic")
    p.add_mesh(bbox.mesh, color="orange")
    p.add_mesh(bbox.outline, color="yellow", line_width=3)
    p.add_base_layer(texture=gv.natural_earth_1(), opacity=0.5)
    p.view_vector(vector=(1, 1, 0))
    p.camera.zoom(1.5)
    p.show()
