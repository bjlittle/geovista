from enum import Enum, auto, unique
from typing import Any, Optional

import numpy as np
import pyvista as pv

from .common import (
    GV_CELL_IDS,
    GV_POINT_IDS,
    GV_REMESH_POINT_IDS,
    REMESH_JOIN,
    REMESH_SEAM,
    calculate_radius,
    sanitize_data,
    to_xy0,
    wrap,
)
from .filters import cast_UnstructuredGrid_to_PolyData as cast
from .filters import remesh
from .log import get_logger

__all__ = [
    "MeridianSlice",
    "add_texture_coords",
    "combine",
    "cut_along_meridian",
    "logger",
]

# Configure the logger.
logger = get_logger(__name__)

#: Preference for a slice to bias cells west of the chosen meridian.
CUT_WEST: str = "west"

#: Preference for a slice to be true to the chosen meridian.
CUT_EXACT: str = "exact"

#: Preference for a slice to bias cells east of the chosen meridian.
CUT_EAST: str = "east"

#: Cartesian west/east bias offset of a slice.
CUT_OFFSET: float = 1e-5

#: By default, generate a mesh seam at this meridian.
DEFAULT_MERIDIAN: float = 0.0


@unique
class SliceBias(Enum):
    west = -1
    exact = auto()
    east = auto()


