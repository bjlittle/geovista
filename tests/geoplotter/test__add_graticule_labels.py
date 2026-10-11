# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter._add_graticule_labels`."""

from __future__ import annotations

import numpy as np
import pyvista as pv

from geovista.geodesic import BBox
from geovista.geoplotter import GeoPlotter
from geovista.gridlines import GraticuleGrid

#: The longitude/latitude points of two labels.
LONLAT = [[0.0, 0.0], [90.0, 0.0]]

#: The two labels.
LABELS = ["0°", "90°E"]


def _labelled(
    mocker, lonlat, *, mask=None, manifold=None
) -> tuple[np.ndarray, list[str]]:
    """Return the points and labels passed on to add_point_labels."""
    p = GeoPlotter(manifold=manifold)
    spy = mocker.spy(p, "add_point_labels")
    graticule = GraticuleGrid(
        blocks=pv.MultiBlock(), lonlat=lonlat, labels=LABELS, mask=mask
    )

    p._add_graticule_labels(graticule)

    points, labels = spy.call_args.args
    return points, labels


def test_lonlat_list(mocker):
    """A list of points is the points given as an array (typing spec §3.3)."""
    expected, _ = _labelled(mocker, np.array(LONLAT))

    result, _ = _labelled(mocker, LONLAT)

    np.testing.assert_array_equal(result, expected)


def test_mask_list(mocker):
    """A list mask is the mask given as an array (typing spec §3.3)."""
    expected, _ = _labelled(mocker, np.array(LONLAT), mask=np.array([True, False]))

    result, _ = _labelled(mocker, np.array(LONLAT), mask=[True, False])

    np.testing.assert_array_equal(result, expected)


def test_manifold_keeps_the_labels_inside(mocker):
    """A manifold keeps only the labels whose points it encloses."""
    manifold = BBox([-10, 10, 10, -10], [-10, -10, 10, 10])

    _, labels = _labelled(mocker, np.array(LONLAT), manifold=manifold)

    assert list(labels) == ["0°"]
