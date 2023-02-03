"""
This module provides coordinate reference system (CRS) utility functions.

Notes
-----
.. versionadded:: 0.1.0

"""
from typing import Optional

from pyproj import CRS
import pyvista as pv

from .common import GV_FIELD_CRS

__all__ = [
    "PlateCarree",
    "WGS84",
    "from_wkt",
    "get_central_meridian",
    "set_central_meridian",
]

#: EPSG projection parameter for longitude of natural origin/central meridian
EPSG_CENTRAL_MERIDIAN: str = "8802"

#: WGS84 / Plate Carree (Equidistant Cylindrical)
PlateCarree = CRS.from_user_input("epsg:32662")

#: Geographic WGS84
WGS84 = CRS.from_user_input("epsg:4326")


def from_wkt(mesh: pv.PolyData) -> CRS:
    """
    Get the :class:`pyproj.CRS` associated with the mesh.

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

    if GV_FIELD_CRS in mesh.field_data:
        wkt = str(mesh.field_data[GV_FIELD_CRS][0])
        crs = CRS.from_wkt(wkt)

    return crs


def get_central_meridian(crs: CRS) -> Optional[float]:
    """
    Get the longitude of natural origin, also known as the central meridian,
    of the CRS.

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


def set_central_meridian(crs: CRS, meridian: float) -> Optional[CRS]:
    """
    Set the longitude of natural origin, also known as the central meridian,
    of the CRS.

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
