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

from .common import (
    BASE,
    CENTRAL_MERIDIAN,
    GV_REMESH_POINT_IDS,
    PERIOD,
    REMESH_SEAM,
    to_cartesian,
    wrap,
)
from .crs import WGS84, to_wkt

__all__ = [
    "GRATICULE_CLOSED_INTERVAL",
    "GRATICULE_ZLEVEL",
    "GraticuleGrid",
    "create_meridians",
    "create_parallels",
]

#: Whether longitudes within half-open [-180, 180) or closed [-180, 180] interval.
GRATICULE_CLOSED_INTERVAL: bool = False

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
LATITUDE_POLES_PARALLEL: bool = False

#: Whether to generate a north/south pole label.
LATITUDE_POLES_LABEL: bool = True

#: The first graticule line of latitude (degrees).
LATITUDE_START: float = -90.0

#: The default step size between graticule parallels (degrees).
LATITUDE_STEP: float = 30.0

#: The period or upper bound (degrees) for parallel step size.
LATITUDE_STEP_PERIOD: float = 90.0

#: The last graticule line of latitude (degrees).
LATITUDE_STOP: float = 90.0

# The default number of points in a meridian line.
LONGITUDE_N_SAMPLES: int = 180

#: The first meridian line in the graticule (degrees).
LONGITUDE_START: float = BASE

#: The default step size between graticule meridians (degrees).
LONGITUDE_STEP: float = 45.0

#: The period or upper bound (degrees) for meridian step size.
LONGITUDE_STEP_PERIOD: float = 180.0

#: The last graticule meridian (degrees).
LONGITUDE_STOP: float = BASE + PERIOD


@dataclass
class GraticuleGrid:
    """Graticule composed of a block of meshes, labels and their points.

    Notes
    -----
    .. versionadded:: 0.3.0

    """

    blocks: pv.MultiBlock
    lonlat: ArrayLike
    labels: list[str]
    mask: ArrayLike = None


def _step_period(lon: float, lat: float) -> tuple[float, float]:
    """Wrap graticule meridian/parallel step size (degrees) to sane upper bounds.

    Parameters
    ----------
    lon : float
        The longitude step (degrees) between meridians.
    lat : float
        The latitude step (degrees) between parallels.

    Returns
    -------
    tuple of float
        The lon/lat step values within the period.

    Notes
    -----
    .. versionadded:: 0.3.0

    """
    lon_sign = 1 if lon >= 0 else -1
    lat_sign = 1 if lat >= 0 else -1
    lon = (lon % LONGITUDE_STEP_PERIOD) * lon_sign
    lat = (lat % LATITUDE_STEP_PERIOD) * lat_sign
    if np.isclose(lon, 0):
        lon = abs(lon)
    if np.isclose(lat, 0):
        lat = abs(lat)
    return (lon, lat)


