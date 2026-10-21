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
    mocker,
    lonlat,
    *,
    mask=None,
    manifold=None,
    crs=None,
    zlevel=None,
    zscale=None,
) -> tuple[np.ndarray, list[str]]:
    """Return the points and labels passed on to add_point_labels."""
    p = GeoPlotter(manifold=manifold, crs=crs)
    spy = mocker.spy(p, "add_point_labels")
    graticule = GraticuleGrid(
        blocks=pv.MultiBlock(), lonlat=lonlat, labels=LABELS, mask=mask
    )

    p._add_graticule_labels(graticule, zlevel=zlevel, zscale=zscale)

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


def test_planar_labels_honour_zscale(mocker):
    """On a planar CRS the labels are lifted by the zscale they are given."""
    points, _ = _labelled(
        mocker, np.array(LONLAT), crs="+proj=eqc", zlevel=3, zscale=1e-3
    )

    # zlevel 3, zscale 1e-3 and the WGS84 semi-major axis of 6378137 m,
    # which is the height add_mesh gives a gridline on the same terms
    np.testing.assert_allclose(points[:, 2], 19134.411)
