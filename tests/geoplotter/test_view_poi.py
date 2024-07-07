# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.view_poi`."""

from __future__ import annotations

import pytest

from geovista.geoplotter import GeoPlotter


def test_no_poi_warning():
    """Test warning raised for no POI."""
    plotter = GeoPlotter()
    wmsg = r"No point-of-interest \(POI\) is available or has been provided."
    with pytest.warns(UserWarning, match=wmsg):
        plotter.view_poi()
