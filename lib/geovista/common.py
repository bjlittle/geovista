"""
A package for provisioning common geovista infra-structure.

"""
from collections.abc import Iterable
from typing import Any, Optional, Tuple

import numpy as np
import numpy.ma as ma
import numpy.typing as npt
import pyvista as pv

from .log import get_logger

__all__ = [
    "GV_CELL_IDS",
    "GV_FIELD_CRS",
    "GV_FIELD_NAME",
    "GV_POINT_IDS",
    "GV_REMESH_POINT_IDS",
    "REMESH_JOIN",
    "REMESH_SEAM",
    "VTK_CELL_IDS",
    "VTK_POINT_IDS",
    "ZLEVEL_FACTOR",
    "calculate_radius",
    "logger",
    "nan_mask",
    "sanitize_data",
    "set_jupyter_backend",
    "to_xy0",
    "to_xyz",
    "triangulated",
    "wrap",
]

# Configure the logger
logger = get_logger(__name__)

#
# TODO: support richer default management
#

#: Name of the geovista cell indices array.
GV_CELL_IDS: str = "gvOriginalCellIds"

#: The field array name of the CF serialized pyproj CRS.
GV_FIELD_CRS: str = "gvCRS"

#: The field array name of the mesh containing field, point and/or cell data.
GV_FIELD_NAME: str = "gvName"

#: Name of the geovista point indices array.
GV_POINT_IDS: str = "gvOriginalPointIds"

#: Name of the geovista remesh point indices/marker array.
GV_REMESH_POINT_IDS: str = "gvRemeshPointIds"

#: Default jupyter plotting backend for pyvista.
JUPYTER_BACKEND: str = "pythreejs"

#: Marker for remesh filter cell join point.
REMESH_JOIN: int = -3

#: Marker for remesh filter western cell boundary point.
REMESH_SEAM: int = -1

#: Name of the VTK cell indices array.
VTK_CELL_IDS: str = "vtkOriginalCellIds"

#: Name of the VTK point indices array.
VTK_POINT_IDS: str = "vtkOriginalPointIds"

#: Proportional multiplier for z-axis levels/offsets.
ZLEVEL_FACTOR: float = 1e-3


def active_kernel() -> bool:
    """
    Determine whether we are executing within an ``IPython`` kernel.

    Returns
    -------
    bool

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    result = True

    try:
        from IPython import get_ipython

        ip = get_ipython()
        # the following statement may or may not raise an exception
        ip.kernel
    except (AttributeError, ModuleNotFoundError):
        result = False

    return result


def calculate_radius(
    mesh: pv.PolyData,
    origin: Optional[Tuple[float, float, float]] = None,
    decimals: Optional[int] = 8,
) -> float:
    """
    Determine the radius of the provided mesh.

    Note that, assumes that the mesh is a spheroid and has not been warped.

    Parameters
    ----------
    mesh : PolyData
        The surface that requires its radius to be calculated, relative to
        the ``origin``.
    origin : float, default=(0, 0, 0)
        The (x, y, z) cartesian center of the spheroid mesh.
    decimals : int, default=8
        The number of decimal places to round the calculated radius.

    Returns
    -------
    float
        The radius of the provided mesh.

    Notes
    -----
    .. versionadded: 0.1.0

    """
    xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds
    xdiff, ydiff, zdiff = (xmax - xmin), (ymax - ymin), (zmax - zmin)

    if np.isclose(xdiff, 0) or np.isclose(ydiff, 0) or np.isclose(zdiff, 0):
        emsg = (
            "Cannot calculate radius of a surface that does not appear to be "
            "spherical."
        )
        raise ValueError(emsg)

    if origin is None:
        origin = (0, 0, 0)

    ox, oy, oz = origin

    # sample a representative mesh point
    mx, my, mz = mesh.points[0]

    radius = np.sqrt((mx - ox) ** 2 + (my - oy) ** 2 + (mz - oz) ** 2)
    result = np.round(radius, decimals=decimals)
    logger.debug(
        "radius %f rounded to %f (%d decimal places)", radius, result, decimals
    )

    return result


def nan_mask(data: npt.ArrayLike) -> np.ndarray:
    """
    Replaces any masked array values with NaNs.

    As a consequence of filling the mask with NaNs, non-float arrays will be
    cast to float.

    Parameters
    ----------
    data : ArrayLike
        The masked array to be filled with NaNs.

    Returns
    -------
    ndarray
        The `data` with masked values replaced with NaNs.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if np.ma.isMaskedArray(data):
        if data.dtype.char not in np.typecodes["Float"]:
            dmsg = (
                f"converting from '{np.typename(data.dtype.char)}' "
                f"to '{np.typename('f')}"
            )
            logger.debug(dmsg)
            data = ma.asanyarray(data, dtype=float)

        data = data.filled(np.nan)

    return data