class MeridianSlice:
    def __init__(
        self,
        mesh: pv.PolyData,
        meridian: float,
        offset: Optional[float] = None,
    ):
        """
        TODO

        Parameters
        ----------
        mesh
        meridian
        offset

        Notes
        -----
        .. versionadded :: 0.1.0

        """
        # logging convenience
        self._extra = dict(cls=self.__class__.__name__)

        # TODO: require a more robust and definitive approach
        zmin, zmax = mesh.bounds[4], mesh.bounds[5]
        if np.isclose(zmax - zmin, 0):
            emsg = "Cannot slice mesh appears to be a planar projection."
            raise ValueError(emsg)

        self._info = mesh.active_scalars_info
        mesh[GV_CELL_IDS] = np.arange(mesh.n_cells)
        mesh[GV_POINT_IDS] = np.arange(mesh.n_points)
        mesh.set_active_scalars(
            self._info.name, preference=self._info.association.name.lower()
        )

        self.mesh = mesh
        self.radius = calculate_radius(mesh)
        self.meridian = wrap(meridian)[0]
        self.offset = abs(CUT_OFFSET if offset is None else offset)
        logger.debug(
            f"meridian={self.meridian}, offset={self.offset}, radius={self.radius}",
            extra=self._extra,
        )
        self.slices = {bias.name: self._intersection(bias.value) for bias in SliceBias}

        n_cells = self.slices[CUT_EXACT].n_cells
        self.west_ids = set(self.slices[CUT_WEST][GV_CELL_IDS]) if n_cells else set()
        self.east_ids = set(self.slices[CUT_EAST][GV_CELL_IDS]) if n_cells else set()
        self.split_ids = self.west_ids.intersection(self.east_ids)
        logger.debug(
            f"west={len(self.west_ids)}, east={len(self.east_ids)}, "
            f"split={len(self.split_ids)}",
            extra=self._extra,
        )

    def _intersection(self, bias: float) -> pv.PolyData:
        """
        TODO

        Parameters
        ----------
        bias

        Returns
        -------

        Notes
        -----
        .. versionadded :: 0.1.0

        """
        logger.debug(f"{bias=}", extra=self._extra)
        y = bias * self.offset
        xyz = pv.Line((-self.radius, y, -self.radius), (self.radius, y, -self.radius))
        xyz.rotate_z(self.meridian, inplace=True)
        spline = pv.Spline(xyz.points, 1)
        mesh = self.mesh.slice_along_line(spline)
        logger.debug(
            f"n_cells={mesh.n_cells}, n_points={mesh.n_points}", extra=self._extra
        )
        return mesh

    def extract(
        self,
        bias: Optional[str] = None,
        split_cells: Optional[bool] = False,
        clip: Optional[bool] = True,
    ) -> pv.PolyData:
        """
        TODO

        Parameters
        ----------
        bias
        split_cells
        clip

        Returns
        -------

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if bias is None:
            bias = CUT_WEST

        if bias.lower() not in SliceBias.__members__:
            options = [f"'{option.name}'" for option in SliceBias]
            options = f"{', '.join(options[:-1])} or {options[-1]}"
            emsg = f"Expected a slice bias of either {options}, got '{bias}'."
            raise ValueError(emsg)

        # there is no intersection between the spline extruded in the
        # z-plane and the mesh
        if (mesh := self.slices[CUT_EXACT].n_cells) == 0:
            return mesh

        mesh = pv.PolyData()

        if split_cells:
            logger.debug(f"{bias=}, split={len(self.split_ids)}", extra=self._extra)
            extract_ids = self.split_ids
        else:
            whole_ids = set(self.slices[bias][GV_CELL_IDS]).difference(self.split_ids)
            logger.debug(f"{bias=}, whole={len(whole_ids)}", extra=self._extra)
            extract_ids = whole_ids

        logger.debug(f"extract={len(extract_ids)}", extra=self._extra)

        if extract_ids:
            mesh = cast(self.mesh.extract_cells(np.array(list(extract_ids))))
            logger.debug(
                f"mesh: {bias=}, n_cells={mesh.n_cells}, " f"n_points={mesh.n_points}",
                extra=self._extra,
            )
            if clip:
                ll = to_xy0(mesh)
                match = np.abs(ll[:, 0] - self.meridian) < 90
                mesh = cast(mesh.extract_points(match))
                logger.debug(
                    f"clip: {bias=}, n_cells={mesh.n_cells}, "
                    f"n_points={mesh.n_points}",
                    extra=self._extra,
                )
            sanitize_data(mesh)
            mesh.set_active_scalars(
                self._info.name, preference=self._info.association.name.lower()
            )
        else:
            logger.debug("no cells extracted from slice", extra=self._extra)

        return mesh


def combine(
    *meshes: Any,
    data: Optional[bool] = True,
    clean: Optional[bool] = False,
) -> pv.PolyData:
    """
    Combine two or more meshes into one mesh.

    Only meshes with faces will be combined. Support is not yet provided for combining
    meshes that consist of only points or lines.

    Note that, no check is performed to ensure that mesh faces do not overlap.
    However, meshes may share coincident points. Coincident point data from the
    first input mesh will overwrite all other mesh data sharing the same
    coincident point in the resultant mesh.

    Parameters
    ----------
    meshes : iterable of PolyData
        The meshes to be combined into a single :class:`pyvista.PolyData` mesh.
    data : bool, default=True
        Whether to also combine and attach common data from the meshes onto
        the resultant mesh.
    clean : bool, default=False
        Specify whether to merge duplicate points, remove unused points,
        and/or remove degenerate faces in the resultant mesh.

    Returns
    -------
    PolyData
        The input meshes combined into a single :class:`pyvista.PolyData`.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if not meshes:
        emsg = "Expected one or more meshes to combine."
        raise ValueError(emsg)

    if len(meshes) == 1:
        return meshes[0]

    first: pv.PolyData = meshes[0]
    combined_points, combined_faces = [], []
    n_points, n_faces = 0, 0

    if data:
        # determine the common point, cell and field array names
        # attached to the input meshes - these will be combined and
        # attached to the resultant combined mesh
        common_point_data = set(first.point_data.keys())
        common_cell_data = set(first.cell_data.keys())
        common_field_data = set(first.field_data.keys())
        active_scalars_info = set([first.active_scalars_info._namedtuple])

    for i, mesh in enumerate(meshes):
        if not isinstance(mesh, pv.PolyData):
            emsg = (
                f"Can only combine 'pyvista.PolyData' meshes, input mesh "
                f"#{i+1} has type '{mesh.__class__.__name__}'."
            )
            raise TypeError(emsg)

        if mesh.n_lines:
            emsg = (
                f"Can only combine meshes with faces, input mesh #{i+1} "
                "contains lines."
            )
            raise TypeError(emsg)

        if mesh.n_faces == 0:
            emsg = (
                f"Can only combine meshes with faces, input mesh #{i+1} "
                "has no faces."
            )
            raise TypeError(emsg)

        combined_points.append(mesh.points.copy())
        faces = mesh.faces.copy()

        if n_points:
            # compute the number of vertices (N) for each face of the mesh
            faces_N = np.diff(mesh._offset_array)
            # determine the N offset for each face within the faces array
            # a face entry consists of (N, v1, v2, ..., vN), where vN is the Nth
            # vertex offset (connectivity) for that face into the associated mesh points array
            faces_N_offset = mesh._offset_array + np.arange(mesh._offset_array.size)
            # offset the current mesh connectivity by the cumulative mesh points count
            faces += n_points
            # reinstate N for each face entry
            faces[faces_N_offset[:-1]] = faces_N

        combined_faces.append(faces)
        # accumulate running totals of combined mesh points and faces
        n_points += mesh.n_points
        n_faces += mesh.n_faces

        if data:
            # perform intersection to determine common names
            common_point_data &= set(mesh.point_data.keys())
            common_cell_data &= set(mesh.cell_data.keys())
            common_field_data &= set(mesh.field_data.keys())
            if mesh.active_scalars_name:
                active_scalars_info &= set([mesh.active_scalars_info._namedtuple])

    points = np.vstack(combined_points)
    faces = np.hstack(combined_faces)
    combined = pv.PolyData(points, faces=faces, n_faces=n_faces)

    def combine_data(names, field=False):
        for name in names:
            if field:
                combined.field_data[name] = first[name]
            else:
                data = [mesh[name] for mesh in meshes]
                combined[name] = (
                    np.vstack(data) if data[0].ndim > 1 else np.hstack(data)
                )

    if data:
        # attach any common combined data
        combine_data(common_point_data)
        combine_data(common_cell_data)
        combine_data(common_field_data, field=True)
        # determine a sensible active scalar array, by opting for the first
        # common active scalar array from the input meshes
        combined.active_scalars_name = None
        for info in active_scalars_info:
            association = info.association.name.lower()
            common_data = (
                common_cell_data if association == "cell" else common_point_data
            )
            if info.name in common_data:
                combined.set_active_scalars(info.name, preference=association)
                break

    # remove degenerate points and faces
    if clean:
        combined.clean(inplace=True)

    return combined


