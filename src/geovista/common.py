# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Provision common geovista infra-structure and utilities.

Notes
-----
.. versionadded:: 0.1.0

"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
import importlib
import math
import pkgutil
import sys
from typing import TYPE_CHECKING, Literal

import lazy_loader as lazy

from .units import _angle, _angle_array, _lonlats

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    import numpy as np
    from numpy.typing import ArrayLike, DTypeLike, NDArray
    import pyvista as pv

    from .globe import Globe
    from .units import Quantity

# lazy import third-party dependencies
np = lazy.load("numpy")
pv = lazy.load("pyvista")
vtk = lazy.load("vtk")

__all__ = [
    "BASE",
    "CENTRAL_MERIDIAN",
    "COASTLINES_RESOLUTION",
    "GV_CELL_IDS",
    "GV_FIELD_CRS",
    "GV_FIELD_GLOBE_EXAGGERATION_ABOVE",
    "GV_FIELD_GLOBE_EXAGGERATION_BELOW",
    "GV_FIELD_GLOBE_RADIUS",
    "GV_FIELD_GLOBE_RENDER_RADIUS",
    "GV_FIELD_NAME",
    "GV_FIELD_RADIUS",
    "GV_FIELD_RESOLUTION",
    "GV_FIELD_ZSCALE",
    "GV_MANIFOLD_CELL_IDS",
    "GV_POINT_HEIGHT",
    "GV_POINT_IDS",
    "GV_POINT_ZLEVEL",
    "GV_REMESH_POINT_IDS",
    "JUPYTER_BACKEND",
    "LRU_CACHE_SIZE",
    "PERIOD",
    "RADIUS",
    "REMESH_JOIN",
    "REMESH_SEAM",
    "RETIRED_FIELDS",
    "VTK_CELL_IDS",
    "VTK_POINT_IDS",
    "WRAP_ATOL",
    "WRAP_RTOL",
    "ZLEVEL_SCALE",
    "ZTRANSFORM_FACTOR",
    "Preference",
    "RetiredField",
    "StrEnumPlus",
    "Vector2DLike",
    "Vector3DLike",
    "VectorLike",
    "active_kernel",
    "cast_UnstructuredGrid_to_PolyData",
    "distance",
    "from_cartesian",
    "get_modules",
    "nan_mask",
    "point_cloud",
    "sanitize",
    "sanitize_legacy",
    "sanitize_vtk",
    "set_jupyter_backend",
    "to_cartesian",
    "to_lonlat",
    "to_lonlats",
    "triangulated",
    "vectors_to_cartesian",
    "vtk_warnings_off",
    "vtk_warnings_on",
    "wrap",
]

type Vector2DLike = tuple[ArrayLike, ArrayLike]
"""Type alias for 2D vector components."""

type Vector3DLike = tuple[ArrayLike, ArrayLike, ArrayLike]
"""Type alias for 3D vector components."""

type VectorLike = Vector2DLike | Vector3DLike
"""Type alias for 2D or 3D vector components."""

# TODO @bjlittle: support richer default management

BASE: float = -180.0
"""Default base for wrapped longitude half-open interval, in degrees."""

CENTRAL_MERIDIAN: float = 0.0
"""Default central meridian."""

COASTLINES_RESOLUTION: str = "10m"
"""Default Natural Earth coastline resolution."""

GV_CELL_IDS: str = "gvOriginalCellIds"
"""Name of the geovista cell indices array."""

GV_FIELD_CRS: str = "gvCRS"
"""The field array name of the OGC WKT of the mesh CRS.

A WKT holding a non-ASCII character or a backslash is escaped, and the array then
has a second element naming the codec, see :func:`geovista.crs.to_wkt`.
"""

GV_FIELD_GLOBE_EXAGGERATION_ABOVE: str = "gvGlobeExaggerationAbove"
"""The field array name of the factor for heights above sea level of the mesh globe.

See :class:`geovista.globe.Globe`.
"""

GV_FIELD_GLOBE_EXAGGERATION_BELOW: str = "gvGlobeExaggerationBelow"
"""The field array name of the factor for depths below sea level of the mesh globe.

See :class:`geovista.globe.Globe`.
"""

GV_FIELD_GLOBE_RADIUS: str = "gvGlobeRadius"
"""The field array name of the radius of the mesh globe, in metres.

See :class:`geovista.globe.Globe`.
"""

GV_FIELD_GLOBE_RENDER_RADIUS: str = "gvGlobeRenderRadius"
"""The field array name of the radius the mesh globe is drawn at.

See :class:`geovista.globe.Globe`.
"""

GV_FIELD_NAME: str = "gvName"
"""The field array name of the mesh containing field, point and/or cell data."""

GV_FIELD_RADIUS: str = "gvRadius"
"""The field array name of the mesh radius.

Retired, and last written by release 0.5.3, since 0.6 records the globe of a
mesh in its place. See :data:`RETIRED_FIELDS`.
"""

GV_FIELD_RESOLUTION: str = "gvResolution"
"""The field array name of the mesh resolution e.g., coastlines."""

GV_FIELD_ZSCALE: str = "gvZScale"
"""The field array name of the mesh proportional multiplier for z-axis levels."""

GV_MANIFOLD_CELL_IDS: str = "gvManifoldCellIds"
"""Name of the geovista manifold cell indices/marker array."""

GV_POINT_HEIGHT: str = "gvHeight"
"""Name of the point array of heights, in metres above mean sea level.

A float64 array of one height for each point, NaN where a height is missing. See
:attr:`geovista.accessor.GeoVistaAccessor.height`, which reads it.
"""

GV_POINT_IDS: str = "gvOriginalPointIds"
"""Name of the geovista point indices array."""

GV_POINT_ZLEVEL: str = "gvZLevel"
"""Name of the point array of z-axis levels a point cloud carries in a planar CRS."""

GV_REMESH_POINT_IDS: str = "gvRemeshPointIds"
"""Name of the geovista remesh point indices/marker array."""

JUPYTER_BACKEND: str = "trame"
"""Default jupyter plotting backend for pyvista."""

LRU_CACHE_SIZE: int = 0 if "pytest" in sys.modules else 128
"""LRU cache size, which is auto-disabled for testing."""

PERIOD: float = 360.0
"""Default period for wrapped longitude half-open interval, in degrees."""

RADIUS: float = 1.0
"""Default radius of a spherical mesh."""

REMESH_JOIN: int = -3
"""Marker for remesh filter cell join point."""

REMESH_SEAM: int = -1
"""Marker for remesh filter western cell boundary point."""

VTK_CELL_IDS: str = "vtkOriginalCellIds"
"""Name of the VTK cell indices array."""

VTK_POINT_IDS: str = "vtkOriginalPointIds"
"""Name of the VTK point indices array."""

WRAP_ATOL: float = 1.0e-8
"""Absolute tolerance for longitudes close to 'wrap meridian'."""

WRAP_RTOL: float = 1.0e-5
"""Relative tolerance for longitudes close to 'wrap meridian'."""

ZLEVEL_SCALE: float = 1.0e-4
"""Proportional multiplier for z-axis levels/offsets."""

ZTRANSFORM_FACTOR: int = 3
"""The zlevel scaling to be applied when transforming to a projection."""

