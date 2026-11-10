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

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest
import pyvista as pv
from vtkmodules.vtkCommonCore import vtkSMPTools

import geovista as gv
from geovista.common import from_cartesian
from geovista.geodesic import BBox
from geovista.search import KDTree

if TYPE_CHECKING:
    from collections.abc import Iterable

pv.OFF_SCREEN = True

# pin VTK to one thread, so that an instruction count never depends on how
# its work was split (bench spec §2 decision 7)
vtkSMPTools.Initialize(1)

# make the process's first matrix product here, so that the buffers OpenBLAS
# sets up on it, 128 MiB under some of its kernels, are charged to no
# benchmark's memory ceiling (bench spec §2 decision 5)
np.eye(3) @ np.eye(3)

#: The marker of pytest-memray carrying a benchmark's memory ceiling.
CEILING = "limit_memory"

#: The directory of the benchmarks, whose items alone are held to a ceiling.
ROOT = Path(__file__).parent

#: The cell size of the global grid, in degrees.
GRID_STEP = 1.0

#: The number of vertices of the line, as in issue 2913.
LINE_VERTICES = 2_000

#: The number of points of the cloud.
CLOUD_POINTS = 100_000

#: The number of copies of the global grid a benchmark joins.
GRID_COPIES = 4


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
    # memray may be disabled, as the CodSpeed run has it; otherwise its switch is
    # read as pytest-memray reads it, so the two can never disagree
    if not config.pluginmanager.hasplugin("memray"):
        return
    # imported here, so that the benchmarks load where pytest-memray is absent
    from pytest_memray.utils import value_or_ini  # noqa: PLC0415

    if not value_or_ini(config, "memray"):
        return
    if names := bare(items, ROOT):
        emsg = (
            "bench spec §2 decision 5: every benchmark carries a memory ceiling, "
            "its measured peak plus 20%, rounded up to a whole MiB, as "
            '@pytest.mark.limit_memory("N MB"). None on: ' + ", ".join(names)
        )
        raise pytest.UsageError(emsg)


def bare(items: Iterable[pytest.Item], root: Path) -> list[str]:
    """Return the node id of each benchmark under ``root`` carrying no ceiling.

    Parameters
    ----------
    items : iterable of pytest.Item
        The collected items, which may include tests outside ``root``.
    root : Path
        The directory of the benchmarks.

    Returns
    -------
    list of str
        The node ids, in the order collected.

    """
    return [
        item.nodeid
        for item in items
        if item.path.is_relative_to(root) and item.get_closest_marker(CEILING) is None
    ]


@pytest.fixture(scope="session")
def grid_bounds() -> tuple[np.ndarray, np.ndarray]:
    """Return the 1-D cell bounds of the global grid, 1° cells, 360 by 180.

    Returns
    -------
    tuple of numpy.ndarray
        The 361 longitudes and the 181 latitudes.

    """
    lons = np.arange(-180, 180 + GRID_STEP, GRID_STEP)
    lats = np.arange(-90, 90 + GRID_STEP, GRID_STEP)
    return lons, lats


