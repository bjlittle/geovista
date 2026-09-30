# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Coordinate reference system (CRS) utility functions.

Notes
-----
.. versionadded:: 0.1.0

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
import warnings

import lazy_loader as lazy
import pyproj
from pyproj import CRS

from .common import GV_FIELD_CRS

if TYPE_CHECKING:
    import pyvista as pv

# lazy import third-party dependencies
np = lazy.load("numpy")

__all__ = [
    "WGS84",
    "CRSLike",
    "PlateCarree",
    "from_wkt",
    "get_central_meridian",
    "has_wkt",
    "projected",
    "set_central_meridian",
    "to_wkt",
]

type CRSLike = int | str | dict[str, Any] | pyproj.crs.crs.CRS
"""Type alias for a Coordinate Reference System."""

# constants
EPSG_CENTRAL_MERIDIAN: str = "8802"
"""EPSG projection parameter for longitude of natural origin/central meridian."""

EPSG_CENTRAL_MERIDIAN_ALIASES: tuple[str, ...] = (
    EPSG_CENTRAL_MERIDIAN,  # longitude of natural origin
    "8822",  # longitude of false origin e.g. conic projections
    "8812",  # longitude of projection centre e.g. oblique mercator
    "8835",  # longitude of topocentric origin e.g. vertical perspective
)
"""EPSG projection parameters that may carry the central meridian.

A projection method defines its longitudinal origin using whichever parameter
suits its geometry, so the central meridian is not always EPSG ``8802``.
Ordered by precedence.
"""

PROJ_CENTRAL_MERIDIAN: str = "lon_0"
"""PROJ parameter for the central meridian, used by PROJ-native methods."""

PROJ_ROTATED_POLE: tuple[str, str] = ("o_lon_p", "o_lat_p")
"""PROJ parameters identifying a rotated pole coordinate operation."""

PlateCarree = CRS.from_user_input("epsg:32662")
"""WGS84 / Plate Carree (Equidistant Cylindrical)."""

WGS84 = CRS.from_user_input("epsg:4326")
"""Geographic WGS84."""


def from_wkt(mesh: pv.PolyData) -> CRS:
    """Get the :class:`~pyproj.crs.CRS` associated with the mesh.

    Parameters
    ----------
    mesh : :class:`~pyvista.PolyData`
        The mesh containing the :class:`~pyproj.crs.CRS` serialized as OGC
        Well-Known-Text (WKT).

    Returns
    -------
    :class:`~pyproj.crs.CRS`
        The Coordinate Reference System.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    crs = None

    if has_wkt(mesh):
        wkt = str(mesh.field_data[GV_FIELD_CRS][0])
        crs = CRS.from_wkt(wkt)

    return crs


def _find_central_meridian(
    crs_json: dict[str, Any],
) -> tuple[dict[str, Any], str] | None:
    """Locate the mapping within `crs_json` that carries the central meridian.

    Shared by :func:`get_central_meridian` and :func:`set_central_meridian` so
    that the two cannot disagree about where the central meridian lives.

    Parameters
    ----------
    crs_json : dict
        The Coordinate Reference System serialized as PROJ JSON, as returned by
        :meth:`pyproj.crs.CRS.to_json_dict`.

    Returns
    -------
    tuple of (dict, str) or None
        The mapping holding the central meridian and the key within it, or
        ``None`` if the central meridian could not be located.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    conversion = crs_json.get("conversion") or {}
    parameters = conversion.get("parameters") or []

    # a rotated pole expresses its origin relative to the rotated pole itself,
    # for which a scalar central meridian is not a faithful abstraction
    if any(param.get("name") in PROJ_ROTATED_POLE for param in parameters):
        return None

    by_code: dict[str, dict[str, Any]] = {}
    native: dict[str, Any] | None = None

    for param in parameters:
        # a PROJ-native method has no EPSG identifier for its parameters
        code = (param.get("id") or {}).get("code")
        if code is not None:
            by_code[str(code)] = param
        elif param.get("name") == PROJ_CENTRAL_MERIDIAN:
            native = param

    for code in EPSG_CENTRAL_MERIDIAN_ALIASES:
        if (param := by_code.get(code)) is not None:
            return param, "value"

    if native is not None:
        return native, "value"

    # cartopy >=0.26 defines PlateCarree(central_longitude=...) as a geographic
    # CRS shifted by its datum prime meridian, rather than as a conversion
    datum = crs_json.get("datum") or {}
    if (prime_meridian := datum.get("prime_meridian")) is not None:
        return prime_meridian, "longitude"

    return None