_GV_SANITIZE: list[str] = [
    GV_CELL_IDS,
    GV_MANIFOLD_CELL_IDS,
    GV_POINT_IDS,
    GV_REMESH_POINT_IDS,
]

_VTK_SANITIZE: list[str] = [
    VTK_CELL_IDS,
    VTK_POINT_IDS,
]


class StrEnumPlus(StrEnum):
    """Convenience behaviour for a string enumeration.

    Notes
    -----
    .. versionadded:: 0.6.0

    Previously called MixinStrEnum.

    """

    @classmethod
    def _missing_(cls, value: object) -> StrEnumPlus | None:
        """Handle missing enumeration members.

        Parameters
        ----------
        value : object
            The candidate preference enumeration member. Expected to be str or
            StrEnumPlus instance, but could be any object.

        Returns
        -------
        StrEnumPlus
            The enum member or None if the member is not a valid
            enumeration member.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        value_string = str(value).lower()
        for member in cls:
            if member.value == value_string:
                return member
        return None

    @classmethod
    def valid(cls, item: str | StrEnumPlus) -> bool:
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
        return tuple(member.value for member in cls)


class Preference(StrEnumPlus):
    """Enumeration of common mesh geometry preferences.

    Notes
    -----
    .. versionadded:: 0.3.0

    """

    CELL = "cell"
    """Preference for cell geometry."""
    POINT = "point"
    """Preference for point geometry."""


@dataclass(frozen=True)
class RetiredField:
    """A field that geovista reads, but no longer writes.

    Notes
    -----
    .. versionadded:: 0.6.0

    """

    name: str
    """The name of the field."""

    association: Literal["field", "point", "cell"]
    """Whether the field is field, point or cell data."""

    replacement: str
    """What replaced the field."""

    last_written: str
    """The last release of geovista that wrote the field."""

    translate: Callable[[pv.DataSet], None]
    """Write what replaced the field onto a mesh that has it, in place."""


def _translate_radius(mesh: pv.DataSet) -> None:
    """Record the globe a mesh's ``gvRadius`` gives, in place.

    A globe the mesh already records wins over its ``gvRadius``.

    Parameters
    ----------
    mesh : pyvista.DataSet
        The mesh, with a ``gvRadius``.

    """
    # geovista.globe imports this module
    from .globe import Globe  # noqa: PLC0415

    globe = Globe.from_mesh(mesh)
    if globe is not None:
        globe.to_mesh(mesh)


RETIRED_FIELDS: tuple[RetiredField, ...] = (
    RetiredField(
        name=GV_FIELD_RADIUS,
        association="field",
        replacement=(
            "the globe, in gvGlobeRadius, gvGlobeRenderRadius, "
            "gvGlobeExaggerationAbove and gvGlobeExaggerationBelow"
        ),
        last_written="0.5.3",
        translate=_translate_radius,
    ),
)
"""Every field that geovista reads, but no longer writes.

See :func:`sanitize_legacy`, which translates and removes them.
"""

#: The four fields a mesh records its globe in, which a globe reads and writes by name.
_GV_GLOBE_FIELDS: tuple[str, str, str, str] = (
    GV_FIELD_GLOBE_RADIUS,
    GV_FIELD_GLOBE_RENDER_RADIUS,
    GV_FIELD_GLOBE_EXAGGERATION_ABOVE,
    GV_FIELD_GLOBE_EXAGGERATION_BELOW,
)


def _retired(mesh: pv.DataSet) -> bool:
    """Determine whether a mesh has any field of :data:`RETIRED_FIELDS`.

    Parameters
    ----------
    mesh : pyvista.DataSet
        The mesh.

    Returns
    -------
    bool
        Whether the mesh has a retired field.

    """
    return any(
        entry.name in getattr(mesh, f"{entry.association}_data")
        for entry in RETIRED_FIELDS
    )


def _current[MeshT: pv.DataSet](result: MeshT, given: pv.DataSet, /) -> MeshT:
    """Return a mesh made from another, carrying only current fields.

    A retired field is translated and removed, on a copy when the mesh is the
    one given, so that a mesh given only to read is never changed.

    Parameters
    ----------
    result : pyvista.DataSet
        The mesh a function returns.
    given : pyvista.DataSet
        The mesh the function was given.

    Returns
    -------
    pyvista.DataSet
        The mesh to return, of the type of `result`.

    """
    if _retired(result):
        if result is given:
            result = result.copy()
        sanitize_legacy(result)

    return result


def active_kernel() -> bool:
    """Determine whether we are executing within an ``IPython`` kernel.

    Returns
    -------
    bool
        Whether there is an active ``IPython`` kernel.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    result = True

    try:
        from IPython import get_ipython  # noqa: PLC0415

        # the following statement may or may not raise an exception
        _ = get_ipython().kernel
    except (AttributeError, ModuleNotFoundError):
        result = False

    return result


def cast_UnstructuredGrid_to_PolyData(  # noqa: N802
    mesh: pv.DataSet,
    /,
    *,
    clean: bool | None = False,
) -> pv.PolyData:
    """Convert a :class:`~pyvista.UnstructuredGrid` to a :class:`~pyvista.PolyData`.

    Parameters
    ----------
    mesh : :class:`~pyvista.DataSet`
        The unstructured grid to be converted. Any other kind of dataset raises
        :class:`TypeError`.
    clean : bool, default=False
        Specify whether to merge duplicate points, remove unused points,
        and/or remove degenerate cells in the resultant mesh. See
        :meth:`pyvista.PolyDataFilters.clean`.

    Returns
    -------
    :class:`~pyvista.PolyData`
        The resultant mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if not isinstance(mesh, pv.UnstructuredGrid):
        emsg = f"Expected a 'pyvista.UnstructuredGrid', got '{type(mesh).__name__}'."
        raise TypeError(emsg)

    alg = pv._vtk.vtkGeometryFilter()  # noqa: SLF001
    alg.AddInputData(mesh)
    alg.Update()
    result = pv.PolyData(alg.GetOutput())
    result.copy_meta_from(mesh, deep=True)

    if clean:
        result = result.clean()

    return _current(result, mesh)


def distance(
    mesh: pv.PolyData,
    /,
    *,
    origin: ArrayLike | None = None,
    mean: bool | None = True,
) -> float | np.ndarray:
    """Calculate the mean distance from the `origin` to the points of the `mesh`.

    Note that given a spherical `mesh` the distance calculated is the radius.

    Parameters
    ----------
    mesh : :class:`~pyvista.PolyData`
        The surface that requires its distance to be calculated, relative to
        the `origin`.
    origin : :data:`~numpy.typing.ArrayLike`, default=(0, 0, 0)
        The (x, y, z) cartesian center of the spheroid mesh.
    mean : bool, default=True
        Calculate the mean distance to the points of the `mesh`. Otherwise, calculate
        the distance to each point from the `origin`.

    Returns
    -------
    float or :class:`~numpy.ndarray`
        The mean distance to the provided mesh or each mesh point.

    Notes
    -----
    .. versionadded:: 0.1.0

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
    result: float | np.ndarray = np.sqrt(np.sum(pts * pts, axis=1))

    if mean:
        result = np.mean(result)

        # geovista.globe imports this module
        from .globe import Globe  # noqa: PLC0415

        globe = Globe.from_mesh(mesh)
        given_radius = RADIUS if globe is None else globe.render_radius

        if np.isclose(result, given_radius):
            result = given_radius

    return result


