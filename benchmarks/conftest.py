# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Shared fixtures for the CodSpeed performance benchmarks.

Every fixture is synthetic, built from ``numpy`` alone, so that the benchmarks
need neither network access nor the cached sample data of :mod:`geovista.pantry`.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

import geovista as gv

if TYPE_CHECKING:
    import pyvista as pv

#: The number of cells along the longitude axis of the global grid.
NLON = 180
#: The number of cells along the latitude axis of the global grid.
NLAT = 90


@pytest.fixture(scope="session")
def lons() -> np.ndarray:
    """Return the contiguous 1D cell boundaries of a global longitude axis."""
    return np.linspace(-180, 180, num=NLON + 1)


@pytest.fixture(scope="session")
def lats() -> np.ndarray:
    """Return the contiguous 1D cell boundaries of a global latitude axis."""
    return np.linspace(-90, 90, num=NLAT + 1)


@pytest.fixture(scope="session")
def data() -> np.ndarray:
    """Return deterministic cell data for the global grid."""
    rng = np.random.default_rng(seed=0)
    return rng.random(NLAT * NLON)


@pytest.fixture(scope="session")
def lons_2d(lons: np.ndarray, lats: np.ndarray) -> np.ndarray:
    """Return the 2D longitude nodes of the global grid."""
    return np.meshgrid(lons, lats)[0]


@pytest.fixture(scope="session")
def lats_2d(lons: np.ndarray, lats: np.ndarray) -> np.ndarray:
    """Return the 2D latitude nodes of the global grid."""
    return np.meshgrid(lons, lats)[1]


@pytest.fixture
def mesh(lons: np.ndarray, lats: np.ndarray, data: np.ndarray) -> pv.PolyData:
    """Return a fresh global quad-faced mesh carrying cell data."""
    return gv.Transform.from_1d(lons, lats, data=data, name="data")
