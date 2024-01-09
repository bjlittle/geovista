"""Provision common geovista infra-structure and utilities.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

from collections.abc import Iterable
from enum import Enum
import sys
from typing import Any

import numpy as np
from numpy import ma
from numpy.typing import ArrayLike
import pyvista as pv
from pyvista import _vtk
from pyvista.core.filters import _get_output
from vtk import vtkLogger, vtkObject

__all__ = [
    "BASE",
    "CENTRAL_MERIDIAN",
    "COASTLINES_RESOLUTION",
    "GV_CELL_IDS",
    "GV_FIELD_CRS",
    "GV_FIELD_NAME",
    "GV_FIELD_RADIUS",
    "GV_FIELD_RESOLUTION",
    "GV_FIELD_ZSCALE",
    "GV_POINT_IDS",
    "GV_REMESH_POINT_IDS",
    "LRU_CACHE_SIZE",
    "PERIOD",
    "Preference",
    "RADIUS",
    "REMESH_JOIN",
    "REMESH_SEAM",
    "VTK_CELL_IDS",
    "VTK_POINT_IDS",
    "WRAP_ATOL",
    "WRAP_RTOL",
    "ZLEVEL_SCALE",
    "ZTRANSFORM_FACTOR",
    "cast_UnstructuredGrid_to_PolyData",
    "distance",
    "from_cartesian",
    "nan_mask",
    "point_cloud",
    "sanitize_data",
    "set_jupyter_backend",
    "to_cartesian",
    "to_lonlat",
    "to_lonlats",
    "triangulated",
    "vtk_warnings_off",
    "vtk_warnings_on",
    "wrap",
]

#
# TODO: support richer default management
#

#: Default base for wrapped longitude half-open interval, in degrees.
BASE: float = -180.0

#: Default central meridian.
CENTRAL_MERIDIAN: float = 0.0

#: Default Natural Earth coastline resolution.
COASTLINES_RESOLUTION: str = "10m"

#: Name of the geovista cell indices array.
GV_CELL_IDS: str = "gvOriginalCellIds"

#: The field array name of the CF serialized pyproj CRS.
GV_FIELD_CRS: str = "gvCRS"

#: The field array name of the mesh containing field, point and/or cell data.
GV_FIELD_NAME: str = "gvName"

#: The field array name of the mesh radius.
GV_FIELD_RADIUS: str = "gvRadius"

#: The field array name of the mesh resolution e.g., coastlines.
GV_FIELD_RESOLUTION: str = "gvResolution"

#: The field array name of the mesh proportional multiplier for z-axis levels/offsets.
GV_FIELD_ZSCALE: str = "gvZScale"

#: Name of the geovista point indices array.
GV_POINT_IDS: str = "gvOriginalPointIds"

#: Name of the geovista remesh point indices/marker array.
GV_REMESH_POINT_IDS: str = "gvRemeshPointIds"

#: Default jupyter plotting backend for pyvista.
JUPYTER_BACKEND: str = "trame"

#: LRU cache size, which is auto-disabled for testing
LRU_CACHE_SIZE: int = 0 if "pytest" in sys.modules else 128

#: Default period for wrapped longitude half-open interval, in degrees.
PERIOD: float = 360.0

#: Default radius of a spherical mesh.
RADIUS: float = 1.0

#: Marker for remesh filter cell join point.
REMESH_JOIN: int = -3

#: Marker for remesh filter western cell boundary point.
REMESH_SEAM: int = -1

#: Name of the VTK cell indices array.
VTK_CELL_IDS: str = "vtkOriginalCellIds"

#: Name of the VTK point indices array.
VTK_POINT_IDS: str = "vtkOriginalPointIds"

#: Absolute tolerance for values close to longitudinal wrap base + period.
WRAP_ATOL: float = 1.0e-8

#: Relative tolerance for values close to longitudinal wrap base + period.
WRAP_RTOL: float = 1.0e-5

#: Proportional multiplier for z-axis levels/offsets.
ZLEVEL_SCALE: float = 1.0e-4

#: The zlevel scaling to be applied when transforming to a projection.
ZTRANSFORM_FACTOR: int = 3


class _MixinStrEnum:
    """Convenience behaviour mixin for a string enumeration.

    Notes
    -----
    .. versionadded:: 0.3.0

    """

    @classmethod
    def _missing_(cls, item: str | Preference) -> Preference | None:
        """Handle missing enumeration members.

        Parameters
        ----------
        item : str or Preference
            The candidate preference enumeration member.

        Returns
        -------
        Preference
            The preference member or None if the member is not a valid
            enumeration member.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        item = str(item).lower()
        for member in cls:
            if member.value == item:
                return member
        return None

    @classmethod
    def valid(cls, item: str | Preference) -> bool:
        """Determine whether the provided item is a valid enumeration member.

        Parameters
        ----------
        item : str or Preference
            The candidate preference enumeration member.

        Returns
        -------
        bool
            Whether the preference enumeration member is valid.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        return str(item).lower() in cls.values()

    @classmethod
    def values(cls) -> tuple[str, ...]:
        """List enumeration member values.

        Returns
        -------
        tuple of str
            Tuple of all the valid preference enumeration member values.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        return tuple([member.value for member in cls])

    def __str__(self) -> str:
        """Serialize enumeration name.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        # TODO: remove when minimum supported python version is 3.11
        return f"{self.name.lower()}"


# TODO: use StrEnum and auto when minimum supported python version is 3.11
class Preference(_MixinStrEnum, Enum):
    """Enumeration of common mesh geometry preferences.

    Notes
    -----
    .. versionadded:: 0.3.0

    """

    CELL = "cell"
    POINT = "point"


def active_kernel() -> bool:
    """Determine whether we are executing within an ``IPython`` kernel.

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

        # the following statement may or may not raise an exception
        _ = get_ipython().kernel
    except (AttributeError, ModuleNotFoundError):
        result = False

    return result


