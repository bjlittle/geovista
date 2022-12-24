"""
pytest infra-structure for :mod:`geovista.common` unit-tests.

"""
# pylint: disable=redefine-outer-name

from dataclasses import dataclass
from typing import Tuple, Union

import numpy as np
from numpy.typing import ArrayLike
import pytest

# typing alias
XYZLike = Union[Tuple[float, float, float], ArrayLike]
XYLike = Union[Tuple[float, float], ArrayLike]


@dataclass
class Convert:
    xyz: XYZLike
    expected: XYLike


values = [
    [(1.0, 0.0, 0.0), (0.0, 0.0)],
    [(np.sqrt(3), 1.0, 0.0), (30.0, 0.0)],
    [(1.0, 1.0, 0.0), (45.0, 0.0)],
    [(1.0, np.sqrt(3), 0.0), (60.0, 0.0)],
    [(0.0, 1.0, 0.0), (90.0, 0.0)],
    [(-1.0, np.sqrt(3), 0.0), (120.0, 0)],
    [(-1.0, 1.0, 0.0), (135.0, 0.0)],
    [(-np.sqrt(3), 1.0, 0.0), (150.0, 0.0)],
    [(-1, 0.0, 0.0), (-180.0, 0.0)],
    [(-np.sqrt(3), -1, 0.0), (-150.0, 0.0)],
    [(-1.0, -1.0, 0.0), (-135.0, 0.0)],
    [(-1.0, -np.sqrt(3), 0.0), (-120.0, 0.0)],
    [(0.0, -1.0, 0.0), (-90.0, 0.0)],
    [(1.0, -np.sqrt(3), 0.0), (-60.0, 0.0)],
    [(1.0, -1.0, 0.0), (-45.0, 0.0)],
    [(np.sqrt(3), -1.0, 0.0), (-30.0, 0.0)],
    [(np.sqrt(3) / 2, 0.0, 0.5), (0.0, 30.0)],
    [(1 / np.sqrt(2), 0.0, 1 / np.sqrt(2)), (0.0, 45.0)],
    [(0.5, 0.0, np.sqrt(3) / 2), (0.0, 60.0)],
    [(0.0, 0.0, 1.0), (0.0, 90.0)],
    [(np.sqrt(3) / 2, 0.0, -0.5), (0.0, -30.0)],
    [(1 / np.sqrt(2), 0.0, -1 / np.sqrt(2)), (0.0, -45.0)],
    [(0.5, 0.0, -np.sqrt(3) / 2), (0.0, -60.0)],
    [(0.0, 0.0, -1.0), (0, -90.0)],
]

params = [Convert(xyz, expected) for (xyz, expected) in values]
manyparams = [Convert(xyz, expected) for (xyz, expected) in [list(zip(*values))]]


@pytest.fixture(params=params)
def degrees(request):
    return request.param


@pytest.fixture
def radians(degrees):
    return Convert(degrees.xyz, np.radians(degrees.expected))


@pytest.fixture(params=manyparams)
def manydegrees(request):
    return request.param


@pytest.fixture
def manyradians(manydegrees):
    return Convert(manydegrees.xyz, np.radians(np.array(manydegrees.expected)))
