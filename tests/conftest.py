"""pytest fixture infra-structure for :mod:`geovista.geodesic` unit-tests."""
from __future__ import annotations

import numpy as np
import pytest
import pyvista as pv

from geovista.bridge import Transform
from geovista.crs import WGS84
from geovista.geometry import coastlines as geometry_coastlines
from geovista.pantry import lam_uk as pantry_lam_uk
from geovista.samples import lam_uk as sample_lam_uk
from geovista.samples import lfric as sample_lfric
from geovista.samples import lfric_sst as sample_lfric_sst


@pytest.fixture()
def coastlines(request):
    """Fixture generates a coastlines line mesh."""
    # support indirect parameters for fixtures and also
    # calling the fixture with no parameter
    resolution = request.param if hasattr(request, "param") else "110m"

    return geometry_coastlines(resolution=resolution)


@pytest.fixture()
def lam_uk():
    """Fixture generates a Local Area Model mesh with indexed faces and points."""
    mesh = sample_lam_uk()
    mesh.cell_data["ids"] = np.arange(mesh.n_cells)
    mesh.point_data["ids"] = np.arange(mesh.n_points)
    return mesh


@pytest.fixture(scope="session")
def lam_uk_cloud(lam_uk_sample):
    """Fixture generates a Local Area Model point-could for the UK."""
    lons, lats = lam_uk_sample

    return Transform.from_points(lons, lats)


@pytest.fixture(scope="session")
def lam_uk_sample():
    """Fixture generates a Local Area Model data sample for the UK."""
    sample = pantry_lam_uk()
    return sample.lons[:], sample.lats[:]


@pytest.fixture()
def lfric(request):
    """Fixture to provide a cube-sphere mesh."""
    # support indirect parameters for fixtures and also
    # calling the fixture with no parameter
    resolution = request.param if hasattr(request, "param") else "c48"

    return sample_lfric(resolution=resolution)


@pytest.fixture(scope="session")
def lfric_sst():
    """Fixture to provide a cube-sphere mesh with SST face data."""
    mesh = sample_lfric_sst()
    name = mesh.active_scalars_name
    mesh["cids"] = np.arange(mesh.n_cells)
    mesh["pids"] = np.arange(mesh.n_points)
    mesh.set_active_scalars(name)
    return mesh


@pytest.fixture()
def sphere():
    """Fixture to provide a pyvista sphere mesh."""
    return pv.Sphere()


@pytest.fixture()
def wgs84_wkt():
    """Fixture for generating WG284 CRS WKT as a string."""
    return WGS84.to_wkt()
