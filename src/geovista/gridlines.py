"""Provides graticule support and other geographical lines of interest for geolocation.

Notes
-----
.. versionadded:: 0.3.0

"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike
import pyvista as pv

from .common import to_cartesian, wrap
from .crs import WGS84, to_wkt

__all__ = [
    "create_meridians",
    "create_parallels",
]

#: The default zlevel for graticule meridians and parallels.
GRATICULE_ZLEVEL: int = 1

#: The degree symbol label.
LABEL_DEGREE: str = "°"

#: The east of the prime meridian label.
LABEL_EAST: str = f"{LABEL_DEGREE}E"

#: The north of the equatorial parallel label.
LABEL_NORTH: str = f"{LABEL_DEGREE}N"

#: The south of the equatorial parallel label.
LABEL_SOUTH: str = f"{LABEL_DEGREE}S"

#: The west of the prime meridian label.
LABEL_WEST: str = f"{LABEL_DEGREE}W"

#: The default number of points in a line of latitude.
LATITUDE_N_SAMPLES: int = 360

#: Whether to generate parallels at the north/south poles.
LATITUDE_POLES: bool = False

#: The first graticule line of latitude (degrees).
LATITUDE_START: float = -90.0

#: The default step size between graticule parallels (degrees).
LATITUDE_STEP: float = 30.0

#: The modulo upper bound (degrees) for parallel step size.
LATITUDE_STEP_MODULO: float = 90.0

#: The last graticule line of latitude (degrees).
LATITUDE_STOP: float = 90.0

# The default number of points in a meridian line.
LONGITUDE_N_SAMPLES: int = 180

#: The first meridian line in the graticule (degrees).
LONGITUDE_START: float = -180.0

#: The default step size between graticule meridians (degrees).
LONGITUDE_STEP: float = 30.0

#: The modulo upper bound (degrees) for meridian step size.
LONGITUDE_STEP_MODULO: float = 180.0

#: The last graticule meridian (degrees).
LONGITUDE_STOP: float = 180.0


@dataclass
class GraticuleGrid:
    """Graticule composed of the grid, labels and their points.

    Notes
    -----
    .. versionadded:: 0.3.0

    """

    blocks: pv.MultiBlock
    lonlat: ArrayLike
    labels: list[str, ...]


def create_meridian_labels(lons: list[float, ...]) -> list[str, ...]:
    """Generate labels for the meridians.

    Parameters
    ----------
    lons : list of float
        The meridian lines that require a label of their location east or west of
        the prime meridian.

    Returns
    -------
    list of str
        The sequence of string labels for each meridian line.

    Notes
    -----
    .. versionadded:: 0.3.0

    """
    result = []

    if not isinstance(lons, Iterable):
        lons = [lons]

    lons = wrap(lons)

    for lon in lons:
        direction = LABEL_EAST
        if lon == 0 or np.isclose(np.abs(lon), 180.0):
            direction = LABEL_DEGREE
        elif lon < 0:
            direction = LABEL_WEST

        value = int(np.abs(lon))
        result.append(f"{value}{direction}")

    return result


def create_parallel_labels(
    lats: list[float, ...], poles: bool | None = None
) -> list[str, ...]:
    """Generate labels for the parallels.

    Parameters
    ----------
    lats : list of float
        The lines of latitude that require a label of their location north or
        south of the prime meridian.
    poles : bool, optional
        Whether to generate a label for the north/south poles. Defaults to
        :data:`LATITUDE_POLES`.

    Returns
    -------
    list of str
        The sequence of string labels for each line of latitude.

    Notes
    -----
    .. versionadded:: 0.3.0

    """
    result = []

    if poles is None:
        poles = LATITUDE_POLES

    if not isinstance(lats, Iterable):
        lats = [lats]

    for lat in lats:
        direction = ""
        if lat > 0:
            direction = LABEL_NORTH
        elif lat < 0:
            direction = LABEL_SOUTH
        elif lat == 0:
            direction = LABEL_DEGREE

        if not poles and np.isclose(np.abs(lat), 90.0):
            continue

        value = int(np.abs(lat)) if direction else ""
        result.append(f"{value}{direction}")

    return result


def _step_modulo(lon_step: float, lat_step: float) -> tuple[float, float]:
    """Wrap graticule meridian/parallel step size (degrees) to sane upper bounds.

    Parameters
    ----------
    lon_step : float
        The longitude step (degrees) between meridians.
    lat_step : float
        The latitude step (degrees) between parallels.

    Returns
    -------
    tuple of float
        The lon/lat step values.

    Notes
    -----
    .. versionadded:: 0.3.0

    """
    return (lon_step % LONGITUDE_STEP_MODULO, lat_step % LATITUDE_STEP_MODULO)


def create_meridians(
    start: float | None = None,
    stop: float | None = None,
    step: float | None = None,
    lat_step: float | None = None,
    n_samples: int | None = None,
    radius: float | None = None,
    zlevel: float | ArrayLike | None = None,
    zscale: float | None = None,
) -> GraticuleGrid:
    """Generate graticule lines of constant longitude (meridians) with labels.

    Parameters
    ----------
    start : float, optional
        The starting line of longitude (degrees). The graticule will include this
        meridian. Defaults to :data:`LONGITUDE_START`.
    stop : float, optional
        The last line of longitude (degrees). The graticule will include this meridian
        when it is a multiple of ``step``. Defaults to :data:`LONGITUDE_STOP`.
    step : float, optional
        The delta (degrees) between neighbouring meridians. Defaults to
        :data:`LONGITUDE_STEP`.
    lat_step : float, optional
        The delta (degrees) between neighbouring parallels. Defaults to
        :data:`LATITUDE_STEP`.
    n_samples : int, optional
        The number of points in a single line of longitude. Defaults to
        :data:`LONGITUDE_N_SAMPLES`.
    radius : float, optional
        The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
    zlevel : int, optional
        The z-axis level. Used in combination with the `zscale` to offset the
        `radius` by a proportional amount i.e., ``radius * zlevel * zscale``. Defaults
        to :data:`GRATICULE_ZLEVEL`
    zscale : float, optional
        The proportional multiplier for z-axis `zlevel`. Defaults to
        :data:`geovista.common.ZLEVEL_SCALE`.

    Returns
    -------
    GraticuleGrid
        The graticule meridians and points with labels on those meridians.

    Notes
    -----
    .. versionadded:: 0.3.0

    """
    if start is None:
        start = LONGITUDE_START

    if stop is None:
        stop = LONGITUDE_STOP

    lon_step = LONGITUDE_STEP if step is None else step

    if n_samples is None:
        n_samples = LONGITUDE_N_SAMPLES

    if lat_step is None:
        lat_step = LATITUDE_STEP

    if zlevel is None:
        zlevel = GRATICULE_ZLEVEL

    # modulo sanity for step sizes
    lon_step, lat_step = _step_modulo(lon_step, lat_step)

    lons = np.unique(wrap(np.arange(start, stop + lon_step, lon_step, dtype=float)))
    lats = np.linspace(LATITUDE_START, LATITUDE_STOP, num=n_samples)

    grid_lons = []
    blocks = pv.MultiBlock()

    for lon in lons:
        xyz = to_cartesian(
            np.ones_like(lats) * lon,
            lats,
            radius=radius,
            zlevel=zlevel,
            zscale=zscale,
        )
        n_points = xyz.shape[0]
        lines = np.full((n_points, 3), 2, dtype=int)
        lines[:, 1] = np.arange(n_points)
        lines[:, 2] = np.arange(n_points) + 1

        mesh = pv.PolyData(xyz, lines=lines, n_lines=n_points)
        to_wkt(mesh, WGS84)
        blocks[str(lon)] = mesh
        grid_lons.append(lon)

    grid_points, grid_labels = [], []
    labels = create_meridian_labels(grid_lons)
    grid_lats = np.arange(LATITUDE_START, LATITUDE_STOP, lat_step, dtype=float) + (
        lat_step / 2
    )

    for lat in grid_lats:
        lonlat = np.vstack([grid_lons, np.ones_like(grid_lons, dtype=float) * lat]).T
        grid_points.append(lonlat)
        grid_labels.extend(labels)

    grid_points = np.vstack(grid_points)
    graticule = GraticuleGrid(blocks=blocks, lonlat=grid_points, labels=grid_labels)

    return graticule


def create_parallels(
    start: float | None = None,
    stop: float | None = None,
    step: float | None = None,
    lon_step: float | None = None,
    n_samples: int | None = None,
    poles: bool | None = None,
    radius: float | None = None,
    zlevel: float | ArrayLike | None = None,
    zscale: float | None = None,
) -> GraticuleGrid:
    """Generate graticule lines of constant latitude (parallels) with labels.

    Parameters
    ----------
    start : float, optional
        The starting line of latitude (degrees). The graticule will include this
        parallel. Defaults to :data:`LATITUDE_START`.
    stop : float, optional
        The last line of latitude (degrees). The graticule will include this parallel
        when it is a multiple of ``step``. Defaults to :data:`LATITUDE_STOP`.
    step : float, optional
        The delta (degrees) between neighbouring parallels. Defaults to
        :data:`LATITUDE_STEP`.
    lon_step : float, optional
        The delta (degrees) between neighbouring meridians. Defaults to
        :data:`LONGITUDE_STEP`.
    n_samples : int, optional
        The number of points in a single line of latitude. Defaults to
        :data:`LATITUDE_N_SAMPLES`.
    poles : bool, optional
        Whether to create a line of latitude at the north/south poles. Defaults to
        :data:`LATITUDE_POLES`.
    radius : float, optional
        The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
    zlevel : int, optional
        The z-axis level. Used in combination with the `zscale` to offset the
        `radius` by a proportional amount i.e., ``radius * zlevel * zscale``. Defaults
        to :data:`GRATICULE_ZLEVEL`
    zscale : float, optional
        The proportional multiplier for z-axis `zlevel`. Defaults to
        :data:`geovista.common.ZLEVEL_SCALE`.

    Returns
    -------
    GraticuleGrid
        The graticule parallels and points with labels on the parallels.

    Notes
    -----
    .. versionadded:: 0.3.0

    """
    if start is None:
        start = LATITUDE_START

    if stop is None:
        stop = LATITUDE_STOP

    lat_step = LATITUDE_STEP if step is None else step

    if lon_step is None:
        lon_step = LONGITUDE_STEP

    if n_samples is None:
        n_samples = LATITUDE_N_SAMPLES

    if poles is None:
        poles = LATITUDE_POLES

    if zlevel is None:
        zlevel = GRATICULE_ZLEVEL

    # modulo sanity for step sizes
    lon_step, lat_step = _step_modulo(lon_step, lat_step)

    lats = np.arange(start, stop + lat_step, lat_step, dtype=float)
    lons = wrap(np.linspace(LONGITUDE_START, LONGITUDE_STOP, num=n_samples + 1)[:-1])

    grid_lats = []
    blocks = pv.MultiBlock()

    for lat in lats:
        if not poles and np.isclose(np.abs(lat), 90.0):
            continue

        xyz = to_cartesian(
            lons,
            np.ones_like(lons) * lat,
            radius=radius,
            zlevel=zlevel,
            zscale=zscale,
        )
        n_points = xyz.shape[0]
        lines = np.full((n_points, 3), 2, dtype=int)
        lines[:, 1] = np.arange(n_points)
        lines[:, 2] = np.arange(n_points) + 1
        lines[-1, 2] = 0

        mesh = pv.PolyData(xyz, lines=lines, n_lines=n_points)
        to_wkt(mesh, WGS84)
        blocks[str(lat)] = mesh
        grid_lats.append(lat)

    grid_points, grid_labels = [], []
    labels = create_parallel_labels(grid_lats, poles=poles)
    grid_lons = wrap(
        np.arange(LONGITUDE_START, LONGITUDE_STOP, lon_step, dtype=float)
        + (lon_step / 2)
    )

    for lon in grid_lons:
        lonlat = np.vstack([np.ones_like(grid_lats, dtype=float) * lon, grid_lats]).T
        grid_points.append(lonlat)
        grid_labels.extend(labels)

    if not poles:
        # create pole labels at when there are no polar parallels
        lonlat = np.array([[0, 90], [0, -90]], dtype=float)
        grid_points.append(lonlat)
        pole_labels = create_parallel_labels([90, -90], poles=True)
        grid_labels.extend(pole_labels)

    grid_points = np.vstack(grid_points)
    graticule = GraticuleGrid(blocks=blocks, lonlat=grid_points, labels=grid_labels)

    return graticule
