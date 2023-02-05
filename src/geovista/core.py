"""
This module provides core geovista behaviour for processing
geo-located meshes.

Notes
-----
.. versionadded:: 0.1.0

"""
from enum import Enum, auto, unique
from typing import Any, Optional
import warnings

import numpy as np
import pyvista as pv

from .common import (
    GV_CELL_IDS,
    GV_FIELD_RADIUS,
    GV_POINT_IDS,
    GV_REMESH_POINT_IDS,
    RADIUS,
    REMESH_JOIN,
    REMESH_SEAM,
    calculate_radius,
    sanitize_data,
    to_xy0,
    to_xyz,
    wrap,
)
from .crs import from_wkt
from .filters import cast_UnstructuredGrid_to_PolyData as cast
from .filters import remesh
from .search import find_cell_neighbours

__all__ = [
    "MeridianSlice",
    "add_texture_coords",
    "combine",
    "cut_along_meridian",
    "is_projected",
    "resize",
]

#: Preference for a slice to bias cells west of the chosen meridian.
CUT_WEST: str = "WEST"

#: Preference for a slice to be true to the chosen meridian.
CUT_EXACT: str = "EXACT"

#: Preference for a slice to bias cells east of the chosen meridian.
CUT_EAST: str = "EAST"

#: Cartesian west/east bias offset of a slice.
CUT_OFFSET: float = 1e-5

#: By default, generate a mesh seam at this meridian.
DEFAULT_MERIDIAN: float = 0.0

#: The number of interpolation points along the meridian slice spline.
INTERSECTION_SPLINE_N_POINTS: int = 1


@unique
class SliceBias(Enum):
    WEST = -1
    EXACT = auto()
    EAST = auto()