def get_central_meridian(crs: CRS) -> float | None:
    """Retrieve the longitude of natural origin of the `CRS`.

    The natural origin is also known as the central meridian.

    Parameters
    ----------
    crs : :class:`~pyproj.crs.CRS`
        The Coordinate Reference System.

    Returns
    -------
    float
        The central meridian, or ``None`` if the `crs` has no such parameter.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    located = _find_central_meridian(crs.to_json_dict())

    if located is None:
        if crs.coordinate_operation is not None:
            wmsg = (
                f"geovista is unable to determine the central meridian of the "
                f"{crs.name!r} coordinate reference system, and will assume 0. A "
                f"mesh transformed to this CRS may be torn at the wrong seam."
            )
            warnings.warn(wmsg, stacklevel=2)
        return None

    mapping, key = located
    value = mapping[key]

    if key == "longitude":
        # a prime meridian may be expressed in a non-degree angular unit, and a
        # Greenwich prime meridian is not a central meridian
        if isinstance(value, dict):
            return None
        if not value:
            return None

    return float(value)


def has_wkt(mesh: pv.PolyData) -> bool:
    """Determine whether the provided mesh has a CRS serialized as WKT attached.

    Parameters
    ----------
    mesh : :class:`~pyvista.PolyData`
        The mesh to be inspected for a serialized :class:`~pyproj.crs.CRS`.

    Returns
    -------
    bool
        Whether the mesh has a :class:`~pyproj.crs.CRS` serialized as WKT attached.

    Notes
    -----
    .. versionadded:: 0.4.0

    """
    return GV_FIELD_CRS in mesh.field_data


def projected(mesh: pv.PolyData) -> bool:
    """Determine if the mesh is a planar projection.

    Simple heuristic approach achieved by attempting to inspect the associated
    :class:`~pyproj.crs.CRS` of the mesh. If the mesh :class:`~pyproj.crs.CRS` is
    unavailable then the weaker contract of inspecting the mesh geometry is
    used to detect for a flat plane.

    Parameters
    ----------
    mesh : :class:`~pyvista.PolyData`
        The mesh to be inspected.

    Returns
    -------
    bool
        Whether the mesh is projected.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    crs = from_wkt(mesh)

    result: bool
    if crs is None:
        xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds
        xdelta, ydelta, zdelta = (xmax - xmin), (ymax - ymin), (zmax - zmin)
        result = np.isclose(xdelta, 0) or np.isclose(ydelta, 0) or np.isclose(zdelta, 0)
    else:
        result = crs.is_projected

    return result


def set_central_meridian(crs: CRS, meridian: float) -> CRS | None:
    """Replace the longitude of natural origin in the :class:`~pyproj.crs.CRS`.

    The natural origin is also known as the central meridian.

    Note that the `crs` is immutable, therefore a new instance will be
    returned with the specified central meridian.

    Parameters
    ----------
    crs : :class:`~pyproj.crs.CRS`
        The Coordinate Reference System.
    meridian : float
        The replacement central meridian.

    Returns
    -------
    :class:`~pyproj.crs.CRS` or None
        The :class:`~pyproj.crs.CRS` with the specified central meridian, or ``None``
        if the :class:`~pyproj.crs.CRS` has no such parameter.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # https://proj.org/development/reference/cpp/operation.html#classosgeo_1_1proj_1_1operation_1_1Conversion_1center_longitude
    crs_json = crs.to_json_dict()
    located = _find_central_meridian(crs_json)

    if located is None:
        return None

    mapping, key = located

    # a prime meridian in a non-degree angular unit is not rewritten, to avoid
    # silently reinterpreting its units
    if key == "longitude" and isinstance(mapping[key], dict):
        return None

    if not mapping.get("id") and mapping.get("name") == PROJ_CENTRAL_MERIDIAN:
        # a PROJ-native parameter is not honoured when rebuilding a CRS from its
        # JSON serialization, so round-trip through the PROJ dict instead
        with warnings.catch_warnings():
            # rebuilding via PROJ is lossy by nature, which is not news here
            warnings.simplefilter("ignore", UserWarning)
            proj = crs.to_dict()
            proj[PROJ_CENTRAL_MERIDIAN] = meridian
            return CRS.from_dict(proj)

    # "mapping" is a view onto "crs_json", so this mutates the serialization
    mapping[key] = meridian

    return CRS.from_json_dict(crs_json)


def to_wkt(mesh: pv.PolyData, crs: CRS) -> None:
    """Attach serialized :class:`~pyproj.crs.CRS` as Well-Known-Text (WKT) to the mesh.

    The serialized OGC WKT is attached to the ``field_data`` of the mesh in-place.

    Parameters
    ----------
    mesh : :class:`~pyvista.PolyData`
        The mesh to contain the serialized OGC WKT.
    crs : :class:`~pyproj.crs.CRS`
        The Coordinate Reference System to be serialized.

    Notes
    -----
    .. versionadded:: 0.2.0

    """
    wkt = crs.to_wkt()
    mesh.field_data[GV_FIELD_CRS] = np.array([wkt])
