"""Provides graticule support and other geographical lines of interest for geolocation.

Notes
-----
.. versionadded:: 0.3.0

"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike
import pyvista as pv

from .common import to_cartesian, wrap
from .crs import WGS84, to_wkt

__all__ = [
    "create_parallels",
]

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

#: Whether to generate a label for the equatorial parallel.
LATITUDE_LABEL_EQUATOR: bool = False

#: Whether to generate a label for the north/south poles.
LATITUDE_LABEL_POLES: bool = False

#: The first graticule line of latitude (degrees).
LATITUDE_START: float = -90.0

#: The default step size between graticule parallels (degrees).
LATITUDE_STEP: float = 30.0

#: The last graticule line of latitude (degrees).
LATITUDE_STOP: float = 90.0

# The default number of points in a meridian line.
LONGITUDE_N_SAMPLES: int = 180

#: The first meridian line in the graticule (degrees).
LONGITUDE_START: float = -180.0

#: The default step size between graticule meridians (degrees).
LONGITUDE_STEP: float = 30.0

#: The last graticule meridian (degrees).
LONGITUDE_STOP: float = 180.0


@dataclass
class GraticuleGrid:
    """Graticule grid composed of the grid mesh, labels and their points."""

    mesh: pv.PolyData
    points: ArrayLike  # geographical lon/lat
    labels: list[str, ...]


def create_parallel_labels(
    lats: list[float, ...], equator: bool | None = None, poles: bool | None = None
) -> list[str, ...]:
    """Generate labels for the parallels.

    Parameters
    ----------
    lats : list of float
        The lines of latitude that require a label of their location north or
        south of the prime meridian.
    equator : bool, optional
        Whether to generate a populated or empty label for the equatorial parallel.
        Defaults to :data:`LATITUDE_LABEL_EQUATOR`.
    poles : bool, optional
        Whether to generate a label for the north/south poles. Defaults to
        :data:`LATITUDE_LABEL_POLES`.

    Returns
    -------
    list of str
        The sequence of string labels for each line of latitude.

    Notes
    -----
    .. versionadded:: 0.3.0

    """
    result = []

    if equator is None:
        equator = LATITUDE_LABEL_EQUATOR

    if poles is None:
        poles = LATITUDE_LABEL_POLES

    for lat in lats:
        direction = ""
        if lat > 0:
            direction = LABEL_NORTH
        elif lat < 0:
            direction = LABEL_SOUTH
        elif lat == 0 and equator:
            direction = "°"

        if not poles and np.isclose(np.abs(lat), 90.0):
            continue

        value = int(abs(lat)) if direction else ""
        result.append(f"{value}{direction}")

    return result


def create_parallels(
    start: float | None = None,
    stop: float | None = None,
    step: float | None = None,
    n_samples: int | None = None,
    lon_step: float | None = None,
    equator: bool | None = None,
    poles: bool | None = None,
    radius: float | None = None,
    zlevel: float | ArrayLike | None = None,
    zscale: float | None = None,
    clean: bool | None = False,
) -> GraticuleGrid:
    """Generate graticule lines of latitude (parallels), with optional labels.

    Parameters
    ----------
    * labels (bool):
        Specify whether the graticule parallels are labelled. Default is ``True``.
    * n_samples (None or float):
        Specify the number of points contained within a graticule line of latitude.
        Default is ``LATITUDE_N_SAMPLES``.
    * step (None or float):
        Specify the increment (in degrees) step size from the equator to the poles,
        used to determine the graticule lines of latitude. The ``step`` is
        modulo ``90`` degrees. Default is ``DEFAULT_LATITUDE_STEP``.
    * lon_step (None or float):
        Specify the increment (in degrees) step size from the prime meridian eastwards,
        used to determine the longitude position of latitude labels. The ``lon_step`` is
        modulo ``180`` degrees. Default is ``DEFAULT_LONGITUDE_STEP``.
    * equator (bool):
        Specify whether equatorial labels are to be rendered. Default is ``False``.
    radius : float, optional
        The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
    zlevel : int, default=1
        The z-axis level. Used in combination with the `zscale` to offset the
        `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
    zscale : float, optional
        The proportional multiplier for z-axis `zlevel`. Defaults to
        :data:`geovista.common.ZLEVEL_SCALE`.

    Returns
    -------
    PolyData


    Notes
    -----
    .. versionadded:: 0.3.0

    """
    if start is None:
        start = LATITUDE_START

    if stop is None:
        stop = LATITUDE_STOP

    lat_step = LATITUDE_STEP if step is None else step

    if n_samples is None:
        n_samples = LATITUDE_N_SAMPLES

    if lon_step is None:
        lon_step = LONGITUDE_STEP

    if equator is None:
        equator = LATITUDE_LABEL_EQUATOR

    if poles is None:
        poles = LATITUDE_LABEL_POLES

    if zlevel is None:
        zlevel = 1

    # step modulo sanity
    lat_step %= 90.0
    lon_step %= 180.0

    lats = np.arange(start, stop + lat_step, lat_step, dtype=float)
    lons = wrap(np.linspace(-180.0, 180.0, num=n_samples + 1)[:-1])

    n_lines, n_segments = 0, 0
    lines, grid_lats, points = [], [], []

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
        points.append(xyz)
        line = np.full((n_points, 3), 2, dtype=int)
        line[:, 1] = np.arange(n_points) + n_segments
        line[:, 2] = np.arange(n_points) + n_segments + 1
        line[-1, 2] = n_segments
        lines.append(line)
        n_segments += n_points
        n_lines += 1
        grid_lats.append(lat)

    points = np.vstack(points)
    lines = np.vstack(lines)

    mesh = pv.PolyData(points, lines=lines, n_lines=n_lines)
    to_wkt(mesh, WGS84)

    grid_points, grid_labels = [], []
    labels = create_parallel_labels(grid_lats, equator=equator, poles=poles)
    grid_lons = np.arange(LONGITUDE_START, LONGITUDE_STOP, lon_step, dtype=float)

    for lon in grid_lons:
        lonlat = np.vstack([np.ones_like(grid_lats, dtype=float) * lon, grid_lats]).T
        grid_points.append(lonlat)
        grid_labels.extend(labels)

    if not poles:
        lonlat = np.array([[0, 90], [0, -90]], dtype=float)
        grid_points.append(lonlat)
        pole_labels = create_parallel_labels([90, -90], poles=True)
        grid_labels.extend(pole_labels)

    if clean:
        mesh.clean(inplace=True)

    grid_points = np.vstack(grid_points)
    graticule = GraticuleGrid(mesh=mesh, points=grid_points, labels=grid_labels)

    return graticule
