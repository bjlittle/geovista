# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""pytest fixture infra-structure for :mod:`geovista.geodesic` unit-tests."""

from __future__ import annotations

from contextlib import suppress
import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pyproj
import pytest
import pyvista as pv

from geovista.bridge import Transform
from geovista.cache import CACHE
from geovista.common import _GV_GLOBE_FIELDS, GV_FIELD_RADIUS
from geovista.crs import WGS84
from geovista.geometry import coastlines as geometry_coastlines
from geovista.globe import Globe
from geovista.pantry.data import lam_uk as pantry_lam_uk
from geovista.pantry.meshes import lam_polar as sample_lam_polar
from geovista.pantry.meshes import lam_uk as sample_lam_uk
from geovista.pantry.meshes import lfric as sample_lfric
from geovista.pantry.meshes import lfric_sst as sample_lfric_sst
from geovista.transform import transform_mesh

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    from numpy.typing import ArrayLike

#: Fixtures this suite takes from pytest's own plugins.
pytest_plugins = ("pytester",)

#: The module holding the text of the repository check breadcrumb.
BREADCRUMB_PATH = Path(__file__).parents[1] / ".github" / "scripts" / "breadcrumb.py"

#: The option requiring, rather than skipping, each prerequisite of the
#: "tests/docs" browser tests.
BROWSER_STRICT = "--browser-strict"


def pytest_addoption(parser):
    """Register the geovista pytest command line options.

    Note that pytest honours this hook only in the test root conftest, so the
    browser test option is registered here rather than alongside the tests in
    "tests/docs" that consume it.

    Parameters
    ----------
    parser : pytest.Parser
        The pytest command line parser.

    """
    parser.addoption(
        BROWSER_STRICT,
        action="store_true",
        default=False,
        help=(
            "require, rather than skip, each prerequisite of the tests/docs "
            "browser tests e.g., the gallery carousel, which is rendered only by "
            "a plotting documentation build target"
        ),
    )


def load_breadcrumb() -> ModuleType:
    """Load the breadcrumb module, which the CI scripts load by path too.

    Returns
    -------
    ModuleType
        The module, defining ``breadcrumb``.

    """
    spec = importlib.util.spec_from_file_location("breadcrumb", BREADCRUMB_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: The breadcrumb that ends a failure of a repository check.
BREADCRUMB = load_breadcrumb()


@pytest.fixture(scope="session")
def breadcrumb() -> ModuleType:
    """Provide the breadcrumb module, loaded once for the hook and the tests.

    Returns
    -------
    ModuleType
        The module, defining ``breadcrumb``.

    """
    return BREADCRUMB


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):  # noqa: ARG001
    """End a failure of a repository check with a link to its section.

    A test module that holds the repository to a rule of ``geovista``'s own
    declares ``CHECK``, the name of the rule's section on the repository checks
    page. Any of its tests that fails, in a fixture or in the test itself, has
    the breadcrumb of checks spec §3.3 added to its report, so the individual
    assertions need not repeat it. It travels in the report, so a test run by a
    "pytest-xdist" worker carries it too.

    Parameters
    ----------
    item : pytest.Item
        The test whose report is made.
    call : pytest.CallInfo
        The call that was made, for each of setup, call and teardown.

    Yields
    ------
    None
        Control, to pytest's own report maker.

    Returns
    -------
    pytest.TestReport
        The report, with the breadcrumb added where the test failed.

    """
    report = yield
    name = getattr(getattr(item, "module", None), "CHECK", None)
    if report.failed and isinstance(name, str):
        hint = BREADCRUMB.breadcrumb(name)
        if hasattr(report.longrepr, "addsection"):
            report.longrepr.addsection("repository check", hint)
        else:
            report.sections.append(("repository check", hint))
    return report


@pytest.fixture
def plot_nodeid(request):
    """Fixture generates a dotted nodeid for plotting tests."""
    names = request.node.listnames()
    index = names.index("plotting")
    names = names[index + 1 :]

    # remove ".py" extension
    names[-2] = names[-2].split(".")[0]

    # reformat pytest parametrization syntax
    names[-1] = names[-1].replace("]", "")
    names[-1] = names[-1].replace("[", "__")
    name = ".".join(names)

    if not name.startswith("test_"):
        name = f"test_{name}"

    # ensure cache is populated with the *existing* baseline image
    # note that pytest-pyvista removes the "test_" prefix from the baseline image
    stem = f"tests/unit/{name.removeprefix('test_')}"

    with suppress(ValueError):
        _ = CACHE.fetch(f"{stem}.png")

    return name


@pytest.fixture
def coastlines(request):
    """Fixture generates a coastlines line mesh."""
    # support indirect parameters for fixtures and also
    # calling the fixture with no parameter
    resolution = request.param if hasattr(request, "param") else "110m"

    return geometry_coastlines(resolution=resolution)


@pytest.fixture
def lam_polar():
    """Fixture generates a Polar Local Area Model mesh with indexed faces and points."""
    mesh = sample_lam_polar()
    mesh.point_data["pids"] = np.arange(mesh.n_points)
    mesh.cell_data["cids"] = np.arange(mesh.n_cells)
    mesh.set_active_scalars("cids")
    return mesh


@pytest.fixture
def lam_uk():
    """Fixture generates a UK Local Area Model mesh with indexed faces and points."""
    mesh = sample_lam_uk()
    mesh.point_data["pids"] = np.arange(mesh.n_points)
    mesh.cell_data["cids"] = np.arange(mesh.n_cells)
    mesh.set_active_scalars("cids")
    return mesh