def cut_along_meridian(
    mesh: pv.PolyData,
    meridian: Optional[float] = None,
    antimeridian: Optional[bool] = False,
) -> pv.PolyData:
    """
    TODO

    Parameters
    ----------
    mesh
    meridian
    antimeridian

    Returns
    -------

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if not isinstance(mesh, pv.PolyData):
        emsg = f"Require a 'pyvista.PolyData' mesh, got '{mesh.__class__.__name__}'."
        raise TypeError(emsg)

    if meridian is None:
        meridian = DEFAULT_MERIDIAN

    if antimeridian:
        meridian += 180

    meridian = wrap(meridian)[0]
    logger.debug(f"{meridian=}, {antimeridian=}")

    slicer = MeridianSlice(mesh, meridian)
    mesh_whole = slicer.extract()
    mesh_split = slicer.extract(split_cells=True)
    info = mesh.active_scalars_info
    result: pv.PolyData = mesh.copy(deep=True)

    meshes = []
    remeshed_ids = np.array([])

    if mesh_whole.n_cells:
        ll = to_xy0(mesh_whole)
        meridian_mask = np.isclose(ll[:, 0], meridian)
        join_points = np.empty(mesh_whole.n_points, dtype=int)
        join_points.fill(REMESH_JOIN)
        mesh_whole[GV_REMESH_POINT_IDS] = join_points
        mesh_whole[GV_REMESH_POINT_IDS][meridian_mask] = REMESH_SEAM
        meshes.append(mesh_whole)
        remeshed_ids = mesh_whole[GV_CELL_IDS]
        result[GV_REMESH_POINT_IDS] = result[GV_POINT_IDS].copy()

    if mesh_split.n_cells:
        remeshed, remeshed_west, remeshed_east = remesh(mesh_split, meridian)
        meshes.extend([remeshed_west, remeshed_east])
        remeshed_ids = np.unique(np.hstack([remeshed_ids, remeshed[GV_CELL_IDS]]))
        if GV_REMESH_POINT_IDS not in result.point_data:
            result.point_data[GV_REMESH_POINT_IDS] = result[GV_POINT_IDS].copy()

    if meshes:
        result.remove_cells(remeshed_ids, inplace=True)
        result.set_active_scalars(info.name, preference=info.association.name.lower())
        result = combine(result, *meshes)

    return result


def add_texture_coords(
    mesh: pv.PolyData,
    meridian: Optional[float] = None,
    antimeridian: Optional[bool] = False,
) -> pv.PolyData:
    """
    TODO

    Parameters
    ----------
    mesh
    meridian
    antimeridian
    inplace

    Returns
    -------

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if meridian is None:
        meridian = DEFAULT_MERIDIAN

    if antimeridian:
        meridian += 180

    meridian = wrap(meridian)[0]

    if GV_REMESH_POINT_IDS not in mesh.point_data:
        mesh = cut_along_meridian(mesh, meridian=meridian)
    else:
        mesh = mesh.copy(deep=True)

    # convert from cartesian xyz to spherical lat/lons
    ll = to_xy0(mesh, closed_interval=True)
    lons, lats = ll[:, 0], ll[:, 1]
    # convert to normalised UV space
    u = (lons + 180) / 360
    v = (lats + 90) / 180
    t = np.vstack([u, v]).T
    mesh.active_t_coords = t
    logger.debug(f"{u.min()=}, {u.max()=}, {v.min()=}, {v.max()=}")

    return mesh
