"""
This module provides Natural Earth geometry support.

Notes
-----
.. versionadded:: 0.1.0

"""
from functools import lru_cache
from typing import List, Optional

import cartopy.io.shapereader as shp
import numpy as np
import pyvista as pv
from shapely.geometry.multilinestring import MultiLineString

from .common import GV_FIELD_RADIUS, RADIUS, set_jupyter_backend, to_xy0, to_xyz

__all__ = [
    "COASTLINE_RESOLUTION",
    "add_coastlines",
    "coastline_geometries",
    "coastline_mesh",
    "get_coastlines",
]

#
# TODO: support richer default management
#

#: Default coastline resolution.
COASTLINE_RESOLUTION: str = "10m"


def add_coastlines(
    resolution: Optional[str] = None,
    projection: Optional[str] = None,
    plotter: Optional[pv.Plotter] = None,
    **kwargs,
) -> pv.Plotter:
    """
    Add the specified Natural Earth coastline geometries to a PyVista plotter
    for rendering.

    Parameters
    ----------
    resolution : str, optional
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m`` or ``10m``. Defaults to
        :data:`geovista.geometry.COASTLINE_RESOLUTION`.
    projection : str or None, default=None
        The name of the PROJ planar projection used to transform the coastlines
        into a 2D projection coordinate system. If ``None``, the coastline
        geometries are rendered on a 3D sphere.
    plotter : Plotter or None, default=None
        The :class:`~pyvista.Plotter` which renders the scene.
        If ``None``, a new :class:`~pyvista.Plotter` will be created.
    **kwargs : dict, optional
        Additional `kwargs` to be passed to PyVista when creating a coastlines
        :class:`~pyvista.PolyData`.

    Returns
    -------
    Plotter
        The provided `plotter` or a new :class:`~pyvista.Plotter`.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if resolution is None:
        resolution = COASTLINE_RESOLUTION

    notebook = set_jupyter_backend()

    if plotter is None:
        plotter = pv.Plotter(notebook=notebook)

    #
    # TODO: support planar projections
    #

    mesh = get_coastlines(resolution=resolution)
    plotter.add_mesh(mesh, pickable=False, **kwargs)

    return plotter


@lru_cache
def coastline_geometries(
    resolution: Optional[str] = None,
) -> List[np.ndarray]:
    """
    Fetch the Natural Earth shapefile coastline geometries for the required
    resolution.

    If the geometries are not already available within the cartopy cache, then
    they will be downloaded.

    The 2D longitude (φ) and latitude (λ) xy coastline geometries will be
    unpacked as 3D xy0 coordinates i.e., φλ0.

    Parameters
    ----------
    resolution : str, optional
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m`` or ``10m``. Defaults to
        :data:`geovista.geometry.COASTLINE_RESOLUTION`.

    Returns
    -------
    List[np.ndarray]
        A list containing one or more coastline xy0 geometries.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if resolution is None:
        resolution = COASTLINE_RESOLUTION

    lines, multi_lines = [], []
    category, name = "physical", "coastline"

    # load in the shapefiles
    fname = shp.natural_earth(resolution=resolution, category=category, name=name)
    reader = shp.Reader(fname)

    def unpack(geometries):
        for geometry in geometries:
            if isinstance(geometry, MultiLineString):
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


@lru_cache
def coastline_mesh(
    resolution: Optional[str] = None,
    radius: Optional[float] = None,
    geocentric: Optional[bool] = True,
) -> pv.PolyData:
    """
    Create a mesh of coastline geometries at the specified resolution.

    Parameters
    ----------
    resolution : str, optional
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m``, or ``10m``. Default to
        :data:`geovista.geometry.COASTLINE_RESOLUTION`.
    radius : float, default=1.0
        The radius of the sphere, when geocentric. Defaults to the S2 unit
        sphere.
    geocentric : bool, default=True
        Specify whether the coastlines are xyz geocentric coordinates.
        Otherwise, longitude (φ) and latitude (λ) xy0 coordinates (i.e., φλ0).

    Returns
    -------
    PolyData
        A mesh of the coastlines.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if resolution is None:
        resolution = COASTLINE_RESOLUTION

    # TODO: address "fudge-factor" zlevel
    radius = RADIUS + RADIUS / 1e4 if radius is None else abs(radius)

    geoms = coastline_geometries(resolution=resolution)
    npoints_per_geom = [geom.shape[0] for geom in geoms]
    ngeoms = len(geoms)
    geoms = np.concatenate(geoms)
    nlines = geoms.shape[0] - ngeoms

    # determine whether to calculate xyz geocentric coordinates
    if geocentric:
        geoms = to_xyz(geoms[:, 0], geoms[:, 1], radius=radius)

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
    if geocentric:
        mesh.field_data[GV_FIELD_RADIUS] = np.array([radius])

    return mesh


@lru_cache
def get_coastlines(
    resolution: Optional[str] = None,
    #    geocentric: Optional[bool] = True,
) -> pv.PolyData:
    """
    Create or fetch the cached mesh of the coastlines.

    Parameters
    ----------
    resolution : str, default=COASTLINE_RESOLUTION
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m``, or ``10m``. Defaults to
        :data:`geovista.geometry.COASTLINE_RESOLUTION`.

    Returns
    -------
    PolyData
        A mesh of the coastlines.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # pylint: disable-next=import-outside-toplevel
    from .cache import fetch_coastlines

    if resolution is None:
        resolution = COASTLINE_RESOLUTION

    # TODO: reinstate with projection support is available
    # geocentric : bool, default=True
    #     Specify whether the coastlines are xyz geocentric coordinates.
    #     Otherwise, longitude (φ) and latitude (λ) xy0 coordinates (i.e., φλ0).
    geocentric = True

    try:
        mesh = fetch_coastlines(resolution=resolution)

        if not geocentric:
            radius = float(mesh.field_data[GV_FIELD_RADIUS])
            mesh.points = to_xy0(mesh, radius=radius)
    except ValueError:
        mesh = coastline_mesh(resolution=resolution, geocentric=geocentric)

    return mesh
