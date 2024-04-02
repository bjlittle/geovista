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

from typing import TYPE_CHECKING, TypeAlias

import lazy_loader as lazy
from pyproj import CRS

from .common import GV_FIELD_CRS

if TYPE_CHECKING:
    import pyvista as pv

# lazy import third-party dependencies
np = lazy.load("numpy")

__all__ = [
    "CRSLike",
    "PlateCarree",
    "WGS84",
    "from_wkt",
    "get_central_meridian",
    "has_wkt",
    "projected",
    "set_central_meridian",
    "to_wkt",
]

# type aliases
CRSLike: TypeAlias = int | str | dict | CRS
"""Type alias for a Coordinate Reference System."""

# constants
EPSG_CENTRAL_MERIDIAN: str = "8802"
"""EPSG projection parameter for longitude of natural origin/central meridian."""

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


def get_central_meridian(crs: CRS) -> float | None:
    """Retrieve the longitude of natural origin of the `CRS`.

    THe natural origin is also known as the central meridian.

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
    result = None

    if crs.coordinate_operation is not None:
        params = crs.coordinate_operation.params
        cm_param = list(
            filter(lambda param: param.code == EPSG_CENTRAL_MERIDIAN, params)
        )
        if len(cm_param) == 1:
            (cm_param,) = cm_param
            result = cm_param.value

    return result


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

    Note that, the `crs` is immutable, therefore a new instance will be
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
    result = None
    crs_json = crs.to_json_dict()
    found = False
    if (conversion := crs_json.get("conversion")) and (
        parameters := conversion.get("parameters")
    ):
        for param in parameters:
            if found := param["id"]["code"] == int(EPSG_CENTRAL_MERIDIAN):
                param["value"] = meridian
                break
    if found:
        result = CRS.from_json_dict(crs_json)

    return result


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