def from_cartesian(
    mesh: pv.PolyData,
    /,
    *,
    stacked: bool | None = True,
    closed_interval: bool | None = False,
    rtol: float | None = None,
    atol: float | None = None,
) -> np.ndarray:
    """Convert cartesian ``xyz`` spherical `mesh` to geographic longitude and latitude.

    Parameters
    ----------
    mesh : :class:`~pyvista.PolyData`
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
        The relative tolerance for longitudes close to the 'wrap meridian' -
        see :func:`geovista.common.wrap` for more.
    atol : float, optional
        The absolute tolerance for longitudes close to the 'wrap meridian' -
        see :func:`geovista.common.wrap` for more.

    Returns
    -------
    :class:`~numpy.ndarray`
        The longitude and latitude coordinates, in degrees.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    cloud = point_cloud(mesh)
    radius = distance(mesh, mean=False)

    if not cloud:
        # the mean the points measure, as distance snaps it to the globe the mesh
        # records, which a lift smaller than that snap leaves the points off
        mean = np.mean(radius)
        # a surface at one radius, to the precision of its points, is read at
        # that radius, which gives the points of a parallel one latitude. One
        # at uneven radii is read at the radius of each point, or a point off
        # the mean would take the wrong latitude. Points kept as integers are
        # exact, so their radii carry only the rounding of the float64 distance
        dtype = mesh.points.dtype
        if not np.issubdtype(dtype, np.floating):
            dtype = np.dtype(np.float64)
        resolution = float(np.finfo(dtype).resolution)
        if np.allclose(radius, mean, rtol=resolution, atol=0):
            radius = mean

    lons, lats = _to_lonlats(
        mesh.points, radius=radius, stacked=False, rtol=rtol, atol=atol
    )

    zlevel = np.zeros_like(lons)

    base = None

    if cloud:
        # geovista.globe imports this module
        from .globe import Globe  # noqa: PLC0415

        globe = Globe.from_mesh(mesh)
        base = None if globe is None else globe.render_radius

    # a mesh with heights carries no z-level, so its radii encode none
    # (heights spec §2 decision 8)
    if (
        base is not None
        and GV_FIELD_ZSCALE in mesh.field_data
        and GV_POINT_HEIGHT not in mesh.point_data
    ):
        # field data injected by geovista.bridge.Transform.from_points
        zscale = mesh[GV_FIELD_ZSCALE][0]
        zlevel = (radius - base) / (base * zscale)

    data = [lons, lats, zlevel]

    # TODO @bjlittle: Manage pole longitudes. an alternative future scheme could be
    #                 more generic and inclusive, but this approach tackles the main
    #                 use case for now.

    # TODO @bjlittle: Refactor this into a separate function.
    pole_pids = np.where(np.isclose(np.abs(lats), 90))[0]
    if pole_pids.size:
        # enforce a common longitude for pole singularities
        # TODO @bjlittle: Review this strategy.
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
            if pole_submesh.n_cells:
                pole_pids = set(pole_pids)
                # get the cids (cell-indices) of mesh cells with polar vertices
                pole_cids = np.unique(pole_submesh[VTK_CELL_IDS])
                for cid in pole_cids:
                    # get the pids (point-indices) of the polar cell points
                    # NOTE:
                    # pyvista 0.38.0: cell_point_ids(cid) -> get_cell(cid).point_ids
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
                                [
                                    np.where(cell_pids == pid)[0][0]
                                    for pid in cell_pole_pids
                                ]
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
            # TODO @bjlittle: Unify closed interval strategies for lines and cells.
            poi_mask = np.isclose(np.abs(lons), 180)

            if np.any(poi_mask):
                poi_pids = np.arange(lons.size)[poi_mask]
                poi_cells = cast_UnstructuredGrid_to_PolyData(
                    mesh.extract_points(poi_pids)
                )
                poi_cell_pids = [
                    mesh.get_cell(cid).point_ids for cid in poi_cells[VTK_CELL_IDS]
                ]
                mask_positive = lons[poi_cell_pids] > 0
                if np.any(mask_positive):
                    select_mask = np.sum(mask_positive, axis=1).astype(bool)
                    select_pids = np.asanyarray(poi_cell_pids)[select_mask]
                    pids = select_pids[~mask_positive[select_mask]]

                    lons[pids] = 180

    return np.vstack(data).T if stacked else np.array(data)


def get_modules(root: str, /, *, base: bool | None = True) -> list[str]:
    """Find all submodule names relative to the `root` package.

    Recursively searches down from the `root` to find all child (leaf) modules.

    The names of the modules will be relative to the `root`.

    Parameters
    ----------
    root : str
        The name (dot notation) of the top level package to search under.
        e.g., ``geovista.examples``.
    base : bool, optional
        Flag the top level `root` package, which will then remove the `root` prefix
        from all packages found and sort them alphabetically.

    Returns
    -------
    list of str
        The sorted list of child module names, relative to the `root`.

    Notes
    -----
    .. versionadded:: 0.5.0

    """
    modules: list[str] = []
    pkgs: list[str] = []

    for info in pkgutil.iter_modules(importlib.import_module(root).__path__):
        name = f"{root}.{info.name}"
        container = pkgs if info.ispkg else modules
        container.append(name)

    for pkg in pkgs:
        modules.extend(get_modules(pkg, base=False))

    if base:
        modules = sorted([name.split(f"{root}.")[1] for name in modules])

    return modules


def nan_mask(data: ArrayLike) -> np.ndarray:
    """Replace any masked array values with NaNs.

    As a consequence of filling the mask with NaNs, non-float arrays will be
    cast to float.

    Parameters
    ----------
    data : :data:`~numpy.typing.ArrayLike`
        The masked array to be filled with NaNs.

    Returns
    -------
    :class:`~numpy.ndarray`
        The `data` with masked values replaced with NaNs.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if not isinstance(data, np.ndarray):
        # keep the mask of any masked arrays a sequence holds
        data = np.ma.asanyarray(data)

        if np.ma.getmask(data) is np.ma.nomask:
            data = data.data

    if np.ma.isMaskedArray(data):
        if data.dtype.char not in np.typecodes["Float"]:
            data = np.ma.asanyarray(data, dtype=float)

        data = data.filled(np.nan)

    return data


def _named(names: Sequence[str]) -> str:
    """Name the coordinates that are missing, with the verb that follows them.

    The phrase completes a refusal of a missing position (positions spec §4.1),
    such as "'x' is" or "'x' and 'y' are".

    Parameters
    ----------
    names : sequence of str
        The names of the arguments that are missing, one or two of them.

    Returns
    -------
    str
        The names quoted and joined by "and", then "is" for one or "are" for more.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    verb = "is" if len(names) == 1 else "are"
    return f"{' and '.join(repr(name) for name in names)} {verb}"


def _first_true(flags: NDArray[np.bool_]) -> tuple[tuple[int, ...], str]:
    """Find the first flag that is set, with its index in each dimension.

    A refusal of an infinite value places it by this index (positions spec §4.1).

    Parameters
    ----------
    flags : ndarray of bool
        The flags, of one dimension or more, at least one of which is set.

    Returns
    -------
    tuple of int
        The index of the first flag set, in each dimension, in C order.
    str
        The index as text, such as "1" for one dimension or "(1, 1)" for two.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    flat = int(np.flatnonzero(flags)[0])
    index = tuple(int(i) for i in np.unravel_index(flat, flags.shape))
    text = str(index[0]) if len(index) == 1 else str(index)
    return index, text