def cast_UnstructuredGrid_to_PolyData(
    mesh: pv.UnstructuredGrid,
    clean: bool | None = False,
) -> pv.PolyData:
    """Convert an unstructured grid to a :class:`pyvista.PolyData` instance.

    Parameters
    ----------
    mesh :  UnstructuredGrid
        The unstructured grid to be converted.
    clean : bool, default=False
        Specify whether to merge duplicate points, remove unused points,
        and/or remove degenerate cells in the resultant mesh.

    Returns
    -------
    PolyData
        The resultant mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if not isinstance(mesh, pv.UnstructuredGrid):
        dtype = type(mesh).split(" ")[1][:-1]
        emsg = f"Expected a 'pyvista.UnstructuredGrid', got {dtype}."
        raise TypeError(emsg)

    # see https://vtk.org/pipermail/vtkusers/2011-March/066506.html
    alg = _vtk.vtkGeometryFilter()
    alg.AddInputData(mesh)
    alg.Update()
    result = _get_output(alg)

    if clean:
        result = result.clean()

    return result


def distance(
    mesh: pv.PolyData,
    origin: ArrayLike | None = None,
    mean: bool | None = True,
) -> float | ArrayLike:
    """Calculate the mean distance from the `origin` to the points of the `mesh`.

    Note that, given a spherical `mesh` the distance calculated is the radius.

    Parameters
    ----------
    mesh : PolyData
        The surface that requires its distance to be calculated, relative to
        the `origin`.
    origin : ArrayLike, default=(0, 0, 0)
        The (x, y, z) cartesian center of the spheroid mesh.
    mean : bool, default=True
        Calculate the mean distance to the points of the `mesh`. Otherwise, calculate
        the distance to each point from the `origin`.

    Returns
    -------
    float or ArrayLike
        The mean distance to the provided mesh or each mesh point.

    Notes
    -----
    .. versionadded: 0.1.0

    """
    if origin is None:
        origin = np.array([0, 0, 0])

    origin = np.atleast_1d(origin)

    if origin.ndim != 1 or origin.size != 3:
        emsg = (
            f"Require an (x, y, z) cartesian point for the origin, got {origin.shape} "
            "instead."
        )
        raise ValueError(emsg)

    pts = mesh.points - origin
    result = np.sqrt(np.sum(pts * pts, axis=1))

    if mean:
        result = np.mean(result)

        given_radius = (
            mesh.field_data[GV_FIELD_RADIUS][0]
            if GV_FIELD_RADIUS in mesh.field_data
            else RADIUS
        )

        if np.isclose(result, given_radius):
            result = given_radius

    return result


def from_cartesian(
    mesh: pv.PolyData,
    stacked: bool | None = True,
    closed_interval: bool | None = False,
    rtol: float | None = None,
    atol: float | None = None,
) -> np.ndarray:
    """Convert cartesian ``xyz`` spherical `mesh` to geographic longitude and latitude.

    Parameters
    ----------
    mesh : PolyData
        The mesh containing the cartesian (x, y, z) points to be converted to
        longitude and latitude coordinates.
    stacked : bool, default=True
        Specify whether the resultant xy0 coordinates have shape (N, 3).
        Otherwise, they will have shape (3, N).
    closed_interval : bool, default=False
        Longitude values will be in the half-closed interval [-180, 180). However,
        if the mesh has a seam at the 180th meridian and `closed_interval`
        is ``True``, then longitudes will be in the closed interval [-180, 180].
    rtol : float, optional
        The relative tolerance for values close to longitudinal
        :func:`geovista.common.wrap` base + period.
    atol : float, optional
        The absolute tolerance for values close to longitudinal
        :func:`geovista.common.wrap` base + period.

    Returns
    -------
    ndarray
        The longitude and latitude coordinates, in degrees.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    cloud = point_cloud(mesh)
    radius = distance(mesh, mean=not cloud)

    lons, lats = to_lonlats(
        mesh.points, radius=radius, stacked=False, rtol=rtol, atol=atol
    )

    zlevel = np.zeros_like(lons)

    if cloud:
        if GV_FIELD_RADIUS in mesh.field_data and GV_FIELD_ZSCALE in mesh.field_data:
            # field data injected by geovista.bridge.Transform.from_points
            base = mesh[GV_FIELD_RADIUS][0]
            zscale = mesh[GV_FIELD_ZSCALE][0]
            zlevel = (radius - base) / (base * zscale)

    data = [lons, lats, zlevel]

    # XXX: manage pole longitudes. an alternative future scheme could be more
    # generic and inclusive, but this approach tackles the main use case for now
    # TODO: refactor this into a separate function
    pole_pids = np.where(np.isclose(np.abs(lats), 90))[0]
    if pole_pids.size:
        # enforce a common longitude for pole singularities
        # TODO: review this strategy
        lons[pole_pids] = 0

        if (
            mesh.n_points
            and {0, mesh.n_points - 1} == set(pole_pids)
            and np.unique(lons[1:-1]).size == 1
        ):
            # unfold polar end-points of a meridian i.e., a line of constant longitude
            lons[0] = lons[-1] = lons[1]
        else:
            pole_submesh = mesh.extract_points(pole_pids)
            pole_pids = set(pole_pids)
            # get the cids (cell-indices) of mesh cells with polar vertices
            pole_cids = np.unique(pole_submesh["vtkOriginalCellIds"])
            for cid in pole_cids:
                # get the pids (point-indices) of the polar cell points
                # XXX: pyvista 0.38.0: cell_point_ids(cid) -> get_cell(cid).point_ids
                cell_pids = np.array(mesh.get_cell(cid).point_ids)
                # unfold polar quad-cells
                if len(cell_pids) == 4:
                    # identify the pids of the cell on the pole
                    cell_pole_pids = pole_pids.intersection(cell_pids)
                    # criterion of exactly two points from the quad-cell
                    # at the pole to unfold the polar points longitudes
                    if len(cell_pole_pids) == 2:
                        # compute the relative offset of the polar points
                        # within the polar cell connectivity
                        offset = sorted(
                            [np.where(cell_pids == pid)[0][0] for pid in cell_pole_pids]
                        )
                        if offset == [0, 1]:
                            lhs = cell_pids[offset]
                            rhs = cell_pids[[3, 2]]
                        elif offset == [1, 2]:
                            lhs = cell_pids[offset]
                            rhs = cell_pids[[0, 3]]
                        elif offset == [2, 3]:
                            lhs = cell_pids[offset]
                            rhs = cell_pids[[1, 0]]
                        elif offset == [0, 3]:
                            lhs = cell_pids[offset]
                            rhs = cell_pids[[1, 2]]
                        else:
                            emsg = (
                                "Failed to unfold a mesh polar quad-cell. Invalid "
                                "polar points connectivity detected."
                            )
                            raise ValueError(emsg)
                        lons[lhs] = lons[rhs]

    if closed_interval:
        if GV_REMESH_POINT_IDS in mesh.point_data:
            seam_ids = np.where(mesh[GV_REMESH_POINT_IDS] == REMESH_SEAM)[0]
            seam_lons = lons[seam_ids]
            seam_mask = np.isclose(np.abs(seam_lons), 180)
            lons[seam_ids[seam_mask]] = 180
        elif mesh.n_lines:
            # TODO: unify closed interval strategies for lines and cells
            poi_mask = np.isclose(np.abs(lons), 180)

            if np.any(poi_mask):
                poi_pids = np.arange(lons.size)[poi_mask]
                poi_cells = cast_UnstructuredGrid_to_PolyData(
                    mesh.extract_points(poi_pids)
                )
                cell_pids = [
                    mesh.get_cell(cid).point_ids
                    for cid in poi_cells["vtkOriginalCellIds"]
                ]
                mask_positive = lons[cell_pids] > 0
                if np.any(mask_positive):
                    select_mask = np.sum(mask_positive, axis=1).astype(bool)
                    select_pids = np.asanyarray(cell_pids)[select_mask]
                    pids = select_pids[~mask_positive[select_mask]]

                    lons[pids] = 180

    result = np.vstack(data).T if stacked else np.array(data)

    return result