@pytest.fixture(scope="session")
def grid_bounds_2d(
    grid_bounds: tuple[np.ndarray, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    """Return the 2-D cell bounds of the global grid, as a curvilinear grid has them.

    Parameters
    ----------
    grid_bounds : tuple of numpy.ndarray
        The 1-D cell bounds.

    Returns
    -------
    tuple of numpy.ndarray
        The longitudes and the latitudes, each of shape (181, 361).

    """
    lons, lats = np.meshgrid(*grid_bounds)
    return lons, lats


@pytest.fixture(scope="session")
def grid_data(grid_bounds: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    """Return the seeded data of each cell of the global grid.

    Parameters
    ----------
    grid_bounds : tuple of numpy.ndarray
        The 1-D cell bounds.

    Returns
    -------
    numpy.ndarray
        The 64,800 values.

    """
    lons, lats = grid_bounds
    rng = np.random.default_rng(0)
    return rng.random((lats.size - 1) * (lons.size - 1))


@pytest.fixture(scope="session")
def grid_nodes(
    grid_bounds: tuple[np.ndarray, np.ndarray], grid_data: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the global grid as a reader of UGRID gives it: nodes and faces.

    Parameters
    ----------
    grid_bounds : tuple of numpy.ndarray
        The 1-D cell bounds.
    grid_data : numpy.ndarray
        The data of each cell.

    Returns
    -------
    tuple of numpy.ndarray
        The longitude and the latitude of each node, and the four nodes of
        each face.

    """
    mesh = gv.Transform.from_1d(*grid_bounds, data=grid_data)
    xyz = from_cartesian(mesh)
    return xyz[:, 0], xyz[:, 1], mesh.regular_faces


@pytest.fixture
def grid_mesh(
    grid_bounds: tuple[np.ndarray, np.ndarray], grid_data: np.ndarray
) -> pv.PolyData:
    """Return a global mesh of 1° cells, 360 by 180, carrying seeded cell data.

    The mesh is built afresh for each benchmark, which may change it.

    Parameters
    ----------
    grid_bounds : tuple of numpy.ndarray
        The 1-D cell bounds.
    grid_data : numpy.ndarray
        The data of each cell.

    Returns
    -------
    pyvista.PolyData
        The mesh, its cell data named ``"data"``.

    """
    # a copy, as the mesh shares the array it is given, and a benchmark may
    # change the mesh's data where the session's would see it
    return gv.Transform.from_1d(*grid_bounds, data=grid_data.copy(), name="data")


@pytest.fixture(scope="session")
def cloud() -> tuple[np.ndarray, np.ndarray]:
    """Return 100,000 seeded positions, spread evenly over the sphere.

    Returns
    -------
    tuple of numpy.ndarray
        The longitudes, uniform in [-180°, 180°), and the latitudes, the
        arcsine of a uniform value, so that equal areas hold equal numbers.

    """
    rng = np.random.default_rng(0)
    lons = rng.uniform(-180, 180, CLOUD_POINTS)
    lats = np.degrees(np.arcsin(rng.uniform(-1, 1, CLOUD_POINTS)))
    return lons, lats


@pytest.fixture(scope="session")
def cloud_mesh(cloud: tuple[np.ndarray, np.ndarray]) -> pv.PolyData:
    """Return the cloud of 100,000 positions as a mesh of points.

    Parameters
    ----------
    cloud : tuple of numpy.ndarray
        The longitudes and the latitudes.

    Returns
    -------
    pyvista.PolyData
        The points, which a benchmark reads but never changes.

    """
    return gv.Transform.from_points(*cloud)


@pytest.fixture
def grid_meshes(grid_mesh: pv.PolyData) -> list[pv.PolyData]:
    """Return four copies of the global grid's mesh, for a benchmark to join.

    Parameters
    ----------
    grid_mesh : pyvista.PolyData
        The global grid's mesh.

    Returns
    -------
    list of pyvista.PolyData
        The copies, built here so that a benchmark's memory ceiling holds the
        join alone.

    """
    return [grid_mesh.copy() for _ in range(GRID_COPIES)]


@pytest.fixture(scope="session")
def cloud_tree(cloud_mesh: pv.PolyData) -> KDTree:
    """Return a kd-tree over the cloud, which a query reads but never changes.

    Parameters
    ----------
    cloud_mesh : pyvista.PolyData
        The cloud as a mesh of points.

    Returns
    -------
    KDTree
        The tree, built here so that a benchmark's memory ceiling holds the
        query alone.

    """
    return KDTree(cloud_mesh)


@pytest.fixture(scope="session")
def bbox() -> BBox:
    """Return a geodesic box from 30° west to 30° east, and 20° south to 40° north.

    Returns
    -------
    BBox
        The box, built here so that a benchmark's memory ceiling holds the
        extraction alone.

    """
    return BBox([-30, 30, 30, -30], [-20, -20, 40, 40])


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