def create_meridian_labels(lons: list[float]) -> list[str]:
    """Generate labels for the meridians.

    Parameters
    ----------
    lons : list of float
        The meridian lines that require a label of their location east or west relative
        to the prime meridian.

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

    for lon in lons:
        # explicit truncation, perhaps offer format control when required
        lon = int(lon)
        direction = LABEL_EAST

        if lon == 0 or np.isclose(np.abs(lon), 180):
            direction = LABEL_DEGREE
        elif lon < 0:
            direction = LABEL_WEST

        value = np.abs(lon)
        result.append(f"{value}{direction}")

    return result


def create_meridians(
    start: float | None = None,
    stop: float | None = None,
    step: float | None = None,
    lat_step: float | None = None,
    n_samples: int | None = None,
    closed_interval: bool | None = None,
    central_meridian: float | None = None,
    radius: float | None = None,
    zlevel: int | None = None,
    zscale: float | None = None,
) -> GraticuleGrid:
    """Generate graticule lines of constant longitude (meridians) with labels.

    Parameters
    ----------
    start : float, optional
        The first line of longitude (degrees). The graticule will include this
        meridian. Defaults to :data:`LONGITUDE_START`.
    stop : float, optional
        The last line of longitude (degrees). The graticule will include this meridian
        when it is a multiple of ``step``. Also see ``closed_interval``. Defaults to
        :data:`LONGITUDE_STOP`.
    step : float, optional
        The delta (degrees) between neighbouring meridians. Defaults to
        :data:`LONGITUDE_STEP`.
    lat_step : float, optional
        The delta (degrees) between neighbouring parallels. Defaults to
        :data:`LATITUDE_STEP`.
    n_samples : int, optional
        The number of points in a single line of longitude. Defaults to
        :data:`LONGITUDE_N_SAMPLES`.
    closed_interval : bool, default=False
        Longitude values will be in the half-closed interval [-180, 180). Otherwise,
        longitudes will be in the closed interval [-180, 180]. Defaults to
        :data:`GRATICULE_CLOSED_INTERVAL`.
    central_meridian : float, optional
        The central meridian of the longitude range. Defaults to
        :data:`geovista.common.CENTRAL_MERIDIAN`.
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

    if lon_step <= 0:
        emsg = f"Require a non-zero positive value for 'step', got {str(lon_step)!r}."
        raise ValueError(emsg)

    if n_samples is None:
        n_samples = LONGITUDE_N_SAMPLES

    if lat_step is None:
        lat_step = LATITUDE_STEP

    if lat_step <= 0:
        emsg = (
            f"Require a non-zero positive value for 'lat_step', got {str(lat_step)!r}."
        )
        raise ValueError(emsg)

    if closed_interval is None:
        closed_interval = GRATICULE_CLOSED_INTERVAL

    if central_meridian is None:
        central_meridian = CENTRAL_MERIDIAN

    if zlevel is None:
        zlevel = GRATICULE_ZLEVEL

    # period sanity for step sizes
    lon_step, lat_step = _step_period(lon_step, lat_step)

    lons = np.arange(start, stop + lon_step, lon_step, dtype=float)

    if closed_interval:
        boundary = wrap(central_meridian - BASE)
        lons = wrap(lons + central_meridian)
        mask = np.isclose(lons, boundary)
        idxs = np.where(mask)[0]
        if idxs.size:
            mask[idxs[0]] = False
    else:
        mask = None
        lons = np.unique(wrap(lons))

    lats = np.linspace(LATITUDE_START, LATITUDE_STOP, num=n_samples)
    blocks = pv.MultiBlock()

    for index, lon in enumerate(lons):
        xyz = to_cartesian(
            np.ones_like(lats) * lon,
            lats,
            radius=radius,
            zlevel=zlevel,
            zscale=zscale,
        )
        # a meridian with N points has N-1 lines
        n_points = xyz.shape[0] - 1
        lines = np.full((n_points, 3), 2, dtype=int)
        lines[:, 1] = np.arange(n_points)
        lines[:, 2] = np.arange(n_points) + 1

        mesh = pv.PolyData(xyz, lines=lines, n_lines=n_points)
        to_wkt(mesh, WGS84)

        if closed_interval and mask[index]:
            # mark this meridian as the closed interval wrap
            seam = np.empty(mesh.n_points, dtype=int)
            seam.fill(REMESH_SEAM)
            mesh.point_data[GV_REMESH_POINT_IDS] = seam
            mesh.set_active_scalars(name=None)

        blocks[f"{index},{str(lon)}"] = mesh

    grid_points, grid_labels = [], []
    labels = create_meridian_labels(list(lons))
    grid_lats = np.arange(LATITUDE_START, LATITUDE_STOP, lat_step, dtype=float) + (
        lat_step / 2
    )

    for lat in grid_lats:
        lonlat = np.vstack([lons, np.ones_like(lons, dtype=float) * lat]).T
        grid_points.append(lonlat)
        grid_labels.extend(labels)

    grid_points = np.vstack(grid_points)

    if mask is not None:
        mask = np.tile(mask, grid_lats.size)

    graticule = GraticuleGrid(
        blocks=blocks, lonlat=grid_points, labels=grid_labels, mask=mask
    )

    return graticule


def create_parallel_labels(
    lats: list[float], poles_parallel: bool | None = None
) -> list[str]:
    """Generate labels for the parallels.

    Parameters
    ----------
    lats : list of float
        The lines of latitude that require a label of their location north or
        south relative to the equator.
    poles_parallel : bool, optional
        Whether to generate a label for the north/south poles. Defaults to
        :data:`LATITUDE_POLES_PARALLEL`.

    Returns
    -------
    list of str
        The sequence of string labels for each line of latitude.

    Notes
    -----
    .. versionadded:: 0.3.0

    """
    result = []

    if poles_parallel is None:
        poles_parallel = LATITUDE_POLES_PARALLEL

    if not isinstance(lats, Iterable):
        lats = [lats]

    for lat in lats:
        # explicit truncation, perhaps offer format control when required
        lat = int(lat)
        direction = LABEL_NORTH

        if lat == 0:
            direction = LABEL_DEGREE
        elif lat < 0:
            direction = LABEL_SOUTH

        if not poles_parallel and np.isclose(np.abs(lat), 90):
            continue

        value = np.abs(lat)
        result.append(f"{value}{direction}")

    return result