def _missing(values: ArrayLike, *, name: str) -> NDArray[np.bool_]:
    """Find where one coordinate of some positions is missing.

    A coordinate is missing where it is masked or NaN, and an infinite one is
    refused, as positions spec §4.1 decides. A value under a mask is never read,
    so an infinite one there is missing too.

    Parameters
    ----------
    values : ArrayLike
        The values of the coordinate, with any ``pint`` quantity read already.
    name : str
        The name of the argument `values` was given as, to name it in a message.

    Returns
    -------
    ndarray of bool
        ``True`` where a value is masked or NaN, in the shape of `values`.

    Raises
    ------
    ValueError
        If a value that is not masked is infinite.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    array = np.ma.asanyarray(values, dtype=float)
    # the values under a mask are hidden here, so they are never read
    filled = np.ma.filled(array, 0.0)
    infinite = np.isinf(filled)

    if np.any(infinite):
        if filled.ndim:
            index, text = _first_true(infinite)
            emsg = f"{name!r} cannot be infinite, got {filled[index]} at index {text}."
        else:
            emsg = f"{name!r} cannot be infinite, got {float(filled)}."
        raise ValueError(emsg)

    result: NDArray[np.bool_] = np.ma.getmaskarray(array) | np.isnan(filled)
    return result


def _missing_and_named(
    xs: ArrayLike, ys: ArrayLike, *, x_name: str, y_name: str
) -> tuple[NDArray[np.bool_], list[str]]:
    """Find the missing positions among some, and name the coordinates missing.

    A position is missing when either of its coordinates is masked or NaN, and
    an infinite coordinate is refused, as positions spec §4.1 decides. The names
    word a refusal or, for a point cloud, the warning of a point dropped
    (positions spec §4.5). Read any ``pint`` quantity first, and call this before
    any position is built.

    Parameters
    ----------
    xs : ArrayLike
        The first coordinate of the positions, such as their longitudes.
    ys : ArrayLike
        The second coordinate of the positions, such as their latitudes.
    x_name : str
        The name of the argument `xs` was given as, to name it in a message.
    y_name : str
        The name of the argument `ys` was given as, to name it in a message.

    Returns
    -------
    ndarray of bool
        ``True`` where a position is missing, in the shape `xs` and `ys`
        broadcast to.
    list of str
        The names of the coordinates masked or NaN anywhere, `x_name` before
        `y_name`.

    Raises
    ------
    ValueError
        If a coordinate that is not masked is infinite, or `xs` and `ys` do not
        broadcast together.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    x_missing = _missing(xs, name=x_name)
    y_missing = _missing(ys, name=y_name)

    try:
        np.broadcast_shapes(x_missing.shape, y_missing.shape)
    except ValueError as err:
        emsg = (
            f"Cannot pair {x_name!r} of shape {x_missing.shape} with {y_name!r} "
            f"of shape {y_missing.shape}."
        )
        raise ValueError(emsg) from err

    named = [
        name
        for name, flags in ((x_name, x_missing), (y_name, y_missing))
        if np.any(flags)
    ]
    return x_missing | y_missing, named


def _missing_positions(
    xs: ArrayLike, ys: ArrayLike, *, x_name: str, y_name: str
) -> NDArray[np.bool_]:
    """Find the missing positions among some, given as two coordinates.

    A position is missing when either of its coordinates is masked or NaN, and
    an infinite coordinate is refused, as positions spec §4.1 decides. Read any
    ``pint`` quantity first, and call this before any position is built.

    Parameters
    ----------
    xs : ArrayLike
        The first coordinate of the positions, such as their longitudes.
    ys : ArrayLike
        The second coordinate of the positions, such as their latitudes.
    x_name : str
        The name of the argument `xs` was given as, to name it in a message.
    y_name : str
        The name of the argument `ys` was given as, to name it in a message.

    Returns
    -------
    ndarray of bool
        ``True`` where a position is missing, in the shape `xs` and `ys`
        broadcast to.

    Raises
    ------
    ValueError
        If a coordinate that is not masked is infinite, or `xs` and `ys` do not
        broadcast together.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    missing, _ = _missing_and_named(xs, ys, x_name=x_name, y_name=y_name)
    return missing


def _missing_as_nan(
    xs: ArrayLike, ys: ArrayLike, *, x_name: str, y_name: str
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Read two coordinates as floats, with NaN in both at each missing position.

    A position is missing when either of its coordinates is masked or NaN, and
    an infinite coordinate is refused, as positions spec §4.1 decides. A missing
    position gives NaN in every component of a conversion (positions spec §4.7),
    so it has neither coordinate here. Coordinates of different shapes are each
    read alone, and left for their caller to refuse. Read any ``pint`` quantity
    first.

    Parameters
    ----------
    xs : ArrayLike
        The first coordinate of the positions, such as their longitudes.
    ys : ArrayLike
        The second coordinate of the positions, such as their latitudes.
    x_name : str
        The name of the argument `xs` was given as, to name it in a message.
    y_name : str
        The name of the argument `ys` was given as, to name it in a message.

    Returns
    -------
    tuple of ndarray
        New arrays of the first and the second coordinates, never those given,
        with NaN in both wherever either is missing, when their shapes match.

    Raises
    ------
    ValueError
        If a coordinate that is not masked is infinite.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    x_missing = _missing(xs, name=x_name)
    y_missing = _missing(ys, name=y_name)

    # copied, so that the arrays given are never written to
    x = np.array(np.ma.filled(np.ma.asanyarray(xs, dtype=float), np.nan))
    y = np.array(np.ma.filled(np.ma.asanyarray(ys, dtype=float), np.nan))

    if x.shape == y.shape:
        missing = x_missing | y_missing
        x[missing] = np.nan
        y[missing] = np.nan

    return x, y


def _missing_pair(
    x: ArrayLike, y: ArrayLike, *, x_name: str, y_name: str
) -> tuple[float, float]:
    """Read one position given as two values, with NaN in both if it is missing.

    The fast form of :func:`_missing_as_nan` for one position, which
    :func:`geovista.geodesic.line` reads once for each pair of its vertices
    (positions spec §8 item 5). Two plain real numbers are read without building
    an array, and any other value, such as a masked one or ``None``, is read by
    :func:`_missing_as_nan`.

    Parameters
    ----------
    x : ArrayLike
        The first coordinate of the position, such as its longitude.
    y : ArrayLike
        The second coordinate of the position, such as its latitude.
    x_name : str
        The name of the argument `x` was given as, to name it in a message.
    y_name : str
        The name of the argument `y` was given as, to name it in a message.

    Returns
    -------
    tuple of float
        The first and the second coordinate, both NaN when either is missing.

    Raises
    ------
    ValueError
        If a coordinate that is not masked is infinite.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    plain = (int, float, np.integer, np.floating)
    if not (isinstance(x, plain) and isinstance(y, plain)):
        first, second = _missing_as_nan(x, y, x_name=x_name, y_name=y_name)
        return float(first), float(second)

    pair = float(x), float(y)
    for name, value in zip((x_name, y_name), pair, strict=True):
        if math.isinf(value):
            emsg = f"{name!r} cannot be infinite, got {value}."
            raise ValueError(emsg)

    if math.isnan(pair[0]) or math.isnan(pair[1]):
        return math.nan, math.nan
    return pair


