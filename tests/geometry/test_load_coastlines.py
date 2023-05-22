"""Unit-test for :func:`geovista.geometry.load_coastlines`."""
import numpy as np
import pytest

from geovista.common import (
    GV_FIELD_RADIUS,
    GV_FIELD_RESOLUTION,
    RADIUS,
    ZLEVEL_FACTOR,
    distance,
)
from geovista.geometry import COASTLINE_RESOLUTION
from geovista.geometry import load_coastlines as load


def test_defaults():
    """Test expected defaults are honoured."""
    result = load()
    assert result[GV_FIELD_RADIUS] == RADIUS
    assert result[GV_FIELD_RESOLUTION] == COASTLINE_RESOLUTION


def test_resolution_metadata(resolution):
    """Test field data contains the correct resolution metadata."""
    result = load(resolution=resolution)
    assert result[GV_FIELD_RESOLUTION][0] == resolution


def test_lines(resolution):
    """Test coastline mesh consists of lines."""
    result = load(resolution=resolution)
    assert result.n_cells == result.n_lines


@pytest.mark.parametrize("radius", np.linspace(0.5, 1.5, num=5))
def test_radius(resolution, radius):
    """Test coastline z-control with radius."""
    result = load(resolution=resolution, radius=radius)
    actual = distance(result)
    assert np.isclose(actual, radius)


@pytest.mark.parametrize("zlevel", range(-10, 11))
def test_zlevel(resolution, zlevel):
    """Test coastline z-control with zlevel."""
    result = load(resolution=resolution, zlevel=zlevel)
    actual = distance(result)
    expected = RADIUS + RADIUS * zlevel * ZLEVEL_FACTOR
    assert np.isclose(actual, expected)


@pytest.mark.parametrize("zfactor", np.linspace(-1, 1, num=5))
def test_zfactor(resolution, zfactor):
    """Test coastline z-control with zfactor with no zlevel."""
    result = load(resolution=resolution, zfactor=zfactor)
    actual = distance(result)
    assert np.isclose(actual, RADIUS)


@pytest.mark.parametrize("zfactor", np.linspace(-1, 1, num=5))
def test_zfactor__with_zlevel(resolution, zfactor):
    """Test coastline z-control with zfactor and zlevel."""
    result = load(resolution=resolution, zlevel=1, zfactor=zfactor)
    actual = distance(result)
    expected = RADIUS + RADIUS * zfactor
    assert np.isclose(actual, expected)
