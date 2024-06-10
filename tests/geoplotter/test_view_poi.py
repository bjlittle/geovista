# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.view_poi`."""

from __future__ import annotations

import pytest

from geovista.geoplotter import GeoPlotter


@pytest.mark.parametrize(("x", "y"), [(0, None), (None, 0)])
def test_underspecified_points_fail(x, y):
    """Test trap of missing explicit POI value."""
    plotter = GeoPlotter()
    emsg = r"Point-of-interest \(POI\) requires both an 'x' and 'y' value."
    with pytest.raises(ValueError, match=emsg):
        plotter.view_poi(x, y)


def test_no_poi_warning():
    """Test warning raised for no POI."""
    plotter = GeoPlotter()
    wmsg = r"No point-of-interest \(POI\) is available or has been provided."
    with pytest.warns(UserWarning, match=wmsg):
        plotter.view_poi()