def _refuse_missing_poi(
    x: ArrayLike, y: ArrayLike, *, x_name: str, y_name: str
) -> None:
    """Refuse a point-of-interest that is missing, naming its missing coordinates.

    A function given one position has nothing to answer for a missing one
    (positions spec §4.3).

    Parameters
    ----------
    x : ArrayLike
        The first coordinate of the point-of-interest.
    y : ArrayLike
        The second coordinate of the point-of-interest.
    x_name : str
        The name of the argument `x` was given as, to name it in a message.
    y_name : str
        The name of the argument `y` was given as, to name it in a message.

    Raises
    ------
    ValueError
        If `x` or `y` is masked or NaN, or either is infinite.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    named = [
        name
        for name, value in ((x_name, x), (y_name, y))
        if np.any(_missing(value, name=name))
    ]

    if named:
        emsg = f"The point-of-interest is missing, as {_named(named)} masked or NaN."
        raise ValueError(emsg)


def _refuse_missing_positions(
    xs: ArrayLike, ys: ArrayLike, *, x_name: str, y_name: str, shape: str
) -> None:
    """Refuse a shape with a missing position, counting them and naming each coordinate.

    A shape built from many positions has no meaning with a gap in it, so it is
    refused before any of it is built (positions spec §4.4). A position is missing
    when either of its coordinates is masked or NaN, and an infinite coordinate is
    refused, as positions spec §4.1 decides. Read any ``pint`` quantity first.

    Parameters
    ----------
    xs : ArrayLike
        The first coordinate of the positions, such as their longitudes.
    ys : ArrayLike
        The second coordinate of the positions, of the same size as `xs`.
    x_name : str
        The name of the argument `xs` was given as, to name it in a message.
    y_name : str
        The name of the argument `ys` was given as, to name it in a message.
    shape : str
        The shape the positions build, to name it in a message, such as
        "geodesic line".

    Raises
    ------
    ValueError
        If a position is missing, or a coordinate that is not masked is infinite,
        or `xs` and `ys` do not pair.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    missing, named = _missing_and_named(xs, ys, x_name=x_name, y_name=y_name)
    count = int(np.count_nonzero(missing))

    if count:
        verb = "is" if count == 1 else "are"
        emsg = (
            f"A {shape} needs every position given, but {count} of {missing.size} "
            f"{verb} missing, as {_named(named)} masked or NaN."
        )
        raise ValueError(emsg)


def point_cloud(mesh: pv.PolyData) -> bool:
    """Determine whether the `mesh` is a point-cloud.

    Parameters
    ----------
    mesh : :class:`~pyvista.PolyData`
        The mesh to be checked.

    Returns
    -------
    bool
        Whether the `mesh` is a point-cloud.

    Notes
    -----
    .. versionadded:: 0.2.0

    """
    result: bool = (mesh.n_points == mesh.n_cells) and (mesh.n_lines == 0)
    return result


def sanitize(
    *meshes: pv.PolyData,
    extra: str | list[str] | None = None,
    vtk: bool = True,
    legacy: bool = True,
) -> None:
    """Purge standard helper cell and point data index arrays.

    Parameters
    ----------
    *meshes : iterable of :class:`~pyvista.PolyData`
        One or more meshes to sanitize.
    extra : str or list of str, optional
        The name of additional data arrays to purge.
    vtk : bool | None, optional
        Whether to sanitize VTK data arrays. Defaults to ``True``.
    legacy : bool, default=True
        Whether to translate and remove retired fields, as
        :func:`sanitize_legacy` does.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if not meshes:
        emsg = "Expected one or more meshes to sanitize."
        raise ValueError(emsg)

    if isinstance(extra, str):
        extra = [extra]

    cleanse = _GV_SANITIZE.copy()

    if extra:
        cleanse.extend(list(extra))

    for mesh in meshes:
        for name in cleanse:
            if name in mesh.cell_data:
                del mesh.cell_data[name]

            if name in mesh.point_data:
                del mesh.point_data[name]

    if vtk:
        sanitize_vtk(*meshes)

    if legacy:
        sanitize_legacy(*meshes)


def sanitize_legacy(
    *meshes: pv.DataSet,
) -> None:
    """Translate and remove the retired fields of each mesh, in place.

    Each field of :data:`RETIRED_FIELDS` that a mesh has is translated into
    what replaced it, then removed, so that saving the mesh does not carry the
    field forward. A mesh with none is unchanged, and nothing warns.

    Parameters
    ----------
    *meshes : iterable of :class:`~pyvista.DataSet`
        One or more meshes to sanitize.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if not meshes:
        emsg = "Expected one or more meshes to sanitize."
        raise ValueError(emsg)

    for mesh in meshes:
        for entry in RETIRED_FIELDS:
            if entry.name in getattr(mesh, f"{entry.association}_data"):
                entry.translate(mesh)
                data = getattr(mesh, f"{entry.association}_data")
                if entry.name in data:
                    del data[entry.name]


def sanitize_vtk(
    *meshes: pv.PolyData,
) -> None:
    """Purge standard VTK helper cell and point data index arrays.

    Parameters
    ----------
    *meshes : iterable of :class:`~pyvista.PolyData`
        One or more meshes to sanitize.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if not meshes:
        emsg = "Expected one or more meshes to sanitize."
        raise ValueError(emsg)

    for mesh in meshes:
        for name in _VTK_SANITIZE:
            if name in mesh.cell_data:
                del mesh.cell_data[name]

            if name in mesh.point_data:
                del mesh.point_data[name]


def set_jupyter_backend(*, backend: str | None = None) -> bool:
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
    lons: ArrayLike | Quantity,
    lats: ArrayLike | Quantity,
    *,
    globe: Globe | None = None,
    zlevel: float | ArrayLike | None = None,
    zscale: float | None = None,
    stacked: bool | None = True,
) -> np.ndarray:
    """Convert geographic longitudes and latitudes to cartesian ``xyz`` points.

    A position is missing when its longitude or latitude is masked or NaN, and
    gives NaN in every component (positions spec §4.7). An infinite longitude or
    latitude is refused.

    Parameters
    ----------
    lons : :data:`~numpy.typing.ArrayLike` or pint.Quantity
        The longitude values (degrees) to be converted.
        A ``pint`` quantity, from any registry, is read in degrees. Give `lats` as a
        quantity too.
    lats : :data:`~numpy.typing.ArrayLike` or pint.Quantity
        The latitude values (degrees) to be converted.
        A ``pint`` quantity, from any registry, is read in degrees. Give `lons` as a
        quantity too.
    globe : :class:`~geovista.globe.Globe`, optional
        The globe whose render radius the points lie at. Defaults to
        ``Globe()``, whose render radius is :data:`RADIUS`.
    zlevel : float or :data:`~numpy.typing.ArrayLike`, default=0.0
        The z-axis level. Used in combination with the `zscale` to offset the
        render radius by a proportional amount i.e.,
        ``render_radius * zlevel * zscale``. If `zlevel` is not a scalar, then its
        shape must match or broadcast with the shape of `lons` and `lats`.
    zscale : float, optional
        The proportional multiplier for z-axis `zlevel`. Defaults to
        :data:`ZLEVEL_SCALE`.
    stacked : bool, default=True
        Specify whether the resultant xyz points have shape (N, 3).
        Otherwise, they will have shape (3, N).

    Returns
    -------
    :class:`~numpy.ndarray`
        The ``xyz`` spherical cartesian points.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # geovista.globe imports this module
    from .globe import _resolve  # noqa: PLC0415

    # promoted first, as _to_cartesian promotes them, so that a number pairs with
    # an array of one
    lons, lats = map(np.atleast_1d, _lonlats(lons, lats))

    # a missing position has neither coordinate, so every component is NaN
    lons, lats = _missing_as_nan(lons, lats, x_name="lons", y_name="lats")

    return _to_cartesian(
        lons,
        lats,
        radius=_resolve(globe).render_radius,
        zlevel=zlevel,
        zscale=zscale,
        stacked=stacked,
    )


