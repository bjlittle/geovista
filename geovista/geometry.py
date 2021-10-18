from functools import lru_cache
from typing import List, Optional

import cartopy.io.shapereader as shp
import numpy as np
from numpy.typing import ArrayLike
import pyvista as pv
from shapely.geometry.multilinestring import MultiLineString

from .common import set_jupyter_backend
from .log import get_logger

__all__ = [
    "add_coastlines",
    "coastline_geometries",
    "coastline_mesh",
    "coastlines",
    "to_xy0",
    "to_xyz",
]

# Configure the logger.
logger = get_logger(__name__)

#
# TODO: support richer default management
#

#: Default coastline resolution.
COASTLINE_RESOLUTION: str = "110m"

#: Default to an S2 unit sphere for 3D plotting.
RADIUS: float = 1.0


def add_coastlines(
    resolution: Optional[str] = COASTLINE_RESOLUTION,
    projection: Optional[str] = None,
    plotter: Optional[pv.Plotter] = None,
    **kwargs,
) -> pv.Plotter:
    """
    .. versionadded:: 0.1.0

    Add the specified Natural Earth coastline geometries to a PyVista plotter
    for rendering.

    Parameters
    ----------
    resolution : str, default="110m"
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m`` or ``10m``.
    projection : str or None, default=None
        The name of the PROJ planar projection used to transform the coastlines
        into a 2D projection coordinate system. If ``None``, the coastline
        geometries are rendered on a 3D sphere.
    plotter : Plotter or None, default=None
        The :class:`~pyvista.Plotter` which renders the scene.
        If ``None``, a new :class:`~pyvista.Plotter` will be created.
    **kwargs : dict, optional
        Additional `kwargs` to be passed to PyVista when creating a coastline
        :class:`~pyvista.PolyData`.

    Returns
    -------
    Plotter
        The provided `plotter` or a new :class:`~pyvista.Plotter`.

    """
    notebook = set_jupyter_backend()

    if plotter is None:
        plotter = pv.Plotter(notebook=notebook)

    # geocentric = projection is None
    # coastlines = get_coastlines(resolution, geocentric=geocentric)

    # if projection is not None:
    #     vtk_projection = vtkPolyDataTransformFilter(projection)
    #     coastlines = [vtk_projection.transform(coastline) for coastline in coastlines]
    #
    # for coastline in coastlines:
    #     plotter.add_mesh(coastline, pickable=False, **kwargs)

    return plotter


@lru_cache
def coastline_geometries(
    resolution: Optional[str] = COASTLINE_RESOLUTION,
) -> List[ArrayLike]:
    """
    .. versionadded:: 0.1.0

    Fetch the Natural Earth shapefile coastline geometries for the required
    resolution.

    If the geometries are not already available within the cartopy cache, then
    they will be downloaded.

    The 2D longitude (φ) and latitude (λ) xy coastline geometries will be
    unpacked as 3D xy0 coordinates i.e., φλ0.

    Parameters
    ----------
    resolution : str, default="110m"
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m`` or ``10m``.

    Returns
    -------
    List[ArrayLike]
        A list containing one or more coastline xy0 geometries.

    """
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

    logger.debug(f"loaded {len(lines)} geometries")

    return lines


@lru_cache
def coastline_mesh(
    resolution: Optional[str] = COASTLINE_RESOLUTION,
    radius: Optional[float] = None,
    geocentric: Optional[bool] = True,
) -> pv.PolyData:
    """
    .. versionadded:: 0.1.0

    Create a mesh of coastline geometries at the specified resolution.

    Parameters
    ----------
    resolution : str, default="110m"
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m``, or ``10m``.
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

    """
    # TODO: address "fudge-factor" zlevel
    if radius is None:
        radius = RADIUS + RADIUS / 1e4

    geoms = coastline_geometries(resolution=resolution)
    npoints_per_geom = [geom.shape[0] for geom in geoms]
    ngeoms = len(geoms)
    geoms = np.concatenate(geoms)
    nlines = geoms.shape[0] - ngeoms

    # determine whether to calculate xyz geocentric coordinates
    if geocentric:
        xr = np.radians(geoms[:, 0]).reshape(-1, 1)
        yr = np.radians(90 - geoms[:, 1]).reshape(-1, 1)
        x = radius * np.sin(yr) * np.cos(xr)
        y = radius * np.sin(yr) * np.sin(xr)
        z = radius * np.cos(yr)
        geoms = np.hstack([x, y, z])
        logger.debug(f"geometries converted from xy0 to xyz, radius={radius}")

    logger.debug(f"coastlines geometry shape={geoms.shape}")

    # convert geometries to a vtk line mesh
    mesh = pv.PolyData()
    mesh.points = geoms
    lines = np.full((nlines, 3), 2, dtype=int)
    pstart, lstart = 0, 0

    logger.debug(f"ngeoms={ngeoms}, nlines={nlines}")

    for npoints in npoints_per_geom:
        pend = pstart + npoints
        lend = lstart + npoints - 1
        lines[lstart:lend, 1] = np.arange(pstart, pend - 1, dtype=int)
        lines[lstart:lend, 2] = np.arange(pstart + 1, pend, dtype=int)
        pstart, lstart = pend, lend

    mesh.lines = lines
    mesh.field_data["radius"] = np.array([radius if geocentric else 0])

    return mesh


