"""pytest infra-structure for :mod:`geovista.geodesic` unit-tests."""
import pytest

from geovista.samples import lfric_sst as sample_lfric_sst


@pytest.fixture
def lfric_sst():
    """Fixture to provide a cube-sphere mesh."""
    mesh = sample_lfric_sst()
    return mesh