def _to_cartesian(
    lons: ArrayLike,
    lats: ArrayLike,
    *,
    radius: float | None = None,
    zlevel: float | ArrayLike | None = None,
    zscale: float | None = None,
    stacked: bool | None = True,
) -> np.ndarray:
    """Convert geographic longitudes and latitudes to points at a radius.

    The float form of :func:`to_cartesian`, which geovista calls inside with a
    render radius, or a radius a z-level has already lifted.

    Parameters
    ----------
    lons : :data:`~numpy.typing.ArrayLike`
        The longitude values (degrees) to be converted.
    lats : :data:`~numpy.typing.ArrayLike`
        The latitude values (degrees) to be converted.
    radius : float, optional
        The radius of the sphere. Defaults to :data:`RADIUS`.
    zlevel : float or :data:`~numpy.typing.ArrayLike`, default=0.0
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
    :class:`~numpy.ndarray`
        The ``xyz`` spherical cartesian points.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    lons = np.atleast_1d(lons)
    lats = np.atleast_1d(lats)

    if (shape := lons.shape) != lats.shape:
        emsg = (
            f"Require longitudes and latitudes with same shape, got {shape} and "
            f"{lats.shape} respectively."
        )
        raise ValueError(emsg)

    if (ndim := lons.ndim) > 3:
        emsg = f"Require at most 3D longitudes and latitudes, got {ndim}D instead."
        raise ValueError(emsg)

    radius = RADIUS if radius is None else abs(float(radius))
    zscale = ZLEVEL_SCALE if zscale is None else float(zscale)
    # cast as float here, as from_cartesian use-case results in float zlevels
    # that should be dtype preserved for the purpose of precision
    zlevel_array = (
        np.array([0.0]) if zlevel is None else np.atleast_1d(zlevel).astype(float)
    )

    try:
        _ = np.broadcast_shapes(zlevel_array.shape, shape)
    except ValueError as err:
        emsg = (
            f"Cannot broadcast zlevel with shape {zlevel_array.shape} to "
            f"longitude/latitude shape {shape}."
        )
        raise ValueError(emsg) from err

    radii = radius + radius * zlevel_array * zscale

    x_rad = np.radians(lons)
    y_rad = np.radians(90.0 - lats)
    x = np.ravel(radii * np.sin(y_rad) * np.cos(x_rad))
    y = np.ravel(radii * np.sin(y_rad) * np.sin(x_rad))
    z = np.ravel(radii * np.cos(y_rad))
    xyz = [x, y, z]

    return np.vstack(xyz).T if stacked else np.array(xyz)


def vectors_to_cartesian(
    lons: ArrayLike | Quantity,
    lats: ArrayLike | Quantity,
    vectors: Vector3DLike,
    *,
    globe: Globe | None = None,
    zlevel: float | ArrayLike | None = None,
    zscale: float | None = None,
) -> Vector3DLike:
    """Transform geographic-oriented vector components ``uvw`` to cartesian ``xyz``.

    A position is missing when its longitude or latitude is masked or NaN, and
    gives NaN in every component of its vector (positions spec §4.7). An infinite
    longitude or latitude is refused.

    Parameters
    ----------
    lons : ArrayLike or pint.Quantity
        The longitude points of the `vectors` (in degrees). Must be the same
        shape as `lats`.
        A ``pint`` quantity, from any registry, is read in degrees. Give `lats` as a
        quantity too.
    lats : ArrayLike or pint.Quantity
        The latitude points of the `vectors` (in degrees). Must be the same
        shape as `lons`.
        A ``pint`` quantity, from any registry, is read in degrees. Give `lons` as a
        quantity too.
    vectors : Vector3DLike
        The eastward (``U``), northward (``V``) and upward (``W``) vector components.
        All shapes must be the same as `lons` and `lats`.
    globe : :class:`~geovista.globe.Globe`, optional
        The globe whose render radius scales the vectors. Defaults to
        ``Globe()``, whose render radius is :data:`RADIUS`.
    zlevel : int  or :data:`~numpy.typing.ArrayLike`, default=0.0
        The z-axis level. Used in combination with the `zscale` to offset the
        render radius by a proportional amount i.e.,
        ``render_radius * zlevel * zscale``.
        NOTE : non-scalar `zlevel` is not actually supported, since it is planned to
        drop support for this from :meth:`~geovista.bridge.Transform.from_points`.
        It will raise an error.
    zscale : float, optional
        The proportional multiplier for z-axis `zlevel`. Defaults to
        :data:`ZLEVEL_SCALE`.

    Returns
    -------
    Vector3DLike
        The corresponding ``xyz`` cartesian vector components.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    # geovista.globe imports this module
    from .globe import _resolve  # noqa: PLC0415

    lons, lats = _lonlats(lons, lats)

    # a missing position has neither coordinate, so every component is NaN
    lons, lats = _missing_as_nan(lons, lats, x_name="lons", y_name="lats")

    return _vectors_to_cartesian(
        lons,
        lats,
        vectors,
        radius=_resolve(globe).render_radius,
        zlevel=zlevel,
        zscale=zscale,
    )