@lru_cache
def coastlines(
    resolution: Optional[str] = COASTLINE_RESOLUTION,
    geocentric: Optional[bool] = True,
) -> pv.PolyData:
    """
    .. versionadded:: 0.1.0

    Create or fetch the cached mesh of the coastlines.

    Parameters
    ----------
    resolution : str, default="110m"
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m``, or ``10m``.
    geocentric : bool, default=True
        Specify whether the coastlines are xyz geocentric coordinates.
        Otherwise, longitude (φ) and latitude (λ) xy0 coordinates (i.e., φλ0).

    Returns
    -------
    PolyData
        A mesh of the coastlines.

    """
    from .cache import fetch_coastlines

    try:
        mesh = fetch_coastlines(resolution=resolution)

        if not geocentric:
            radius = float(mesh.field_data["radius"])
            mesh.points = to_xy0(mesh.points, radius=radius)
    except ValueError:
        mesh = coastline_mesh(resolution=resolution, geocentric=geocentric)

    return mesh


def to_xy0(
    xyz: ArrayLike, radius: Optional[float] = RADIUS, stacked: Optional[bool] = True
) -> ArrayLike:
    """
    .. versionadded:: 0.1.0

    Convert geocentric xyz coordinates to longitude (φ) and latitude (λ)
    xy0 (i.e., φλ0) coordinates.

    Parameters
    ----------
    xyz : ArrayLike
        A sequence of one or more (x, y, z) values to be converted to
        longitude and latitude coordinates.
    radius : bool, default=1.0
        The radius of the sphere. Defaults to an S2 unit sphere.
    stacked : bool, default=True
        Specify whether the resultant xy0 coordinates have shape (N, 3).
        Otherwise, they will have shape (3, N).

    Returns
    -------
    ArrayLike
        The longitude and latitude xy0 coordinates, in degrees.

    """
    xyz = np.asanyarray(xyz)
    lons = np.degrees(np.arctan2(xyz[:, 1], xyz[:, 0]))
    lats = np.degrees(np.arcsin(xyz[:, 2] / radius))
    z = np.zeros_like(lons)
    data = [lons, lats, z]

    if stacked:
        result = np.vstack(data).T
    else:
        result = np.array(data)

    return result


def to_xyz(
    longitudes: ArrayLike,
    latitudes: ArrayLike,
    radius: Optional[float] = RADIUS,
    stacked: Optional[bool] = True,
) -> ArrayLike:
    """
    .. versionadded:: 0.1.0

    Convert longitudes (φ) and latitudes (λ) to geocentric xyz coordinates.

    Parameters
    ----------
    longitudes : ArrayLike
        The longitude values (degrees) to be converted.
    latitudes : ArrayLike
        The latitude values (degrees) to be converted.
    radius : float, default=1.0
        The radius of the sphere. Defaults to an S2 unit sphere.
    stacked : bool, default=True
        Specify whether the resultant xyz coordinates have shape (N, 3).
        Otherwise, they will have shape (3, N).

    Returns
    -------
    ArrayLike
        The geocentric xyz coordinates.

    """
    longitudes = np.ravel(longitudes)
    latitudes = np.ravel(latitudes)

    x_rad = np.radians(longitudes)
    y_rad = np.radians(90.0 - latitudes)
    x = radius * np.sin(y_rad) * np.cos(x_rad)
    y = radius * np.sin(y_rad) * np.sin(x_rad)
    z = radius * np.cos(y_rad)
    xyz = [x, y, z]

    if stacked:
        xyz = np.vstack(xyz).T
    else:
        xyz = np.array(xyz)

    return xyz
