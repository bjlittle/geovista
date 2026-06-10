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
    GV_FIELD_RADIUS,
    GV_FIELD_RESOLUTION,
    LRU_CACHE_SIZE,
    RADIUS,
    ZLEVEL_SCALE,
    to_cartesian,
)
from .core import resize
from .crs import WGS84, to_wkt
from .pantry import fetch_coastlines

if TYPE_CHECKING:
    from collections.abc import Generator

    import numpy as np
    import pyvista as pv
    from shapely import LineString, MultiLineString
    from shapely.geometry.base import GeometrySequence

# lazy import third-party dependencies
cartopy = lazy.load("cartopy")
np = lazy.load("numpy")
pv = lazy.load("pyvista")
shapely = lazy.load("shapely")

__all__ = [
    "coastlines",
    "load_coastline_geometries",
    "load_coastlines",
    "load_natural_earth_feature",
    "load_natural_earth_geometries",
]


@lru_cache(maxsize=LRU_CACHE_SIZE)
def coastlines(
    *,
    resolution: str | None = None,
    radius: float | None = None,
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

    resize(mesh, radius=radius, zlevel=zlevel, zscale=zscale, inplace=True)

    return mesh


@lru_cache(maxsize=LRU_CACHE_SIZE)
def load_natural_earth_geometries(
    category: str,
    name: str,
    resolution: str | None = None,
) -> list[np.ndarray]:
    """Download Natural Earth shapefile for the required `resolution`.

    Generic routine for downloading natural earth "Line" features, such
    as coastlines, borders, etc.

    If the geometries are not already available within the cartopy cache, then
    they will be downloaded.

    The 2-D longitude (``φ``) and latitude (``λ``) ``xy`` coastline geometries will be
    unpacked as 3-D ``xy0`` coordinates i.e., ``φλ0``.

    Parameters
    ----------
    category : str
        The Natural Earth category of the feature.
    name : str
        The name of the Natural Earth feature.
    resolution : str, optional
        The resolution of the Natural Earth feature, which may be either
        ``110m``, ``50m`` or ``10m`` (defaults to "110m").

    Returns
    -------
    list of np.ndarray
        A list containing one or more ``xy0`` geometries.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    import cartopy.io.shapereader as shp
    from shapely import LineString, MultiLineString, MultiPolygon, Polygon

    if resolution is None:
        resolution = "110m"  # TODO(chris): Better default

    lines, multi_lines = [], []

    # load in the shapefiles
    fname = shp.natural_earth(resolution=resolution, category=category, name=name)
    reader = shp.Reader(fname)

    def unpack(
        geometries: Generator[LineString | MultiLineString | MultiPolygon],
    ) -> None:
        """Unpack the geometries coordinates.

        Parameters
        ----------
        geometries : Generator of LineString or MultiLineString
            The geometries to unpack.

        """
        for geometry in geometries:
            if isinstance(geometry, MultiLineString | MultiPolygon):
                multi_lines.extend(list(geometry.geoms))
            else:
                if isinstance(geometry, Polygon):
                    xy = np.array(geometry.exterior.coords[:], dtype=np.float32)
                elif isinstance(geometry, LineString):
                    xy = np.array(geometry.coords[:], dtype=np.float32)
                else:
                    msg = f"Unsupported geometry type: {type(geometry)}"
                    raise ValueError(msg)  # noqa: TRY004
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
def load_natural_earth_geometries(
    category: str,
    name: str,
    resolution: str | None = None,
) -> list[np.ndarray]:
    """Download Natural Earth shapefile for the required `resolution`.

    Generic routine for downloading natural earth "Line" features, such
    as coastlines, borders, etc.

    If the geometries are not already available within the cartopy cache, then
    they will be downloaded.

    The 2-D longitude (``φ``) and latitude (``λ``) ``xy`` coastline geometries will be
    unpacked as 3-D ``xy0`` coordinates i.e., ``φλ0``.

    Parameters
    ----------
    category : str
        The Natural Earth category of the feature.
    name : str
        The name of the Natural Earth feature.
    resolution : str, optional
        The resolution of the Natural Earth feature, which may be either
        ``110m``, ``50m`` or ``10m`` (defaults to "110m").

    Returns
    -------
    list of np.ndarray
        A list containing one or more ``xy0`` geometries.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    import cartopy.io.shapereader as shp
    from shapely import LineString, MultiLineString, MultiPolygon, Polygon

    if resolution is None:
        resolution = "110m"  # TODO(chris): Better default

    lines, multi_lines = [], []

    # load in the shapefiles
    fname = shp.natural_earth(resolution=resolution, category=category, name=name)
    reader = shp.Reader(fname)

    def unpack(
        geometries: Generator[LineString | MultiLineString | MultiPolygon],
    ) -> None:
        """Unpack the geometries coordinates.

        Parameters
        ----------
        geometries : Generator of LineString or MultiLineString
            The geometries to unpack.

        """
        for geometry in geometries:
            if isinstance(geometry, MultiLineString | MultiPolygon):
                multi_lines.extend(list(geometry.geoms))
            else:
                if isinstance(geometry, Polygon):
                    xy = np.array(geometry.exterior.coords[:], dtype=np.float32)
                elif isinstance(geometry, LineString):
                    xy = np.array(geometry.coords[:], dtype=np.float32)
                else:
                    msg = f"Unsupported geometry type: {type(geometry)}"
                    raise ValueError(msg)  # noqa: TRY004
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
    Wrapper around :func:`load_natural_earth_geometries`:
        load_natural_earth_geometries("physical", "coastline", resolution)

    .. versionadded:: 0.1.0

    """
    return load_natural_earth_geometries("physical", "coastline", resolution)


@lru_cache(maxsize=LRU_CACHE_SIZE)
def load_coastlines(
    *,
    resolution: str | None = None,
    radius: float | None = None,
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
    radius : float, optional
        The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
    zlevel : int, default=0
        The z-axis level. Used in combination with the `zscale` to offset the
        `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
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

    Calls :load_natural_earth_feature: with the category="physical" and
    name="coastline".
    """
    if resolution is None:
        resolution = COASTLINES_RESOLUTION

    return load_natural_earth_feature(
        "physical",
        "coastline",
        resolution=resolution,
        radius=radius,
        zlevel=zlevel,
        zscale=zscale,
    )


# @lru_cache(maxsize=LRU_CACHE_SIZE) # TODO(Chris): Can't cache PolyData...
def load_natural_earth_feature(
    category: str,
    name: str,
    resolution: str | None = None,
    radius: float | None = None,
    zlevel: int | None = None,
    zscale: float | None = None,
    drape_over_mesh: pv.PolyData = None,
) -> pv.PolyData:
    """Create a mesh of natural earth geometries at the specified `resolution`.

    Optionally, these can be "draped" over an existing mesh by finding the
    vertical intersection of the geometries with a user provided mesh.

    Parameters
    ----------
    category : str
        The Natural Earth category of the feature.
    name : str
        The name of the Natural Earth feature.
    resolution : str, optional
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m``, or ``10m``. Default to
        :data:`geovista.common.COASTLINES_RESOLUTION`.
    radius : float, optional
        The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
    zlevel : int, default=0
        The z-axis level. Used in combination with the `zscale` to offset the
        `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
    zscale : float, optional
        The proportional multiplier for z-axis `zlevel`. Defaults to
        :data:`geovista.common.ZLEVEL_SCALE`.
    drape_over_mesh : PolyData, optional
        A mesh to drape the feature over. Warning: can be computationally
        expensive; only use for small domains or low resolution features
        and/or meshes.

    Returns
    -------
    PolyData
        A mesh of the poly line feature.

    Notes
    -----
    .. versionadded:: 0.6.0

    Calls :func:`load_natural_earth_geometries` to download the original
    geometries.

    """
    if resolution is None:
        resolution = COASTLINES_RESOLUTION

    radius = RADIUS if radius is None else abs(float(radius))
    zscale = ZLEVEL_SCALE if zscale is None else float(zscale)
    zlevel = 0 if zlevel is None else int(zlevel)
    radius += radius * zlevel * zscale

    geoms_list = load_natural_earth_geometries(category, name, resolution=resolution)
    npoints_per_geom = [geom.shape[0] for geom in geoms_list]
    ngeoms = len(geoms_list)
    geoms = np.concatenate(geoms_list)
    nlines = geoms.shape[0] - ngeoms

    if drape_over_mesh is not None:
        # Calculate lower and upper vertical bounds of geoms. These will be
        # used make a 2D "wall" extending from the lower to upper bounds.
        geoms_lower = to_cartesian(geoms[:, 0], geoms[:, 1], radius=radius * 0.5)
        geoms_upper = to_cartesian(geoms[:, 0], geoms[:, 1], radius=radius * 1.5)
        geoms = np.r_[geoms_lower, geoms_upper]
        verts = np.full((nlines, 5), 4, dtype=int)  # 4 nodes per face
        npnts = geoms.shape[0] / 2
    else:
        # simple line mesh
        geoms = to_cartesian(geoms[:, 0], geoms[:, 1], radius=radius)
        verts = np.full((nlines, 3), 2, dtype=int)  # 2 nodes per line

    # convert geometries to a vtk line/poly mesh
    mesh = pv.PolyData()
    mesh.points = geoms
    pstart, lstart = 0, 0

    for npoints in npoints_per_geom:
        pend = pstart + npoints
        lend = lstart + npoints - 1
        verts[lstart:lend, 1] = np.arange(pstart, pend - 1, dtype=int)
        verts[lstart:lend, 2] = np.arange(pstart + 1, pend, dtype=int)
        if drape_over_mesh is not None:
            verts[lstart:lend, 3] = npnts + np.arange(pstart + 1, pend, dtype=int)
            verts[lstart:lend, 4] = npnts + np.arange(pstart, pend - 1, dtype=int)
        pstart, lstart = pend, lend

    if drape_over_mesh is not None:
        mesh.faces = verts

        # Need to triangulate both coastline wall and underlying mesh
        # as pyvista struggles to intersect rectangular cells
        mesh.triangulate(inplace=True)
        if not drape_over_mesh.is_all_triangles:
            drape_over_mesh = drape_over_mesh.triangulate(inplace=False)

        # Get intersection of border "wall" with warped mesh. Could be slow...
        intersection, _, _ = drape_over_mesh.intersection(
            mesh, split_first=False, split_second=False
        )

        if intersection.number_of_points == 0:
            msg = (
                "No intersection found between mesh and feature. "
                "Try triangulating the mesh."
            )
            raise ValueError(msg)

        mesh = intersection
    else:
        mesh.lines = verts

    mesh.field_data[GV_FIELD_RADIUS] = np.array([radius])
    mesh.field_data[GV_FIELD_RESOLUTION] = np.array([resolution])
    to_wkt(mesh, WGS84)

    return mesh
