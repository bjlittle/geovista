# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Provide Natural Earth geometry support.

Notes
-----
.. versionadded:: 0.1.0

"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

import lazy_loader as lazy

from .common import (
    COASTLINES_RESOLUTION,
    GV_FIELD_RESOLUTION,
    LRU_CACHE_SIZE,
    ZLEVEL_SCALE,
    _to_cartesian,
)
from .core import resize
from .crs import WGS84, to_wkt
from .globe import _resolve
from .pantry import fetch_coastlines

if TYPE_CHECKING:
    from collections.abc import Iterable

    import numpy as np
    import pyvista as pv
    from shapely import LineString, MultiLineString

    from .globe import Globe

# lazy import third-party dependencies
cartopy = lazy.load("cartopy")
np = lazy.load("numpy")
pv = lazy.load("pyvista")
shapely = lazy.load("shapely")

__all__ = [
    "coastlines",
    "load_coastline_geometries",
    "load_coastlines",
]


@lru_cache(maxsize=LRU_CACHE_SIZE)
def coastlines(
    *,
    resolution: str | None = None,
    globe: Globe | None = None,
    zlevel: int | None = None,
    zscale: float | None = None,
) -> pv.PolyData:
    """Create or fetch the cached mesh of the coastlines.

    Parameters
    ----------
    resolution : str, optional
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m``, or ``10m``. Defaults to
        :data:`geovista.common.COASTLINES_RESOLUTION`.
    globe : :class:`~geovista.globe.Globe`, optional
        The globe the coastlines are drawn on, which they record. Defaults
        to ``Globe()``.
    zlevel : int, default=1
        The z-axis level. Used in combination with the `zscale` to offset the
        render radius by a proportional amount i.e.,
        ``render_radius * zlevel * zscale``.
    zscale : float, optional
        The proportional multiplier for z-axis `zlevel`. Defaults to
        :data:`geovista.common.ZLEVEL_SCALE`.

    Returns
    -------
    PolyData
        A mesh of the coastlines.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if resolution is None:
        resolution = COASTLINES_RESOLUTION

    if zlevel is None:
        zlevel = 1

    try:
        mesh = fetch_coastlines(resolution=resolution)
    except ValueError:
        mesh = load_coastlines(resolution=resolution)

    resize(mesh, globe=_resolve(globe), zlevel=zlevel, zscale=zscale, inplace=True)

    return mesh


@lru_cache(maxsize=LRU_CACHE_SIZE)
def load_coastline_geometries(*, resolution: str | None = None) -> list[np.ndarray]:
    """Download Natural Earth coastline shapefile for the required `resolution`.

    If the geometries are not already available within the cartopy cache, then
    they will be downloaded.

    The 2D longitude (``φ``) and latitude (``λ``) ``xy`` coastline geometries will be
    unpacked as 3D ``xy0`` coordinates i.e., ``φλ0``.

    Parameters
    ----------
    resolution : str, optional
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m`` or ``10m``. Defaults to
        :data:`geovista.common.COASTLINES_RESOLUTION`.

    Returns
    -------
    list of np.ndarray
        A list containing one or more coastline ``xy0`` geometries.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if resolution is None:
        resolution = COASTLINES_RESOLUTION

    lines, multi_lines = [], []
    category, name = "physical", "coastline"

    # load in the shapefiles
    fname = cartopy.io.shapereader.natural_earth(
        resolution=resolution, category=category, name=name
    )
    reader = cartopy.io.shapereader.Reader(fname)

    def unpack(
        geometries: Iterable[LineString | MultiLineString],
    ) -> None:
        """Unpack the geometries coordinates.

        Parameters
        ----------
        geometries : iterable of LineString or MultiLineString
            The geometries to unpack.

        """
        for geometry in geometries:
            if isinstance(geometry, shapely.MultiLineString):
                multi_lines.extend(list(geometry.geoms))
            else:
                xy = np.array(geometry.coords[:], dtype=np.float32)
                x = xy[:, 0].reshape(-1, 1)
                y = xy[:, 1].reshape(-1, 1)
                z = np.zeros_like(x)
                xyz = np.hstack((x, y, z))
                lines.append(xyz)

    unpack(reader.geometries())
    if multi_lines:
        unpack(multi_lines)

    return lines


@lru_cache(maxsize=LRU_CACHE_SIZE)
def load_coastlines(
    *,
    resolution: str | None = None,
    globe: Globe | None = None,
    zlevel: int | None = None,
    zscale: float | None = None,
) -> pv.PolyData:
    """Create a mesh of coastline geometries at the specified `resolution`.

    Parameters
    ----------
    resolution : str, optional
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m``, or ``10m``. Default to
        :data:`geovista.common.COASTLINES_RESOLUTION`.
    globe : :class:`~geovista.globe.Globe`, optional
        The globe the coastlines are drawn on, which they record. Defaults
        to ``Globe()``.
    zlevel : int, default=0
        The z-axis level. Used in combination with the `zscale` to offset the
        render radius by a proportional amount i.e.,
        ``render_radius * zlevel * zscale``.
    zscale : float, optional
        The proportional multiplier for z-axis `zlevel`. Defaults to
        :data:`geovista.common.ZLEVEL_SCALE`.

    Returns
    -------
    PolyData
        A mesh of the coastlines.

    Notes
    -----
    .. versionadded:: 0.1.0

    Calls :func:`load_coastline_geometries` to download the original coastline
    geometries.

    """
    if resolution is None:
        resolution = COASTLINES_RESOLUTION

    globe = _resolve(globe)
    zscale = ZLEVEL_SCALE if zscale is None else float(zscale)
    zlevel = 0 if zlevel is None else int(zlevel)

    geoms_list = load_coastline_geometries(resolution=resolution)
    npoints_per_geom = [geom.shape[0] for geom in geoms_list]
    ngeoms = len(geoms_list)
    geoms = np.concatenate(geoms_list)
    nlines = geoms.shape[0] - ngeoms

    # lifted from the render radius by the z-level, which the globe never includes
    geoms = _to_cartesian(
        geoms[:, 0],
        geoms[:, 1],
        radius=globe.render_radius,
        zlevel=zlevel,
        zscale=zscale,
    )

    # convert geometries to a vtk line mesh
    mesh = pv.PolyData()
    mesh.points = geoms
    lines = np.full((nlines, 3), 2, dtype=int)
    pstart, lstart = 0, 0

    for npoints in npoints_per_geom:
        pend = pstart + npoints
        lend = lstart + npoints - 1
        lines[lstart:lend, 1] = np.arange(pstart, pend - 1, dtype=int)
        lines[lstart:lend, 2] = np.arange(pstart + 1, pend, dtype=int)
        pstart, lstart = pend, lend

    mesh.lines = lines
    globe.to_mesh(mesh)
    mesh.field_data[GV_FIELD_RESOLUTION] = np.array([resolution])
    to_wkt(mesh, WGS84)

    return mesh