@pytest.fixture(scope="session")
def lam_uk_cloud(lam_uk_sample):
    """Fixture generates a Local Area Model point-cloud for the UK."""
    lons, lats = lam_uk_sample

    return Transform.from_points(lons, lats)


@pytest.fixture(scope="session")
def lam_uk_sample():
    """Fixture generates a Local Area Model data sample for the UK."""
    sample = pantry_lam_uk()
    return sample.lons[:], sample.lats[:]


@pytest.fixture
def lfric(request):
    """Fixture to provide a cube-sphere mesh."""
    # support indirect parameters for fixtures and also
    # calling the fixture with no parameter
    resolution = request.param if hasattr(request, "param") else "c48"

    return sample_lfric(resolution=resolution)


@pytest.fixture
def lfric_sst():
    """Fixture to provide a cube-sphere mesh with SST face data."""
    mesh = sample_lfric_sst()
    name = mesh.active_scalars_name
    mesh["cids"] = np.arange(mesh.n_cells)
    mesh["pids"] = np.arange(mesh.n_points)
    mesh.set_active_scalars(name)
    return mesh


@pytest.fixture
def lfric_sst_eqc():
    """Fixture to provide an eqc cube-sphere mesh with SST face data."""
    mesh = sample_lfric_sst()
    name = mesh.active_scalars_name
    mesh["cids"] = np.arange(mesh.n_cells)
    mesh["pids"] = np.arange(mesh.n_points)
    mesh = transform_mesh(mesh, tgt_crs="+proj=eqc")
    mesh.set_active_scalars(name)
    return mesh


@pytest.fixture
def in_radians():
    """Fixture to declare the geographic axes of a CRS in radians.

    ``pyproj`` gives and takes the coordinates of a geographic CRS declared in
    radians in degrees, as it does those declared in degrees, whereas it gives and
    takes those of a CRS in any other angular unit, such as grads, in that unit.

    """

    def declare(crs: str) -> pyproj.CRS:
        spec = pyproj.CRS.from_user_input(crs).to_json_dict()
        spec.pop("id", None)
        # a projected CRS declares its geographic axes in its base CRS
        geographic = spec.get("base_crs", spec)
        geographic.pop("id", None)
        for axis in geographic["coordinate_system"]["axis"]:
            axis["unit"] = {
                "type": "AngularUnit",
                "name": "radian",
                "conversion_factor": 1.0,
            }
        return pyproj.CRS.from_json_dict(spec)

    return declare


@pytest.fixture
def no_network():
    """Fixture to turn off PROJ's network access, as pyproj's wheels ship it.

    A conda environment turns it on, and PROJ then fetches any grid it lacks. A
    wheel leaves it off, and an operation whose grid is not installed is then
    unavailable.

    """
    enabled = pyproj.network.is_network_enabled()
    pyproj.network.set_network_enabled(False)
    yield
    pyproj.network.set_network_enabled(enabled)


@pytest.fixture
def sphere():
    """Fixture to provide a pyvista sphere mesh."""
    return pv.Sphere()


@pytest.fixture
def wgs84_wkt():
    """Fixture for generating WG284 CRS WKT as a string."""
    return WGS84.to_wkt()


def _legacy(mesh: pv.DataSet, /, *, radius: float | None = None) -> pv.DataSet:
    """Return a copy of the mesh as geovista 0.5 wrote it.

    The copy has no globe, and a ``gvRadius`` of `radius`, else of the render
    radius the mesh records.

    """
    if radius is None:
        globe = Globe.from_mesh(mesh)
        assert globe is not None, "the mesh records no globe to write as gvRadius"
        radius = globe.render_radius
    result = mesh.copy()
    for name in _GV_GLOBE_FIELDS:
        result.field_data.pop(name, None)
    result.field_data[GV_FIELD_RADIUS] = np.array([float(radius)])
    return result


@pytest.fixture
def legacy() -> Callable[..., pv.DataSet]:
    """Fixture to build a mesh as geovista 0.5 wrote it, for tests of retired fields."""
    return _legacy


def _at_heights(
    lons: ArrayLike, lats: ArrayLike, heights: ArrayLike, globe: Globe
) -> np.ndarray:
    """Return the points at their heights on a globe, worked out with numpy alone.

    The reference of heights spec §4.3, from the globe's public values: a point
    lies at a radius of ``s (R + V(h))``, where ``V`` exaggerates a height above
    sea level and one below it by their own factors, and a missing height is 0.

    """
    lons = np.radians(np.ravel(np.asarray(lons, dtype=np.float64)))
    lats = np.radians(np.ravel(np.asarray(lats, dtype=np.float64)))
    heights = np.ravel(np.asarray(heights, dtype=np.float64))
    mapped = np.where(
        heights >= 0,
        globe.exaggeration * heights,
        globe.exaggeration_below * heights,
    )
    mapped = np.where(np.isnan(heights), 0.0, mapped)
    radius = globe.radius.m_as("m")
    radii = globe.render_radius * (1.0 + mapped / radius)
    return np.column_stack(
        [
            radii * np.cos(lats) * np.cos(lons),
            radii * np.cos(lats) * np.sin(lons),
            radii * np.sin(lats),
        ]
    )


@pytest.fixture
def at_heights() -> Callable[..., np.ndarray]:
    """Fixture to place points at their heights on a globe, for reference."""
    return _at_heights
