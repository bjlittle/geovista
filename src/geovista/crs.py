"""Coordinate reference system (CRS) utility functions.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

from typing import Union

import numpy as np
from pyproj import CRS
import pyvista as pv

from .common import GV_FIELD_CRS

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
CRSLike = Union[int, str, dict, CRS]

#: EPSG projection parameter for longitude of natural origin/central meridian
EPSG_CENTRAL_MERIDIAN: str = "8802"

#: WGS84 / Plate Carree (Equidistant Cylindrical)
PlateCarree = CRS.from_user_input("epsg:32662")

#: Geographic WGS84
WGS84 = CRS.from_user_input("epsg:4326")


def from_wkt(mesh: pv.PolyData) -> CRS:
    """Get the :class:`pyproj.CRS` associated with the mesh.

    Parameters
    ----------
    mesh : PolyData
        The mesh containing the pyproj CRS serialized as OGC WKT.

    Returns
    -------
    CRS
        The :class:`pyproj.CRS`

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
    crs : CRS
        The :class:`pyproj.CRS`.

    Returns
    -------
    float
        The central meridian, or ``None`` if the CRS has no such parameter.

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
    mesh : PolyData
        The mesh to be inspected for a serialized CRS.

    Returns
    -------
    bool
        Whether the mesh has a CRS serialized as WKT attached.

    Notes
    -----
    .. versionadded:: 0.4.0

    """
    return GV_FIELD_CRS in mesh.field_data


def projected(mesh: pv.PolyData) -> bool:
    """Determine if the mesh is a planar projection.

    Simple heuristic approach achieved by attempting to inspect the associated CRS of
    the mesh. If the mesh CRS is unavailable then the weaker contract of inspecting the
    mesh geometry is used to detect for a flat plane.

    Parameters
    ----------
    mesh : PolyData
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
    """Replace the longitude of natural origin in the `CRS`.

    The natural origin is also known as the central meridian.

    Note that, the `crs` is immutable, therefore a new instance will be
    returned with the specified central meridian.

    Parameters
    ----------
    crs : CRS
        The :class:`pyproj.CRS`.
    meridian : float
        The replacement central meridian.

    Returns
    -------
    CRS
        The CRS with the specified central meridian, or ``None`` if the CRS
        has no such parameter.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # https://proj.org/development/reference/cpp/operation.html#classosgeo_1_1proj_1_1operation_1_1Conversion_1center_longitude
    result = None
    crs_json = crs.to_json_dict()
    found = False
    if conversion := crs_json.get("conversion"):
        if parameters := conversion.get("parameters"):
            for param in parameters:
                if found := param["id"]["code"] == int(EPSG_CENTRAL_MERIDIAN):
                    param["value"] = meridian
                    break
    if found:
        result = CRS.from_json_dict(crs_json)

    return result


def to_wkt(mesh: pv.PolyData, crs: CRS) -> None:
    """Attach serialized :class:`pyproj.CRS` as Well-Known-Text in-place to the `mesh`.

    The serialized OGC WKT is attached to the ``field_data`` of the mesh.

    Parameters
    ----------
    mesh : PolyData
        The mesh to contain the OGC WKT.
    crs : CRS
        The :class:`pyproj.CRS` to be serialized.

    Notes
    -----
    .. versionadded:: 0.2.0

    """
    wkt = crs.to_wkt()
    mesh.field_data[GV_FIELD_CRS] = np.array([wkt])
