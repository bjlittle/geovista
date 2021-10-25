"""
A package for provisioning common geovista infra-structure.

"""
from collections.abc import Iterable
from typing import Optional

import numpy as np
import numpy.ma as ma
from numpy.typing import ArrayLike
import pyvista as pv

from .log import get_logger

__all__ = [
    "nan_mask",
    "set_jupyter_backend",
    "to_xy0",
    "to_xyz",
    "wrap",
]

# configure the logger
logger = get_logger(__name__)

#
# TODO: support richer default management
#

#: Default jupyter plotting backend for pyvista.
JUPYTER_BACKEND: bool = "ipygany"


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


def nan_mask(data: ArrayLike) -> ArrayLike:
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
    ArrayLike
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
            logger.info(f"Unable to set the pyvista jupyter backend to {backend!r}")
    else:
        logger.debug("No active IPython kernel available")

    return result


def to_xy0(
    xyz: ArrayLike, radius: Optional[float] = 1.0, stacked: Optional[bool] = True
) -> ArrayLike:
    """
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

    Notes
    -----
    .. versionadded:: 0.1.0

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
    radius: Optional[float] = 1.0,
    stacked: Optional[bool] = True,
) -> ArrayLike:
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
    ArrayLike
        The geocentric xyz coordinates.

    Notes
    -----
    .. versionadded:: 0.1.0

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


def wrap(
    longitudes: ArrayLike, base: float = -180.0, period: Optional[float] = 360.0
) -> ArrayLike:
    """
    Transform the longitude values to be within the closed interval
    [base, base + period].

    Parameters
    ----------
    longitudes : ArrayLike
        One or more longitude values (degrees) to be wrapped.
    base : float, default=-180.0
        The start limit of the closed interval.
    period : float, default=360.0
        The end limit of the closed interval expressed as a length from the
        `base`.

    Returns
    -------
    ArrayLike
        The transformed longitude values.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if not isinstance(longitudes, Iterable):
        longitudes = [longitudes]
    longitudes = np.asanyarray(longitudes)
    result = ((longitudes.astype(np.float64) - base + period * 2) % period) + base
    return result
