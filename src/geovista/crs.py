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
    "EPSG_ANGULAR_UNIT",
    "EPSG_CENTRAL_MERIDIAN",
    "EPSG_CENTRAL_MERIDIAN_ALIASES",
    "EPSG_DEGREE",
    "PROJ_CENTRAL_MERIDIAN",
    "PROJ_ROTATED_POLE",
    "WGS84",
    "CRSLike",
    "PlateCarree",
    "from_wkt",
    "get_central_meridian",
    "has_wkt",
    "planar",
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
    "8833",  # longitude of origin e.g. polar stereographic variant B, krovak
    "8835",  # longitude of topocentric origin e.g. vertical perspective
)
"""EPSG projection parameters that may carry the central meridian.

A projection method defines its longitudinal origin using whichever parameter
suits its geometry, so the central meridian is not always EPSG ``8802``.
Ordered by precedence.

Note that EPSG ``8830`` (initial longitude) is deliberately absent, as it is
the western edge of zone one of a zoned grid system rather than the central
meridian of the projection.
"""

EPSG_DEGREE: str = "degree"
"""PROJ JSON angular unit of a projection parameter expressed in degrees."""

EPSG_ANGULAR_UNIT: str = "AngularUnit"
"""PROJ JSON unit type of a projection parameter measuring an angle."""

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


def _rotated_pole(crs_json: dict[str, Any]) -> bool:
    """Determine whether the `crs_json` describes a rotated pole.

    A rotated pole expresses its origin relative to the rotated pole itself,
    for which a scalar central meridian is not a faithful abstraction.

    Parameters
    ----------
    crs_json : dict
        The Coordinate Reference System serialized as PROJ JSON, as returned by
        :meth:`pyproj.crs.CRS.to_json_dict`.

    Returns
    -------
    bool
        Whether the coordinate operation rotates the pole.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    conversion = crs_json.get("conversion") or {}
    parameters = conversion.get("parameters") or []

    return any(param.get("name") in PROJ_ROTATED_POLE for param in parameters)


def _degrees_per_unit(unit: Any) -> float | None:  # noqa: ANN401
    """Calculate the number of degrees in the angular `unit`.

    Parameters
    ----------
    unit : str or dict or None
        The unit of a projection parameter, as serialized in PROJ JSON.

    Returns
    -------
    float or None
        The degrees per `unit`, or ``None`` if the `unit` is not angular.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if unit is None or unit == EPSG_DEGREE:
        return 1.0

    # a unit other than degrees is serialized as a mapping that quantifies
    # itself in radians e.g. "EPSG:29701" is in grad, of which there are 400
    # in a turn, making its 49 grad longitude of projection centre 44.1 degrees
    if (
        isinstance(unit, dict)
        and unit.get("type") == EPSG_ANGULAR_UNIT
        and (factor := unit.get("conversion_factor"))
    ):
        return float(float(factor) * 180.0 / np.pi)

    return None


def _find_central_meridian(
    crs_json: dict[str, Any],
) -> tuple[dict[str, Any], str, float] | None:
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
    tuple of (dict, str, float) or None
        The mapping holding the central meridian, the key within it, and the
        degrees per unit of the value held there, or ``None`` if the central
        meridian could not be located.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if _rotated_pole(crs_json):
        return None

    conversion = crs_json.get("conversion") or {}
    parameters = conversion.get("parameters") or []

    by_code: dict[str, tuple[dict[str, Any], float]] = {}
    native: tuple[dict[str, Any], float] | None = None

    for param in parameters:
        # a parameter in a non-angular unit is not a longitude at all
        if (degrees := _degrees_per_unit(param.get("unit"))) is None:
            continue

        # a PROJ-native method has no EPSG identifier for its parameters
        code = (param.get("id") or {}).get("code")
        if code is not None:
            by_code[str(code)] = (param, degrees)
        elif param.get("name") == PROJ_CENTRAL_MERIDIAN:
            native = (param, degrees)

    for code in EPSG_CENTRAL_MERIDIAN_ALIASES:
        if (found := by_code.get(code)) is not None:
            param, degrees = found
            return param, "value", degrees

    if native is not None:
        param, degrees = native
        return param, "value", degrees

    # cartopy >=0.26 defines PlateCarree(central_longitude=...) as a geographic
    # CRS shifted by its datum prime meridian, rather than as a conversion
    datum = crs_json.get("datum") or {}
    if (prime_meridian := datum.get("prime_meridian")) is not None:
        return prime_meridian, "longitude", 1.0

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
    crs_json = crs.to_json_dict()
    located = _find_central_meridian(crs_json)

    if located is None:
        # a projection that simply omits its longitudinal origin is centred on
        # 0, which needs no warning - only a rotated pole carries an origin that
        # cannot be expressed as a central meridian at all
        if _rotated_pole(crs_json):
            wmsg = (
                f"geovista is unable to determine the central meridian of the "
                f"{crs.name!r} rotated pole coordinate reference system, and will "
                f"assume 0. A mesh transformed to this CRS may be torn at the "
                f"wrong seam."
            )
            warnings.warn(wmsg, stacklevel=2)
        return None

    mapping, key, degrees = located
    value = mapping[key]

    if key == "longitude":
        # a prime meridian may be expressed in a non-degree angular unit, and a
        # Greenwich prime meridian is not a central meridian
        if isinstance(value, dict):
            return None
        if not value:
            return None

    return float(value) * degrees


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


def planar(crs: CRS) -> bool:
    """Determine whether the `crs` renders a scene as a flat plane.

    A :mod:`geovista` scene is rendered on the surface of a 3D sphere only for
    :data:`WGS84`, and on a flat plane for every other
    :class:`~pyproj.crs.CRS`. This is the same rule applied by
    :func:`geovista.transform.transform_mesh`.

    Note that this asks a different question to :func:`projected`, which
    inspects a *mesh* to determine whether it has already been projected.

    Parameters
    ----------
    crs : :class:`~pyproj.crs.CRS`
        The Coordinate Reference System of the scene.

    Returns
    -------
    bool
        Whether the scene is rendered as a flat plane.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    return crs != WGS84


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

    mapping, key, degrees = located

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

    # "mapping" is a view onto "crs_json", so this mutates the serialization.
    # the value is written back in the unit it was read in, which matters for
    # the legacy grad based national grids e.g. "EPSG:29701"
    mapping[key] = meridian / degrees

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