def sanitize_data(
    *meshes: Any,
) -> None:
    """
    Purge standard VTK helper cell and point data index arrays.

    Parameters
    ----------
    meshes : iterable of PolyData
        The :class:`pyvista.PolyData` to sanitize.

    Notes
    -----
    .. versionadded:: 0.1.0
    """
    if not meshes:
        emsg = "Expected one or more meshes to sanitize."
        raise ValueError(emsg)

    for mesh in meshes:
        if VTK_CELL_IDS in mesh.cell_data:
            del mesh.cell_data[VTK_CELL_IDS]

        if VTK_POINT_IDS in mesh.point_data:
            del mesh.point_data[VTK_POINT_IDS]


def set_jupyter_backend(backend: Optional[str] = None) -> bool:
    """
    Configure the jupyter plotting backend for pyvista.

    Parameters
    ----------
    backend : str, optional
        The pyvista plotting backend. For further details see
        :func:`pyvista.set_jupyter_backend`. If ``None``, defaults to
        :data:`JUPYTER_BACKEND`.

    Returns
    -------
    bool
        Whether the jupyter backend was successfully configured.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    result = False
    if active_kernel():
        try:
            if backend is None:
                backend = JUPYTER_BACKEND
            pv.set_jupyter_backend(backend)
            result = True
        except ImportError:
            logger.info("Unable to set the pyvista jupyter backend to '%s'", backend)
    else:
        logger.debug("No active IPython kernel available")

    return result


def to_xy0(
    mesh: pv.PolyData,
    radius: Optional[float] = None,
    stacked: Optional[bool] = True,
    closed_interval: Optional[bool] = False,
) -> np.ndarray:
    """
    Convert the xyz cartesian points of the mesh to longitude (φ) and latitude (λ)
    xy0 (i.e., φλ0) coordinates.

    Parameters
    ----------
    mesh : PolyData
        The mesh containing the cartesian (x, y, z) points to be converted to
        longitude and latitude coordinates.
    radius : float, optional
        The radius of the sphere. If not provided the radius is determined
        from the mesh.
    stacked : bool, default=True
        Specify whether the resultant xy0 coordinates have shape (N, 3).
        Otherwise, they will have shape (3, N).
    closed_interval : bool, default=False
        Longitude values will be in the half-closed interval [-180, 180). However,
        if the mesh has a seam at the 180th meridian and ``closed_interval``
        is ``True``, then longitudes will be in the closed interval [-180, 180].

    Returns
    -------
    ndarray
        The longitude and latitude xy0 coordinates, in degrees.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    radius = calculate_radius(mesh) if radius is None else abs(radius)
    xyz = mesh.points
    # XXX: hack
    lons = wrap(np.degrees(np.arctan2(xyz[:, 1], xyz[:, 0])), decimals=4)
    lats = np.degrees(np.arcsin(xyz[:, 2] / radius))
    z = np.zeros_like(lons)
    data = [lons, lats, z]

    if closed_interval:
        if GV_REMESH_POINT_IDS in mesh.point_data:
            seam_ids = np.where(mesh[GV_REMESH_POINT_IDS] == REMESH_SEAM)[0]
            seam_lons = lons[seam_ids]
            seam_mask = np.isclose(np.abs(seam_lons), 180)
            lons[seam_ids[seam_mask]] = 180
        else:
            logger.debug(
                "cannot honour closed interval due to missing '%s' field",
                GV_REMESH_POINT_IDS,
            )

    if stacked:
        result = np.vstack(data).T
    else:
        result = np.array(data)

    return result


def to_xyz(
    longitudes: npt.ArrayLike,
    latitudes: npt.ArrayLike,
    radius: Optional[float] = None,
    stacked: Optional[bool] = True,
) -> np.ndarray:
    """
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
    ndarray
        The geocentric xyz coordinates.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    longitudes = np.ravel(longitudes)
    latitudes = np.ravel(latitudes)
    radius = 1.0 if radius is None else abs(radius)

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


def triangulated(surface: pv.PolyData) -> bool:
    """
    Determine whether the provided surface is triangulated.

    Parameters
    ----------
    surface : PolyData
        The :class:`pyvista.PolyData` surface mesh to check
        whether the geometry of all its cells are triangles.

    Returns
    -------
    bool
        Whether the surface is fully triangulated.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return np.all(np.diff(surface._offset_array) == 3)


def wrap(
    longitudes: npt.ArrayLike,
    base: Optional[float] = -180.0,
    period: Optional[float] = 360.0,
    decimals: Optional[int] = 8,
) -> np.ndarray:
    """
    Transform the longitude values to be within the closed interval
    [base, base + period].

    Parameters
    ----------
    longitudes : ArrayLike
        One or more longitude values (degrees) to be wrapped.
    base : float, default=-180.0
        The start limit (degrees) of the closed interval.
    period : float, default=360.0
        The end limit (degrees) of the closed interval expressed as a length
        from the `base`.

    Returns
    -------
    ndarray
        The transformed longitude values.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    #
    # TODO: support radians
    #
    if not isinstance(longitudes, Iterable):
        longitudes = [longitudes]

    longitudes = np.round(longitudes, decimals=decimals)
    result = ((longitudes.astype(np.float64) - base + period * 2) % period) + base

    return result
