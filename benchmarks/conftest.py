# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Fixtures and settings shared by the benchmarks.

Every input is built outside the measured call, from a seeded generator where it
is random, and nothing is downloaded, so a run needs neither the network nor the
pooch cache (bench spec §2 decision 7). VTK runs on one thread, so an instruction
count never depends on how its work was split, and nothing is rendered to a
window.

Under ``--memray``, a benchmark that carries no memory ceiling is refused
(bench spec §2 decision 5). The ceiling's marker is registered here too, so that
the CodSpeed run, which disables memray, still accepts it under
``--strict-markers``.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest
import pyvista as pv
from vtkmodules.vtkCommonCore import vtkSMPTools

import geovista as gv

if TYPE_CHECKING:
    from collections.abc import Iterable

pv.OFF_SCREEN = True

# pin VTK to one thread, so that an instruction count never depends on how
# its work was split (bench spec §2 decision 7)
vtkSMPTools.Initialize(1)

#: The marker of pytest-memray carrying a benchmark's memory ceiling.
CEILING = "limit_memory"

#: The cell size of the global grid, in degrees.
GRID_STEP = 1.0

#: The number of vertices of the line, as in issue 2913.
LINE_VERTICES = 2_000


def pytest_configure(config: pytest.Config) -> None:
    """Register the ceiling's marker, for a run with memray disabled.

    Parameters
    ----------
    config : pytest.Config
        The pytest configuration.

    """
    config.addinivalue_line(
        "markers",
        f"{CEILING}(memory_limit): the peak memory a benchmark may reach",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: Iterable[pytest.Item]
) -> None:
    """Refuse, under memray, every benchmark that carries no memory ceiling.

    Parameters
    ----------
    config : pytest.Config
        The pytest configuration.
    items : iterable of pytest.Item
        The collected benchmarks.

    Raises
    ------
    pytest.UsageError
        Naming each benchmark that carries no ceiling (bench spec §2 decision 5).

    """
    if not config.getoption("memray", default=False):
        return
    bare = [item.name for item in items if item.get_closest_marker(CEILING) is None]
    if bare:
        emsg = (
            "bench spec §2 decision 5: every benchmark carries a memory ceiling, "
            "its measured peak plus 20%, rounded up to a whole MiB, as "
            '@pytest.mark.limit_memory("N MB"). None on: ' + ", ".join(bare)
        )
        raise pytest.UsageError(emsg)


@pytest.fixture
def grid_mesh() -> pv.PolyData:
    """Return a global mesh of 1° cells, 360 by 180, carrying seeded cell data.

    The mesh is built afresh for each benchmark, which may change it.

    Returns
    -------
    pyvista.PolyData
        The mesh, its cell data named ``"data"``.

    """
    lons = np.arange(-180, 180 + GRID_STEP, GRID_STEP)
    lats = np.arange(-90, 90 + GRID_STEP, GRID_STEP)
    rng = np.random.default_rng(0)
    data = rng.random((lats.size - 1) * (lons.size - 1))
    return gv.Transform.from_1d(lons, lats, data=data, name="data")


@pytest.fixture(scope="session")
def line() -> tuple[np.ndarray, np.ndarray]:
    """Return the longitudes and latitudes of a line through 2,000 vertices.

    Returns
    -------
    tuple of numpy.ndarray
        The longitudes, evenly spaced from -170° to 170°, and the latitudes,
        drawn from a seeded generator between -60° and 60°.

    """
    rng = np.random.default_rng(0)
    lons = np.linspace(-170, 170, LINE_VERTICES)
    lats = rng.uniform(-60, 60, LINE_VERTICES)
    return lons, lats
