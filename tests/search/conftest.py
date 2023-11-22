"""pytest fixture infra-structure for :mod:`geovista.search` unit-tests."""
from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable


class Center(NamedTuple):
    """Define cell and associated vertices."""

    cid: int
    pids: Iterable[int]


class Neighbour(NamedTuple):
    """Define cell and associated neighbouring cells."""

    cid: int
    expected: Iterable[int]


class POI(NamedTuple):
    """Define cell and named geolocated point-of-interest."""

    name: str
    lon: float
    lat: float
    cid: int


class Vertex(NamedTuple):
    """Define vertex and parent cell/s."""

    pid: int
    cids: Iterable[int]


@pytest.fixture(
    params=[
        Center(cid=0, pids=[0, 1, 2, 3]),
        Center(cid=1, pids=[1, 2, 4, 5]),
        Center(cid=2, pids=[4, 5, 6, 7]),
        Center(cid=3, pids=[6, 7, 8, 9]),
        Center(cid=4, pids=[0, 1, 10, 11]),
        Center(cid=5, pids=[1, 4, 11, 12]),
        Center(cid=6, pids=[4, 6, 12, 13]),
        Center(cid=7, pids=[6, 8, 13, 14]),
        Center(cid=8, pids=[10, 11, 15, 16]),
        Center(cid=9, pids=[11, 12, 16, 17]),
        Center(cid=10, pids=[12, 13, 17, 18]),
        Center(cid=11, pids=[13, 14, 18, 19]),
        Center(cid=12, pids=[15, 16, 20, 21]),
        Center(cid=13, pids=[16, 17, 21, 22]),
        Center(cid=14, pids=[17, 18, 22, 23]),
        Center(cid=15, pids=[18, 19, 23, 24]),
    ]
)
def center(request):
    """Fixutre enumerates the lam_uk point-IDs associated with the cell-ID."""
    return request.param


@pytest.fixture(
    params=[
        Vertex(pid=0, cids=[0, 4]),
        Vertex(pid=1, cids=[0, 1, 4, 5]),
        Vertex(pid=2, cids=[0, 1]),
        Vertex(pid=3, cids=[0]),
        Vertex(pid=4, cids=[1, 2, 5, 6]),
        Vertex(pid=5, cids=[1, 2]),
        Vertex(pid=6, cids=[2, 3, 6, 7]),
        Vertex(pid=7, cids=[2, 3]),
        Vertex(pid=8, cids=[3, 7]),
        Vertex(pid=9, cids=[3]),
        Vertex(pid=10, cids=[4, 8]),
        Vertex(pid=11, cids=[4, 5, 8, 9]),
        Vertex(pid=12, cids=[5, 6, 9, 10]),
        Vertex(pid=13, cids=[6, 7, 10, 11]),
        Vertex(pid=14, cids=[7, 11]),
        Vertex(pid=15, cids=[8, 12]),
        Vertex(pid=16, cids=[8, 9, 12, 13]),
        Vertex(pid=17, cids=[9, 10, 13, 14]),
        Vertex(pid=18, cids=[10, 11, 14, 15]),
        Vertex(pid=19, cids=[11, 15]),
        Vertex(pid=20, cids=[12]),
        Vertex(pid=21, cids=[12, 13]),
        Vertex(pid=22, cids=[13, 14]),
        Vertex(pid=23, cids=[14, 15]),
        Vertex(pid=24, cids=[15]),
    ]
)
def vertex(request):
    """Fixture enumerates the lam_uk cell-IDs associated with the point-ID."""
    return request.param


@pytest.fixture(
    params=[
        Vertex(pid=3, cids=0),
        Vertex(pid=9, cids=3),
        Vertex(pid=20, cids=12),
        Vertex(pid=24, cids=15),
    ]
)
def vertex_corner(request):
    """Fixture enumerates the single lam_uk cell-ID for the corner point-ID (pid)."""
    return request.param


@pytest.fixture(
    params=[
        POI(name="portree", lon=-6.1960, lat=57.4125, cid=0),
        POI(name="aberdeen", lon=-2.0938, lat=57.1499, cid=1),
        POI(name="oslo", lon=10.7522, lat=59.9139, cid=2),
        POI(name="visby", lon=18.2948, lat=57.6348, cid=3),
        POI(name="dublin", lon=-6.2603, lat=53.3498, cid=4),
        POI(name="edinburgh", lon=-3.1883, lat=55.9533, cid=5),
        POI(name="amsterdam", lon=4.9041, lat=52.3676, cid=6),
        POI(name="berlin", lon=13.4050, lat=52.5200, cid=7),
        POI(name="plymouth", lon=-4.1427, lat=50.3755, cid=8),
        POI(name="st helier", lon=-2.1032, lat=49.1805, cid=9),
        POI(name="strasbourg", lon=7.7521, lat=48.5734, cid=10),
        POI(name="graz", lon=15.4395, lat=47.0707, cid=11),
        POI(name="santander", lon=-3.8226, lat=43.4636, cid=12),
        POI(name="toulouse", lon=1.4442, lat=43.6047, cid=13),
        POI(name="genoa", lon=8.9463, lat=44.4056, cid=14),
        POI(name="pula", lon=13.8496, lat=44.8666, cid=15),
    ]
)
def poi(request):
    """Fixture gives the lam_uk cell-ID (cid) containing the point-of-interest (POI)."""
    return request.param


@pytest.fixture(
    params=[
        Neighbour(cid=0, expected=[1, 4, 5]),
        Neighbour(cid=1, expected=[0, 2, 4, 5, 6]),
        Neighbour(cid=2, expected=[1, 3, 5, 6, 7]),
        Neighbour(cid=3, expected=[2, 6, 7]),
        Neighbour(cid=4, expected=[0, 1, 5, 8, 9]),
        Neighbour(cid=5, expected=[0, 1, 2, 4, 6, 8, 9, 10]),
        Neighbour(cid=6, expected=[1, 2, 3, 5, 7, 9, 10, 11]),
        Neighbour(cid=7, expected=[2, 3, 6, 10, 11]),
        Neighbour(cid=8, expected=[4, 5, 9, 12, 13]),
        Neighbour(cid=9, expected=[4, 5, 6, 8, 10, 12, 13, 14]),
        Neighbour(cid=10, expected=[5, 6, 7, 9, 11, 13, 14, 15]),
        Neighbour(cid=11, expected=[6, 7, 10, 14, 15]),
        Neighbour(cid=12, expected=[8, 9, 13]),
        Neighbour(cid=13, expected=[8, 9, 10, 12, 14]),
        Neighbour(cid=14, expected=[9, 10, 11, 13, 15]),
        Neighbour(cid=15, expected=[10, 11, 14]),
    ]
)
def neighbours(request):
    """Fixture enumerates the expected neighbouring cell-IDs of the given cell-ID."""
    return request.param
