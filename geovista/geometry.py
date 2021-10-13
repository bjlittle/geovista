from functools import lru_cache
from typing import Optional

import cartopy.io.shapereader as shp
import numpy as np
from numpy.typing import ArrayLike
import pyvista as pv
from shapely.geometry.multilinestring import MultiLineString

from .common import set_jupyter_backend
from .logger import get_logger

__all__ = [
    "add_coastlines",
    "combine_coastlines",
    "fetch_coastline_geometries",
    "get_coastlines",
    "to_xy0",
    "to_xyz",
]


#
# TODO: support richer default management
#

#: Default coastline resolution.
COASTLINE_RESOLUTION: str = "110m"

#: Default to an S2 unit sphere for 3D plotting.
RADIUS: float = 1.0

# Configure the logger.
logger = get_logger(__name__)


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


def combine_coastlines(
    resolution: Optional[str] = COASTLINE_RESOLUTION,
    merge_points: Optional[bool] = True,
) -> pv.UnstructuredGrid:
    """
    .. versionadded:: 0.1.0

    Parameters
    ----------

    Returns
    -------
    UnstructuredGrid

    """
    blocks = fetch_coastline_geometries(resolution=resolution)
    mesh = blocks.combine(merge_points=merge_points)
    mesh.field_data["radius"] = blocks.field_data["radius"]

    return mesh


@lru_cache
def fetch_coastline_geometries(
    resolution: Optional[str] = COASTLINE_RESOLUTION, geocentric: Optional[bool] = True
) -> pv.MultiBlock:
    """
    .. versionadded:: 0.1.0

    Fetch the Natural Earth coastline shapefile geometries for the required
    resolution.

    If the geometries are not already available in the Cartopy cache, then they
    will downloaded.

    The geometries will be then transformed for use with a 2D planar projection
    or a 3D spherical mesh.

    Parameters
    ----------
    resolution : str, default="110m"
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m`` or ``10m``.
    geocentric : bool, default=True
        Convert the coastline longitude (φ) and latitude (λ) geometries to
        geocentric xyz coordinates. Otherwise, xy0 (i.e., φλ0) coordinates.

    Returns
    -------
    pyvista.MultiBlock
        A :class:~pyvista.MultiBlock` containing one or more
        :class:`~pyvista.PolyData` coastline geometries.

    """
    # TODO: address "fudge-factor" zorder to ensure coastlines overlay the mesh
    radius = RADIUS + RADIUS / 1e4

    category, name = "physical", "coastline"

    # load in the shapefiles
    fname = shp.natural_earth(resolution=resolution, category=category, name=name)
    reader = shp.Reader(fname)
    blocks = pv.MultiBlock()
    geoms = []

    def to_pyvista_blocks(geometries):
        for geometry in geometries:
            if isinstance(geometry, MultiLineString):
                geoms.extend(list(geometry.geoms))
            else:
                xy = np.array(geometry.coords[:], dtype=np.float32)

                if geocentric:
                    # calculate 3d xyz coordinates
                    xr = np.radians(xy[:, 0]).reshape(-1, 1)
                    yr = np.radians(90 - xy[:, 1]).reshape(-1, 1)

                    x = radius * np.sin(yr) * np.cos(xr)
                    y = radius * np.sin(yr) * np.sin(xr)
                    z = radius * np.cos(yr)
                else:
                    # otherwise, calculate xy0 coordinates
                    x = xy[:, 0].reshape(-1, 1)
                    y = xy[:, 1].reshape(-1, 1)
                    z = np.zeros_like(x)

                xyz = np.hstack((x, y, z))
                poly = pv.lines_from_points(xyz, close=False)
                blocks.append(poly)
                logger.debug(f"coastline block {blocks.n_blocks}")

    to_pyvista_blocks(reader.geometries())
    if geoms:
        to_pyvista_blocks(geoms)

    blocks.field_data["radius"] = np.array([radius if geocentric else 0])

    return blocks


@lru_cache
def get_coastlines(
    resolution: Optional[str] = COASTLINE_RESOLUTION,
    geocentric: Optional[bool] = True,
) -> pv.UnstructuredGrid:
    """ """
    from .cache import fetch_coastlines

    mesh = fetch_coastlines(resolution=resolution)
    if not geocentric:
        radius = float(mesh.field_data["radius"])
        mesh.points = to_xy0(mesh.points, radius=radius)

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
