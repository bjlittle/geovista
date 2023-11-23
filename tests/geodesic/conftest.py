# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""pytest fixture infra-structure for :mod:`geovista.geodesic` unit-tests."""
from __future__ import annotations

import pytest

from geovista.common import from_cartesian

# cubed-sphere antarctic panel corner cell-ids (top to bottom, left to right)
CIDS = [11520, 11567, 13776, 13823]


@pytest.fixture()
def antarctic_corners(lfric_sst):
    """Fixture generates lon/lats of cubed-sphere corner cells centers."""
    cells = lfric_sst.extract_cells(CIDS)
    cell_centers = cells.cell_centers()
    lonlat = from_cartesian(cell_centers)[[0, 1, 3, 2]]
    return lonlat[:, 0], lonlat[:, 1]