def nan_mask(data: ArrayLike) -> np.ndarray:
    """Replace any masked array values with NaNs.

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
            data = ma.asanyarray(data, dtype=float)

        data = data.filled(np.nan)

    return data


def point_cloud(mesh: pv.PolyData) -> bool:
    """Determine whether the `mesh` is a point-cloud.

    Parameters
    ----------
    mesh : PolyData
        The :class:`pyvista.PolyData` mesh.

    Returns
    -------
    bool
        Whether the `mesh` is a point-cloud.

    Notes
    -----
    .. versionadded:: 0.2.0

    """
    return (mesh.n_points == mesh.n_cells) and (mesh.n_lines == 0)


def sanitize_data(
    *meshes: Any,
) -> None:
    """Purge standard VTK helper cell and point data index arrays.

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


def set_jupyter_backend(backend: str | None = None) -> bool:
    """Configure the jupyter plotting backend for pyvista.

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
            pass

    return result


def to_cartesian(
    lons: ArrayLike,
    lats: ArrayLike,
    radius: float | None = None,
    zlevel: float | ArrayLike | None = None,
    zscale: float | None = None,
    stacked: bool | None = True,
) -> np.ndarray:
    """Convert geographic longitudes and latitudes to cartesian ``xyz`` points.

    Parameters
    ----------
    lons : ArrayLike
        The longitude values (degrees) to be converted.
    lats : ArrayLike
        The latitude values (degrees) to be converted.
    radius : float, optional
        The radius of the sphere. Defaults to :data:`RADIUS`.
    zlevel : float or ArrayLike, default=0.0
        The z-axis level. Used in combination with the `zscale` to offset the
        `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
        If `zlevel` is not a scalar, then its shape must match or broadcast
        with the shape of `lons` and `lats`.
    zscale : float, optional
        The proportional multiplier for z-axis `zlevel`. Defaults to
        :data:`ZLEVEL_SCALE`.
    stacked : bool, default=True
        Specify whether the resultant xyz points have shape (N, 3).
        Otherwise, they will have shape (3, N).

    Returns
    -------
    ndarray
        The ``xyz`` spherical cartesian points.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    lons = np.asanyarray(lons)
    lats = np.asanyarray(lats)

    if (shape := lons.shape) != lats.shape:
        emsg = (
            f"Require longitudes and latitudes with same shape, got {shape} and "
            f"{lats.shape} respectively."
        )
        raise ValueError(emsg)

    if (ndim := lons.ndim) > 3:
        emsg = f"Require at most 3-D longitudes and latitudes, got {ndim}-D instead."
        raise ValueError(emsg)

    radius = RADIUS if radius is None else abs(float(radius))
    zscale = ZLEVEL_SCALE if zscale is None else float(zscale)
    # cast as float here, as from_cartesian use-case results in float zlevels
    # that should be dtype preserved for the purpose of precision
    zlevel = np.array([0.0]) if zlevel is None else np.atleast_1d(zlevel).astype(float)

    try:
        _ = np.broadcast_shapes(zshape := zlevel.shape, shape)
    except ValueError as err:
        emsg = (
            f"Cannot broadcast zlevel with shape {zshape} to longitude/latitude"
            f"shape {shape}."
        )
        raise ValueError(emsg) from err

    radius += radius * zlevel * zscale

    x_rad = np.radians(lons)
    y_rad = np.radians(90.0 - lats)
    x = np.ravel(radius * np.sin(y_rad) * np.cos(x_rad))
    y = np.ravel(radius * np.sin(y_rad) * np.sin(x_rad))
    z = np.ravel(radius * np.cos(y_rad))
    xyz = [x, y, z]
    xyz = np.vstack(xyz).T if stacked else np.array(xyz)

    return xyz


def to_lonlat(
    xyz: ArrayLike,
    radians: bool | None = False,
    radius: float | None = None,
    rtol: float | None = None,
    atol: float | None = None,
) -> np.ndarray:
    """Convert cartesian `xyz` point on sphere to geographic longitude and latitude.

    Parameters
    ----------
    xyz : ArrayLike
        The cartesian (x, y, z) point to be converted.
    radians : bool, default=False
        Convert resultant longitude and latitude values to radians.
        Default units are degrees.
    radius : float, optional
        The `radius` of the sphere. Defaults to :data:`RADIUS`.
    rtol : float, optional
        The relative tolerance for values close to longitudinal
        :func:`geovista.common.wrap` base + period.
    atol : float, optional
        The absolute tolerance for values close to longitudinal
        :func:`geovista.common.wrap` base + period.

    Returns
    -------
    ndarray
        The longitude and latitude values.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    point = np.asanyarray(xyz)

    if point.shape != (3,):
        shape = f" with shape {point.shape}" if point.shape else ""
        emsg = (
            "Require a 1-D array of (x, y, z) points, got a "
            f"{point.ndim}-D array{shape}."
        )
        raise ValueError(emsg)

    (result,) = to_lonlats(point, radians=radians, radius=radius, rtol=rtol, atol=atol)

    return result


def to_lonlats(
    xyz: ArrayLike,
    radians: bool | None = False,
    radius: float | ArrayLike | None = None,
    stacked: bool | None = True,
    rtol: float | None = None,
    atol: float | None = None,
) -> np.ndarray:
    """Convert cartesian `xyz` points on sphere to geographic longitudes and latitudes.

    Parameters
    ----------
    xyz : ArrayLike
        The cartesian (x, y, z) points to be converted.
    radians : bool, default=False
        Convert resultant longitude and latitude values to radians.
        Default units are degrees.
    radius : float or ArrayLike, optional
        The `radius` of the sphere. If `radius` is not a scalar, then its shape must
        match the number of `xyz` points i.e., radii with shape ``(N,)`` for `xyz`
        points with shape ``(N, 3)``. Defaults to :data:`RADIUS`.
    stacked : bool, default=True
        Default the resultant shape to be ``(N, 2)``, otherwise ``(2, N)``.
    rtol : float, optional
        The relative tolerance for values close to longitudinal
        :func:`geovista.common.wrap` base + period.
    atol : float, optional
        The absolute tolerance for values close to longitudinal
        :func:`geovista.common.wrap` base + period.

    Returns
    -------
    ndarray
        The longitude and latitude values.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    points = np.atleast_2d(xyz)

    if points.ndim != 2 or points.shape[1] != 3:
        emsg = (
            "Require a 2-D array of (x, y, z) points, got a "
            f"{points.ndim}-D array with shape {points.shape}."
        )
        raise ValueError(emsg)

    if radius is None:
        radius = RADIUS

    radius = np.abs(np.atleast_1d(radius).astype(float))

    if radius.shape != (1,) and (
        radius.ndim != 1 or radius.shape[0] != points.shape[0]
    ):
        emsg = (
            f"Require a 1-D array of radii, got a {radius.ndim}-D array with shape "
            f"{radius.shape}."
        )
        raise ValueError(emsg)

    base, period = (np.radians(BASE), np.radians(PERIOD)) if radians else (BASE, PERIOD)

    lons = np.arctan2(points[:, 1], points[:, 0])
    if not radians:
        lons = np.degrees(lons)
    lons = wrap(lons, base=base, period=period, rtol=rtol, atol=atol)

    z_radius = points[:, 2] / radius
    # XXX: defensive clobber of values outside arcsin domain [-1, 1]
    # which is the result of floating point inaccuracies at the extremes
    if indices := np.where(z_radius > 1):
        z_radius[indices] = 1.0
    if indices := np.where(z_radius < -1):
        z_radius[indices] = -1.0
    lats = np.arcsin(z_radius)
    if not radians:
        lats = np.degrees(lats)

    data = [lons, lats]
    result = np.vstack(data).T if stacked else np.array(data)

    return result


def triangulated(surface: pv.PolyData) -> bool:
    """Determine whether the provided mesh is triangulated.

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


def vtk_warnings_off() -> None:
    """Disable :mod:`vtk` warning messages.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    vtkObject.GlobalWarningDisplayOff()
    # https://gitlab.kitware.com/vtk/vtk/-/issues/18785
    vtkLogger.SetStderrVerbosity(vtkLogger.VERBOSITY_OFF)


def vtk_warnings_on() -> None:
    """Enable :mod:`vtk` warning messages.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    vtkObject.GlobalWarningDisplayOn()
    # https://gitlab.kitware.com/vtk/vtk/-/issues/18785
    vtkLogger.SetStderrVerbosity(vtkLogger.VERBOSITY_INFO)


def wrap(
    lons: ArrayLike,
    base: float | None = None,
    period: float | None = None,
    rtol: float | None = None,
    atol: float | None = None,
    dtype: np.dtype | None = None,
) -> np.ndarray:
    """Transform longitudes to be in the half-open interval [base, base + period).

    Parameters
    ----------
    lons : ArrayLike
        One or more longitude values to be wrapped in the interval.
    base : float, optional
        The start limit of the half-open interval. Defaults to :data:`BASE`.
    period : float, optional
        The end limit of the half-open interval expressed as a length
        from the `base`, in the same units. Defaults to :data:`PERIOD`.
    rtol : float, optional
        The relative tolerance for values close to longitudinal wrap
        base + period. Defaults to :data:`WRAP_RTOL`.
    atol : float, optional
        The absolute tolerance for values close to longitudinal wrap
        base + period. Defaults to :data:`WRAP_ATOL`.
    dtype : data-type, default=float64
        The resultant longitude `dtype`.

    Returns
    -------
    ndarray
        The transformed longitude values.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if not isinstance(lons, Iterable):
        lons = [lons]

    if base is None:
        base = BASE

    if period is None:
        period = PERIOD

    if rtol is None:
        rtol = WRAP_RTOL

    if atol is None:
        atol = WRAP_ATOL

    if dtype is None:
        dtype = np.float64

    lons = np.asanyarray(lons, dtype=dtype)
    result = ((lons - base + period * 2) % period) + base

    mask = np.isclose(result, base + period, rtol=rtol, atol=atol)
    if np.any(mask):
        # snap to the base for values within tolerances
        result[mask] = base

    return result