def _refuse_multiple_zlevel(zlevel: float | ArrayLike | None) -> None:
    """Refuse a z-level of more than one value, which vectors cannot carry.

    :meth:`~geovista.bridge.Transform.from_points` refuses one given with its
    vectors before it drops any missing point, so the shape named is the one given
    (positions spec §8 item 4).

    Parameters
    ----------
    zlevel : float or ArrayLike, optional
        The z-axis level.

    Raises
    ------
    ValueError
        If `zlevel` holds more than one value.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if zlevel is None:
        return

    levels = np.atleast_1d(zlevel)

    if levels.size > 1:
        # TODO @pp-mo: remove multiple zlevel, when removed from "from_points".
        msg = f"'zlevel' may not be multiple, has shape {levels.shape}."
        raise ValueError(msg)


def _vectors_to_cartesian(
    lons: ArrayLike,
    lats: ArrayLike,
    vectors: Vector3DLike,
    *,
    radius: float | None = None,
    zlevel: float | ArrayLike | None = None,
    zscale: float | None = None,
) -> Vector3DLike:
    """Transform geographic-oriented vector components to cartesian at a radius.

    The float form of :func:`vectors_to_cartesian`, which geovista calls inside
    with a render radius.

    Parameters
    ----------
    lons : ArrayLike
        The longitude points of the `vectors` (in degrees). Must be the same
        shape as `lats`.
    lats : ArrayLike
        The latitude points of the `vectors` (in degrees). Must be the same
        shape as `lons`.
    vectors : Vector3DLike
        The eastward (``U``), northward (``V``) and upward (``W``) vector components.
        All shapes must be the same as `lons` and `lats`.
    radius : float, optional
        The radius of the sphere. Defaults to :data:`RADIUS`.
    zlevel : int  or :data:`~numpy.typing.ArrayLike`, default=0.0
        The z-axis level. Used in combination with the `zscale` to offset the
        `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
        NOTE : non-scalar `zlevel` is not actually supported, since it is planned to
        drop support for this from :meth:`~geovista.bridge.Transform.from_points`.
        It will raise an error.
    zscale : float, optional
        The proportional multiplier for z-axis `zlevel`. Defaults to
        :data:`ZLEVEL_SCALE`.

    Returns
    -------
    Vector3DLike
        The corresponding ``xyz`` cartesian vector components.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    radius = RADIUS if radius is None else abs(float(radius))
    zscale = ZLEVEL_SCALE if zscale is None else float(zscale)
    # cast as float here, as from_cartesian use-case results in float zlevels
    # that should be dtype preserved for the purpose of precision
    zlevel_array = (
        np.array([0.0]) if zlevel is None else np.atleast_1d(zlevel).astype(float)
    )

    _refuse_multiple_zlevel(zlevel_array)

    radii = radius + radius * zlevel_array * zscale

    lons, lats = np.asanyarray(lons), np.asanyarray(lats)
    u, v, w = (np.asanyarray(component) for component in vectors)

    if lons.shape != lats.shape:
        msg = f"'lons' and 'lats' do not have same shape: {lons.shape} != {lats.shape}."
        raise ValueError(msg)

    if any(x.shape != lons.shape for x in (u, v, w)):
        msg = (
            "some 'vectors' do not have same shape as 'lons' : "
            f"{[x.shape for x in (u, v, w)]} != {lons.shape}."
        )
        raise ValueError(msg)

    lons, lats = (np.deg2rad(arr) for arr in (lons, lats))

    coslons = np.cos(lons)
    sinlons = np.sin(lons)
    coslats = np.cos(lats)
    sinlats = np.sin(lats)
    # N.B. the term signs are slightly unexpected here, because the viewing coord system
    # is not quite what you may expect :  The "Y" axis goes to the right, and the "X"
    # axis points out of the screen, towards the viewer.
    z_factor = w * coslats - v * sinlats
    wy = coslons * u + sinlons * z_factor
    wx = -sinlons * u + coslons * z_factor
    wz = v * coslats + w * sinlats
    # NOTE: for better efficiency, we *COULD* handle the w=0 special case separately.
    # Right now, for simplicity, we just don't bother.
    return (radii * wx, radii * wy, radii * wz)


def to_lonlat(
    xyz: ArrayLike,
    /,
    *,
    radians: bool | None = False,
    globe: Globe | None = None,
    rtol: float | None = None,
    atol: float | None = None,
) -> np.ndarray:
    """Convert cartesian `xyz` point on sphere to geographic longitude and latitude.

    Parameters
    ----------
    xyz : :data:`~numpy.typing.ArrayLike`
        The cartesian (x, y, z) point to be converted.
    radians : bool, default=False
        Convert resultant longitude and latitude values to radians.
        Default units are degrees.
    globe : :class:`~geovista.globe.Globe`, optional
        The globe whose render radius the point lies at. Defaults to
        ``Globe()``, whose render radius is :data:`RADIUS`.
    rtol : float, optional
        The relative tolerance for longitudes close to the 'wrap meridian' -
        see :func:`geovista.common.wrap` for more.
    atol : float, optional
        The absolute tolerance for longitudes close to the 'wrap meridian' -
        see :func:`geovista.common.wrap` for more.

    Returns
    -------
    :class:`~numpy.ndarray`
        The longitude and latitude values.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    point = np.asanyarray(xyz)

    if point.shape != (3,):
        shape = f" with shape {point.shape}" if point.shape else ""
        emsg = (
            f"Require a 1D array of (x, y, z) points, got a {point.ndim}D array{shape}."
        )
        raise ValueError(emsg)

    result: np.ndarray
    (result,) = to_lonlats(point, radians=radians, globe=globe, rtol=rtol, atol=atol)

    return result


def to_lonlats(
    xyz: ArrayLike,
    /,
    *,
    radians: bool | None = False,
    globe: Globe | None = None,
    stacked: bool | None = True,
    rtol: float | None = None,
    atol: float | None = None,
) -> np.ndarray:
    """Convert cartesian `xyz` points on sphere to geographic longitudes and latitudes.

    Parameters
    ----------
    xyz : :data:`~numpy.typing.ArrayLike`
        The cartesian (x, y, z) points to be converted.
    radians : bool, default=False
        Convert resultant longitude and latitude values to radians.
        Default units are degrees.
    globe : :class:`~geovista.globe.Globe`, optional
        The globe whose render radius the points lie at. Defaults to
        ``Globe()``, whose render radius is :data:`RADIUS`.
    stacked : bool, default=True
        Default the resultant shape to be ``(N, 2)``, otherwise ``(2, N)``.
    rtol : float, optional
        The relative tolerance for longitudes close to the 'wrap meridian' -
        see :func:`geovista.common.wrap` for more.
    atol : float, optional
        The absolute tolerance for longitudes close to the 'wrap meridian' -
        see :func:`geovista.common.wrap` for more.

    Returns
    -------
    :class:`~numpy.ndarray`
        The longitude and latitude values.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    # geovista.globe imports this module
    from .globe import _resolve  # noqa: PLC0415

    return _to_lonlats(
        xyz,
        radians=radians,
        radius=_resolve(globe).render_radius,
        stacked=stacked,
        rtol=rtol,
        atol=atol,
    )


def _to_lonlats(
    xyz: ArrayLike,
    /,
    *,
    radians: bool | None = False,
    radius: float | ArrayLike | None = None,
    stacked: bool | None = True,
    rtol: float | None = None,
    atol: float | None = None,
) -> np.ndarray:
    """Convert cartesian `xyz` points at a radius to longitudes and latitudes.

    The float form of :func:`to_lonlats`, which geovista calls inside with a
    render radius, or with the radius of each point.

    Parameters
    ----------
    xyz : :data:`~numpy.typing.ArrayLike`
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
        The relative tolerance for longitudes close to the 'wrap meridian' -
        see :func:`geovista.common.wrap` for more.
    atol : float, optional
        The absolute tolerance for longitudes close to the 'wrap meridian' -
        see :func:`geovista.common.wrap` for more.

    Returns
    -------
    :class:`~numpy.ndarray`
        The longitude and latitude values.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    points = np.atleast_2d(xyz)

    if points.ndim != 2 or points.shape[1] != 3:
        emsg = (
            "Require a 2D array of (x, y, z) points, got a "
            f"{points.ndim}D array with shape {points.shape}."
        )
        raise ValueError(emsg)

    if radius is None:
        radius = RADIUS

    radius_array = np.abs(np.atleast_1d(radius).astype(float))

    if radius_array.shape != (1,) and (
        radius_array.ndim != 1 or radius_array.shape[0] != points.shape[0]
    ):
        emsg = (
            f"Require a 1D array of radii, got a {radius_array.ndim}D array "
            f"with shape {radius_array.shape}."
        )
        raise ValueError(emsg)

    base, period = (np.radians(BASE), np.radians(PERIOD)) if radians else (BASE, PERIOD)

    lons = np.arctan2(points[:, 1], points[:, 0])
    if not radians:
        lons = np.degrees(lons)
    lons = wrap(lons, base=base, period=period, rtol=rtol, atol=atol)

    z_radius = points[:, 2] / radius_array
    # NOTE: defensive clobber of values outside arcsin domain [-1, 1]
    #       which is the result of floating point inaccuracies at the extremes
    if indices := np.where(z_radius > 1):
        z_radius[indices] = 1.0
    if indices := np.where(z_radius < -1):
        z_radius[indices] = -1.0
    lats = np.arcsin(z_radius)
    if not radians:
        lats = np.degrees(lats)

    data = [lons, lats]

    return np.vstack(data).T if stacked else np.array(data)


def _face_offsets(surface: pv.PolyData) -> np.ndarray:
    """Determine the face offsets of the provided mesh.

    The offsets are the indices into the face connectivity array of the first
    point of each face, along with a final entry of the total number of
    connectivity entries i.e., there are ``surface.n_faces + 1`` offsets.

    Parameters
    ----------
    surface : :class:`~pyvista.PolyData`
        The surface mesh to determine the face offsets of.

    Returns
    -------
    :class:`~numpy.ndarray`
        The face offsets of the mesh.

    Notes
    -----
    .. versionadded:: 0.6.0

    Defers to the underlying :vtk:`vtkCellArray` of the mesh, as ``pyvista``
    removed its private ``PolyData._offset_array`` property in ``pyvista>=0.49``
    when adopting fixed-size storage for regular cell arrays, see
    https://github.com/pyvista/pyvista/pull/8873.

    """
    result: np.ndarray = pv.convert_array(surface.GetPolys().GetOffsetsArray())
    return result


def triangulated(surface: pv.PolyData) -> bool:
    """Determine whether the provided mesh is triangulated.

    Parameters
    ----------
    surface : :class:`~pyvista.PolyData`
        The surface mesh to check whether the geometry of all its cells are triangles.

    Returns
    -------
    bool
        Whether the surface is fully triangulated.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return bool(np.all(np.diff(_face_offsets(surface)) == 3))


def vtk_warnings_off() -> None:
    """Disable :vtk:`vtkLogger` warning messages.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    vtk.vtkObject.GlobalWarningDisplayOff()
    vtk.vtkLogger.SetStderrVerbosity(vtk.vtkLogger.VERBOSITY_OFF)


def vtk_warnings_on() -> None:
    """Enable :vtk:`vtkLogger` warning messages.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    vtk.vtkObject.GlobalWarningDisplayOn()
    vtk.vtkLogger.SetStderrVerbosity(vtk.vtkLogger.VERBOSITY_INFO)


def wrap(
    lons: ArrayLike | Quantity,
    *,
    base: float | Quantity | None = None,
    period: float | Quantity | None = None,
    rtol: float | None = None,
    atol: float | None = None,
    dtype: DTypeLike | None = None,
) -> np.ndarray:
    """Transform longitudes to be in the half-open interval ``[base, base + period)``.

    Parameters
    ----------
    lons : :data:`~numpy.typing.ArrayLike` or pint.Quantity
        One or more longitude values to be wrapped in the interval.
        A ``pint`` quantity, from any registry, is read in degrees, so a plain
        `base` or `period` given with it is in degrees too.
    base : float or pint.Quantity, optional
        The start limit of the half-open interval. Defaults to :data:`BASE`.
        A ``pint`` quantity, from any registry, is read in degrees.
    period : float or pint.Quantity, optional
        The end limit of the half-open interval expressed as a length
        from the `base`, in the same units. Defaults to :data:`PERIOD`.
        A ``pint`` quantity, from any registry, is read in degrees.
    rtol : float, optional
        The relative tolerance for longitudes close to the 'wrap meridian' -
        that is ``base + period`` - to be considered equal to the wrap
        meridian. Necessary to prevent cell smearing. See  `rtol` in
        :func:`numpy.isclose`. Defaults to :data:`WRAP_RTOL`.
    atol : float, optional
        The absolute tolerance for longitudes close to the 'wrap meridian' -
        that is ``base + period`` - to be considered equal to the wrap
        meridian. Necessary to prevent cell smearing. See `atol` in
        :func:`numpy.isclose`. Defaults to :data:`WRAP_ATOL`.
    dtype : :data:`~numpy.typing.DTypeLike`, optional
        The data-type of the wrapped longitudes. Defaults to ``float64``. The
        longitudes are wrapped in the `dtype` when it is floating point.
        Otherwise they are wrapped as ``float64`` and then converted, so an
        integer `dtype` truncates each wrapped longitude towards zero.

    Returns
    -------
    :class:`~numpy.ndarray`
        The transformed longitude values.

    Notes
    -----
    .. versionadded:: 0.1.0

    Examples
    --------
    >>> from geovista.common import wrap
    >>> import numpy as np
    >>> wrap([179.0, 179.999, 180.0, 181.0])
    array([ 179., -180., -180., -179.])

    >>> wrap([179, 180, 181], period=90)
    array([ -91., -180., -179.])

    >>> wrap([179, 180, 181], base=0, period=90)
    array([89.,  0.,  1.])

    """
    lons = _angle_array("lons", lons)
    base, period = _angle("base", base), _angle("period", period)

    if not isinstance(lons, Iterable):
        lons = np.atleast_1d(lons)

    if base is None:
        base = BASE

    if period is None:
        period = PERIOD

    if rtol is None:
        rtol = WRAP_RTOL

    if atol is None:
        atol = WRAP_ATOL

    dtype = np.dtype(np.float64 if dtype is None else dtype)
    # wrapping is floating point arithmetic, so converting the longitudes to
    # any other dtype beforehand would wrap different values
    floating = np.issubdtype(dtype, np.floating)

    lons = np.asanyarray(lons, dtype=dtype if floating else np.float64)
    # arithmetic on a 0D array gives a numpy scalar, so keep the array
    result = np.asanyarray(((lons - base + period * 2) % period) + base)

    mask = np.isclose(result, base + period, rtol=rtol, atol=atol)
    if np.any(mask):
        # snap to the base for values within tolerances
        result[mask] = base

    return result if floating else result.astype(dtype)