def create_parallels(
    start: float | None = None,
    stop: float | None = None,
    step: float | None = None,
    lon_step: float | None = None,
    n_samples: int | None = None,
    poles_parallel: bool | None = None,
    poles_label: bool | None = None,
    radius: float | None = None,
    zlevel: int | None = None,
    zscale: float | None = None,
) -> GraticuleGrid:
    """Generate graticule lines of constant latitude (parallels) with labels.

    Parameters
    ----------
    start : float, optional
        The first line of latitude (degrees). The graticule will include this
        parallel. Also see ``poles_parallel``. Defaults to :data:`LATITUDE_START`.
    stop : float, optional
        The last line of latitude (degrees). The graticule will include this parallel
        when it is a multiple of ``step``. Also see ``poles_parallel`. Defaults to
        :data:`LATITUDE_STOP`.
    step : float, optional
        The delta (degrees) between neighbouring parallels. Defaults to
        :data:`LATITUDE_STEP`.
    lon_step : float, optional
        The delta (degrees) between neighbouring meridians. Defaults to
        :data:`LONGITUDE_STEP`.
    n_samples : int, optional
        The number of points in a single line of latitude. Defaults to
        :data:`LATITUDE_N_SAMPLES`.
    poles_parallel : bool, optional
        Whether to create a line of latitude at the north/south poles. Also see
        ``poles_label``. Defaults to :data:`LATITUDE_POLES_PARALLEL`.
    poles_label : bool, optional
        Whether to create a single north/south pole label. Only applies when
        ``poles_parallel=False``. Defaults to :data:`LATITUDE_POLES_LABEL`.
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

    if lat_step <= 0:
        emsg = f"Require a non-zero positive value for 'step', got {str(lat_step)!r}."
        raise ValueError(emsg)

    if lon_step is None:
        lon_step = LONGITUDE_STEP

    if lon_step <= 0:
        emsg = (
            f"Require a non-zero positive value for 'lon_step', got {str(lon_step)!r}."
        )
        raise ValueError(emsg)

    if n_samples is None:
        n_samples = LATITUDE_N_SAMPLES

    if poles_parallel is None:
        poles_parallel = LATITUDE_POLES_PARALLEL

    if poles_label is None:
        poles_label = LATITUDE_POLES_LABEL

    if zlevel is None:
        zlevel = GRATICULE_ZLEVEL

    # period sanity for step sizes
    lon_step, lat_step = _step_period(lon_step, lat_step)

    lats = np.arange(start, stop + lat_step, lat_step, dtype=float)
    lons = wrap(np.linspace(LONGITUDE_START, LONGITUDE_STOP, num=n_samples + 1)[:-1])

    grid_lats = []
    blocks = pv.MultiBlock()

    for index, lat in enumerate(lats):
        if not poles_parallel and np.isclose(np.abs(lat), 90.0):
            continue

        xyz = to_cartesian(
            lons,
            np.ones_like(lons) * lat,
            radius=radius,
            zlevel=zlevel,
            zscale=zscale,
        )
        # a parallel is a closed loop with N points and N lines
        n_points = xyz.shape[0]
        lines = np.full((n_points, 3), 2, dtype=int)
        lines[:, 1] = np.arange(n_points)
        lines[:, 2] = np.arange(n_points) + 1
        lines[-1, 2] = 0

        mesh = pv.PolyData(xyz, lines=lines, n_lines=n_points)
        to_wkt(mesh, WGS84)
        blocks[f"{index},{str(lat)}"] = mesh
        grid_lats.append(lat)

    grid_points, grid_labels = [], []
    labels = create_parallel_labels(grid_lats, poles_parallel=poles_parallel)
    grid_lons = wrap(
        np.arange(LONGITUDE_START, LONGITUDE_STOP, lon_step, dtype=float)
        + (lon_step / 2)
    )

    for lon in grid_lons:
        lonlat = np.vstack([np.ones_like(grid_lats, dtype=float) * lon, grid_lats]).T
        grid_points.append(lonlat)
        grid_labels.extend(labels)

    if not poles_parallel and poles_label:
        lonlat = []
        if 90 in lats:
            lonlat.append([0, 90])
        if -90 in lats:
            lonlat.append([0, -90])
        if lonlat:
            lonlat = np.array(lonlat, dtype=float)
            grid_points.append(lonlat)
            pole_labels = create_parallel_labels(
                list(lonlat[:, 1]), poles_parallel=True
            )
            grid_labels.extend(pole_labels)

    grid_points = np.vstack(grid_points)
    graticule = GraticuleGrid(blocks=blocks, lonlat=grid_points, labels=grid_labels)

    return graticule