class MeridianSlice:
    """
    Remesh a geo-located mesh along a meridian, from the north pole to the
    south pole.

    Remeshing involves introducing a seam into the mesh along the meridian
    of choice, splitting cells bisected by the meridan, which will be
    triangulated.

    """

    def __init__(
        self,
        mesh: pv.PolyData,
        meridian: float,
        offset: Optional[float] = None,
    ):
        """
        Create a seam along the `meridian` of the geo-located `mesh`, from the
        north pole to the south pole, breaking cell connectivity thus allowing
        the mesh to be correctly projected or texture mapped.

        Cells bisected by the `meridian` of choice will be remeshed i.e., split
        and triangulated.

        Parameters
        ----------
        mesh : PolyData
            The geo-located mesh to be remeshed along the `meridian`.
        meridian : float
            The meridian (degrees longitude) along which to create the mesh seam.
        offset : float, optional
            Offset buffer around the meridian, used to determine those cells west
            and east of that are coincident or bisected by the `meridian`. Defaults
            to :data:`geovista.core.CUT_OFFSET`.

        Notes
        -----
        .. versionadded :: 0.1.0

        """
        if is_projected(mesh):
            emsg = "Cannot slice mesh that appears to be a planar projection."
            raise ValueError(emsg)

        self._info = mesh.active_scalars_info
        mesh[GV_CELL_IDS] = np.arange(mesh.n_cells)
        mesh[GV_POINT_IDS] = np.arange(mesh.n_points)
        mesh.set_active_scalars(name=None)
        mesh.set_active_scalars(
            self._info.name, preference=self._info.association.name.lower()
        )
        self.mesh = mesh
        self.radius = calculate_radius(mesh)
        self.meridian = wrap(meridian)[0]
        self.offset = abs(CUT_OFFSET if offset is None else offset)
        self.slices = {bias.name: self._intersection(bias) for bias in SliceBias}

        n_cells = self.slices[CUT_EXACT].n_cells
        self.west_ids = set(self.slices[CUT_WEST][GV_CELL_IDS]) if n_cells else set()
        self.east_ids = set(self.slices[CUT_EAST][GV_CELL_IDS]) if n_cells else set()
        self.split_ids = self.west_ids.intersection(self.east_ids)

    def _intersection(
        self, bias: SliceBias, n_points: Optional[float] = None
    ) -> pv.PolyData:
        """
        Cut the mesh along the meridian, with or without a bias, to determine
        the cells that are coincident or bisected.

        The intersection is performed by extruding a spline in the z-axis to
        form a plane of intersection with the mesh.

        Parameters
        ----------
        bias : SliceBias
            Whether the the spline is west, east or exactly along the slice
            meridian.
        n_points : float, optional
            The number of interpolation points along the spline, which defines
            the plane of intersection through the mesh. Defaults to
            :data:`geovista.core.INTERSECTION_SPINE_N_POINTS`.

        Returns
        -------
        PolyData
            The cells of the mesh that are coincident or bisected by the slice.

        Notes
        -----
        .. versionadded :: 0.1.0

        """
        if n_points is None:
            n_points = INTERSECTION_SPLINE_N_POINTS

        y = bias.value * self.offset
        xyz = pv.Line((-self.radius, y, -self.radius), (self.radius, y, -self.radius))
        xyz.rotate_z(self.meridian, inplace=True)
        # the higher the number of spline interpolation "n_points"
        # the more accurate, but the more compute intensive and less performant
        spline = pv.Spline(xyz.points, n_points=n_points)
        mesh = self.mesh.slice_along_line(spline)

        return mesh

    def extract(
        self,
        bias: Optional[str] = None,
        split_cells: Optional[bool] = False,
        clip: Optional[bool] = True,
    ) -> pv.PolyData:
        """
        Extract the cells participating in the intersection between the
        meridian (with or without bias) and the mesh.

        Parameters
        ----------
        bias : str, optional
            Whether to extract the west, east or exact intersection cells.
            Default to :data:`geovista.core.CUT_WEST`.
        split_cells : bool, default=False
            Determine whether to return coincident whole cells or bisected
            cells of the meridian.
        clip : bool, default=True
            Determine whether to return the cells of intersection along the
            meridian or the great circle passing through the meridian.

        Returns
        -------
        PolyData
            The mesh cells from the intersection.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if bias is None:
            bias = CUT_WEST

        if bias.upper() not in SliceBias.__members__:
            options = [f"'{option.name.lower()}'" for option in SliceBias]
            options = f"{', '.join(options[:-1])} or {options[-1]}"
            emsg = f"Expected a slice bias of either {options}, got '{bias}'."
            raise ValueError(emsg)

        bias = bias.upper()
        mesh = pv.PolyData()

        # there is no intersection between the spline extruded in the
        # z-plane and the mesh
        if self.slices[CUT_EXACT].n_cells == 0:
            return mesh

        if split_cells:
            extract_ids = self.split_ids
        else:
            whole_ids = set(self.slices[bias][GV_CELL_IDS]).difference(self.split_ids)
            extract_ids = whole_ids

        if extract_ids:
            mesh = cast(self.mesh.extract_cells(np.array(list(extract_ids))))
            if clip:
                lonlat = to_xy0(mesh)
                match = np.abs(lonlat[:, 0] - self.meridian) < 90
                mesh = cast(mesh.extract_points(match))
            sanitize_data(mesh)
            if mesh.n_cells:
                mesh.set_active_scalars(
                    self._info.name, preference=self._info.association.name.lower()
                )

        return mesh


def add_texture_coords(
    mesh: pv.PolyData,
    meridian: Optional[float] = None,
    antimeridian: Optional[bool] = False,
) -> pv.PolyData:
    """
    Compute and attach texture coordinates, in UV space, of the mesh.

    Note that, the mesh will be sliced along the `meridian` to ensure that
    cell connectivity is appropriately disconnected prior to texture mapping.

    Parameters
    ----------
    mesh : PolyData
        The mesh that requires texture coordinates.
    meridian : float, optional
        The meridian (degrees longitude) to slice along.
    antimeridian : bool, default=False
        Whether to flip the given `meridian` to use its anti-meridian instead.

    Returns
    -------
    PolyData
        The original mesh with inplace texture coordinates attached.

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
    lonlat = to_xy0(mesh, closed_interval=True)
    lons, lats = lonlat[:, 0], lonlat[:, 1]
    # convert to normalised UV space
    u_coord = (lons + 180) / 360
    v_coord = (lats + 90) / 180
    t_coord = np.vstack([u_coord, v_coord]).T
    mesh.active_t_coords = t_coord

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
            faces_n = np.diff(mesh._offset_array)
            # determine the N offset for each face within the faces array
            # a face entry consists of (N, v1, v2, ..., vN), where vN is the Nth
            # vertex offset (connectivity) for that face into the associated mesh points array
            faces_n_offset = mesh._offset_array + np.arange(mesh._offset_array.size)
            # offset the current mesh connectivity by the cumulative mesh points count
            faces += n_points
            # reinstate N for each face entry
            faces[faces_n_offset[:-1]] = faces_n

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
    rtol: Optional[float] = None,
    atol: Optional[float] = None,
) -> pv.PolyData:
    """
    Create a seam along the `meridian` of the geo-located `mesh`, from the
    north pole to the south pole, breaking cell connectivity thus allowing
    the mesh to be correctly projected or texture mapped.

    Cells bisected by the `meridian` of choice will be remeshed i.e., split
    and triangulated.

    Parameters
    ----------
    mesh : PolyData
        The mesh to be sliced along the `meridian`.
    meridian : float, optional
        The meridian (degrees longitude) to slice along.
    antimeridian : bool, default=False
        Whether to flip the given `meridian` to use its anti-meridian instead.
    rtol : float, optional
        The relative tolerance for values close to longitudinal
        :func:`geovista.common.wrap` base + period.
    atol : float, optional
        The absolute tolerance for values close to longitudinal
        :func:`geovista.common.wrap` base + period.

    Returns
    -------
    PolyData
        The mesh with a seam along the meridian and remeshed cells, if
        bisected.

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

    info = mesh.active_scalars_info
    slicer = MeridianSlice(mesh, meridian)
    mesh_whole = slicer.extract(split_cells=False)
    mesh_split = slicer.extract(split_cells=True)
    result: pv.PolyData = mesh.copy(deep=True)

    meshes = []
    remeshed_ids = np.array([], dtype=int)

    if mesh_whole.n_cells:
        lonlat = to_xy0(mesh_whole, rtol=rtol, atol=atol)
        meridian_mask = np.isclose(lonlat[:, 0], meridian)
        join_points = np.empty(mesh_whole.n_points, dtype=int)
        join_points.fill(REMESH_JOIN)
        mesh_whole[GV_REMESH_POINT_IDS] = join_points
        mesh_whole[GV_REMESH_POINT_IDS][meridian_mask] = REMESH_SEAM
        meshes.append(mesh_whole)
        remeshed_ids = mesh_whole[GV_CELL_IDS]
        result[GV_REMESH_POINT_IDS] = result[GV_POINT_IDS].copy()

    if mesh_split.n_cells:
        remeshed, remeshed_west, remeshed_east = remesh(
            mesh_split, meridian, rtol=rtol, atol=atol
        )
        meshes.extend([remeshed_west, remeshed_east])
        remeshed_ids = np.hstack([remeshed_ids, remeshed[GV_CELL_IDS]])
        if GV_REMESH_POINT_IDS not in result.point_data:
            result.point_data[GV_REMESH_POINT_IDS] = result[GV_POINT_IDS].copy()

        # XXX: defensive removal of cells that span the meridian and should
        # have been remeshed, but haven't due to their geometry ?
        cids = set(find_cell_neighbours(result, remeshed[GV_CELL_IDS]))
        cids = cids.difference(set(remeshed_ids))
        if cids:
            neighbours = result.extract_cells(list(cids))
            xy0 = to_xy0(neighbours)
            neighbours.points = xy0
            xdelta = []
            for cid in range(neighbours.n_cells):
                # XXX: pyvista 0.38.0: cell_points(cid) -> get_cell(cid).points
                cxpts = neighbours.cell_points(cid)[:, 0]
                cxmin, cxmax = cxpts.min(), cxpts.max()
                xdelta.append(cxmax - cxmin)
            xdelta = np.array(xdelta)
            bad = np.where(xdelta > 270)[0]
            if bad.size:
                bad_cids = np.unique(neighbours[GV_CELL_IDS][bad])
                plural = "s" if (n_cells := bad_cids.size) > 1 else ""
                naughty = ", ".join([f"{cid}" for cid in bad_cids])
                wmsg = (
                    f"Unable to remesh {n_cells} cell{plural}. Removing the "
                    f"following mesh cell-id{plural} [{naughty}]."
                )
                warnings.warn(wmsg)
                remeshed_ids = np.hstack([remeshed_ids, bad_cids])

    if meshes:
        result.remove_cells(np.unique(remeshed_ids), inplace=True)
        result = combine(result, *meshes)

    result.set_active_scalars(name=None)
    result.set_active_scalars(info.name, preference=info.association.name.lower())

    return result


def is_projected(mesh: pv.PolyData) -> bool:
    """
    Determine whether the provided mesh is a planar projection by inspecting
    the associated CRS or the mesh geometry.

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


def resize(mesh: pv.PolyData, radius: Optional[float] = None) -> pv.PolyData:
    """
    Change the radius of the spherical mesh.

    Parameters
    ----------
    mesh : PolyData
        The mesh to be resized to the provided ``radius``.
    radius : float, default=1.0
        The target radius of the ``mesh``.

    Returns
    -------
    PolyData
        The resized mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if is_projected(mesh):
        emsg = "Cannot resize mesh that appears to be a planar projection."
        raise ValueError(emsg)

    if radius is None:
        radius = RADIUS

    if radius and not np.isclose(calculate_radius(mesh), radius):
        lonlat = to_xy0(mesh)
        xyz = to_xyz(lonlat[:, 0], lonlat[:, 1], radius=radius)
        mesh.points = xyz
        mesh.field_data[GV_FIELD_RADIUS] = np.array([radius])

    return mesh
