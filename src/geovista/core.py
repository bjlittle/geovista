"""Core geovista behaviour for processing geolocated meshes.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

import copy
from enum import Enum, auto, unique
from typing import Any
import warnings

import numpy as np
from numpy.typing import ArrayLike
import pyvista as pv

from .common import (
    CENTRAL_MERIDIAN,
    GV_CELL_IDS,
    GV_FIELD_RADIUS,
    GV_FIELD_ZSCALE,
    GV_POINT_IDS,
    GV_REMESH_POINT_IDS,
    RADIUS,
    REMESH_JOIN,
    REMESH_SEAM,
    ZLEVEL_SCALE,
    distance,
    from_cartesian,
    point_cloud,
    sanitize_data,
    to_cartesian,
    wrap,
)
from .common import cast_UnstructuredGrid_to_PolyData as cast
from .crs import projected
from .filters import remesh
from .search import find_cell_neighbours

__all__ = [
    "MeridianSlice",
    "add_texture_coords",
    "combine",
    "resize",
    "slice_cells",
    "slice_lines",
    "slice_mesh",
]

#: Preference for a slice to bias cells west of the chosen meridian.
CUT_WEST: str = "WEST"

#: Preference for a slice to be true to the chosen meridian.
CUT_EXACT: str = "EXACT"

#: Preference for a slice to bias cells east of the chosen meridian.
CUT_EAST: str = "EAST"

#: Cartesian west/east bias offset of a slice.
CUT_OFFSET: float = 1e-5

#: The default number of interpolation points along a spline.
SPLINE_N_POINTS: int = 1


@unique
class SliceBias(Enum):
    """Enumerate meridian slice bias."""

    WEST = -1
    EXACT = auto()
    EAST = auto()


class MeridianSlice:
    """Remesh geolocated mesh along a meridian, from the north-pole to the south-pole.

    Remeshing involves introducing a seam into the mesh along the meridian
    of choice, splitting cells bisected by the meridian, which will be
    triangulated.

    """

    def __init__(
        self,
        mesh: pv.PolyData,
        meridian: float,
        offset: float | None = None,
    ) -> None:
        """Create a `meridian` seam in the `mesh`.

        The seam extends from the north-pole to the south-pole in a great circle,
        breaking cell connectivity and thus allowing the geolocated mesh to be
        correctly projected or texture mapped.

        Cells bisected by the `meridian` of choice will be remeshed i.e., split
        and triangulated.

        Parameters
        ----------
        mesh : PolyData
            The geolocated mesh to be remeshed along the `meridian`.
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
        if projected(mesh):
            emsg = "Cannot slice a mesh that has been projected."
            raise ValueError(emsg)

        self._info = mesh.active_scalars_info
        mesh[GV_CELL_IDS] = np.arange(mesh.n_cells)
        mesh[GV_POINT_IDS] = np.arange(mesh.n_points)
        mesh.set_active_scalars(name=None)
        mesh.set_active_scalars(
            self._info.name, preference=self._info.association.name.lower()
        )
        self.mesh = mesh
        self.radius = distance(mesh)
        self.meridian = wrap(meridian)[0]
        self.offset = abs(CUT_OFFSET if offset is None else offset)
        self.slices = {bias.name: self._intersection(bias) for bias in SliceBias}

        n_cells = self.slices[CUT_EXACT].n_cells
        self.west_ids = set(self.slices[CUT_WEST][GV_CELL_IDS]) if n_cells else set()
        self.east_ids = set(self.slices[CUT_EAST][GV_CELL_IDS]) if n_cells else set()
        self.split_ids = self.west_ids.intersection(self.east_ids)

    def _intersection(
        self, bias: SliceBias, n_points: float | None = None
    ) -> pv.PolyData:
        """Perform the meridian intersection with the mesh.

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
            :data:`SPLINE_N_POINTS`.

        Returns
        -------
        PolyData
            The cells of the mesh that are coincident or bisected by the slice.

        Notes
        -----
        .. versionadded :: 0.1.0

        """
        if n_points is None:
            n_points = SPLINE_N_POINTS

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
        bias: str | None = None,
        split_cells: bool | None = False,
        clip: bool | None = True,
    ) -> pv.PolyData:
        """Reduce mesh to only the cells intersecting with the meridian.

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
                lonlat = from_cartesian(mesh)
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
    meridian: float | None = None,
    antimeridian: bool | None = False,
) -> pv.PolyData:
    """Compute and attach texture coordinates, in UV space, to the mesh.

    Note that, the mesh will be sliced along the `meridian` to ensure that
    cell connectivity is appropriately disconnected prior to texture mapping.

    Parameters
    ----------
    mesh : PolyData
        The mesh that requires texture coordinates.
    meridian : float, optional
        The meridian (degrees longitude) to slice along. Defaults to
        :data:`geovista.common.CENTRAL_MERIDIAN`.
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
    if point_cloud(mesh):
        # don't attach texture coordinates to a point-cloud
        return mesh

    if meridian is None:
        meridian = CENTRAL_MERIDIAN

    if antimeridian:
        meridian += 180

    meridian = wrap(meridian)[0]

    if GV_REMESH_POINT_IDS not in mesh.point_data:
        mesh = slice_cells(mesh, meridian=meridian)
    else:
        mesh = mesh.copy(deep=True)

    # convert from cartesian xyz to spherical lat/lons
    lonlat = from_cartesian(mesh, closed_interval=True)
    lons, lats = lonlat[:, 0], lonlat[:, 1]
    # convert to normalised UV space
    u_coord = (lons + 180) / 360
    v_coord = (lats + 90) / 180
    t_coord = np.vstack([u_coord, v_coord]).T
    mesh.active_texture_coordinates = t_coord

    return mesh


def combine(
    *meshes: Any,
    data: bool | None = True,
    clean: bool | None = False,
) -> pv.PolyData:
    """Combine two or more meshes into one mesh.

    Only meshes with cells will be combined. Support is not yet provided for combining
    meshes that consist of only points or lines.

    Note that, no check is performed to ensure that mesh cells do not overlap.
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
        and/or remove degenerate cells in the resultant mesh.

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
        active_scalars_info = {first.active_scalars_info._namedtuple}

    for i, mesh in enumerate(meshes):
        if not isinstance(mesh, pv.PolyData):
            emsg = (
                f"Can only combine 'pyvista.PolyData' meshes, input mesh "
                f"#{i+1} has type '{mesh.__class__.__name__}'."
            )
            raise TypeError(emsg)

        if mesh.n_lines:
            emsg = (
                f"Can only combine meshes with cells, input mesh #{i+1} "
                "contains lines."
            )
            raise TypeError(emsg)

        if mesh.n_cells == 0:
            emsg = (
                f"Can only combine meshes with cells, input mesh #{i+1} "
                "has no cells."
            )
            raise TypeError(emsg)

        combined_points.append(mesh.points.copy())
        faces = mesh.faces.copy()

        if n_points:
            # compute the number of vertices (N) for each face of the mesh
            faces_n = np.diff(mesh._offset_array)
            # determine the N offset for each face within the faces array
            # a face entry consists of (N, v1, v2, ..., vN), where vN is the Nth
            # vertex offset (connectivity) for that face into the associated mesh
            # points array
            faces_n_offset = mesh._offset_array + np.arange(mesh._offset_array.size)
            # offset the current mesh connectivity by the cumulative mesh points count
            faces += n_points
            # reinstate N for each face entry
            faces[faces_n_offset[:-1]] = faces_n

        combined_faces.append(faces)
        # accumulate running totals of combined mesh points and cells
        n_points += mesh.n_points
        n_faces += mesh.n_cells

        if data:
            # perform intersection to determine common names
            common_point_data &= set(mesh.point_data.keys())
            common_cell_data &= set(mesh.cell_data.keys())
            common_field_data &= set(mesh.field_data.keys())
            if mesh.active_scalars_name:
                active_scalars_info &= {mesh.active_scalars_info._namedtuple}

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


def resize(
    mesh: pv.PolyData,
    radius: float | None = None,
    zlevel: int | None = None,
    zscale: float | None = None,
    inplace: bool | None = False,
) -> pv.PolyData:
    """Change the radius of the spherical mesh.

    Parameters
    ----------
    mesh : PolyData
        The mesh to be resized to the provided ``radius``.
    radius : float, optional
        The target radius of the ``mesh``. Defaults to :data:`geovista.common.RADIUS`.
    zlevel : int, default=0
        The z-axis level. Used in combination with the `zscale` to offset the
        `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
    zscale : float, optional
        The proportional multiplier for z-axis `zlevel`. Defaults to
        :data:`geovista.common.ZLEVEL_SCALE`.
    inplace : boolean, default=False
        Update `mesh` in-place.

    Returns
    -------
    PolyData
        The resized mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if projected(mesh):
        emsg = "Cannot resize a mesh that has been projected."
        raise ValueError(emsg)

    cloud = point_cloud(mesh)

    if radius is None:
        if cloud and GV_FIELD_RADIUS in mesh.field_data:
            radius = mesh[GV_FIELD_RADIUS][0]
        else:
            radius = RADIUS
    else:
        radius = abs(float(radius))

    if zscale is None:
        if cloud and GV_FIELD_ZSCALE in mesh.field_data:
            zscale = mesh[GV_FIELD_ZSCALE][0]
        else:
            zscale = ZLEVEL_SCALE
    else:
        zscale = float(zscale)

    zlevel = 0 if zlevel is None else int(zlevel)

    if cloud:
        update = bool(zlevel)
        if not update:
            update = GV_FIELD_ZSCALE not in mesh.field_data or not np.isclose(
                mesh[GV_FIELD_ZSCALE], zscale
            )
        if not update:
            update = GV_FIELD_RADIUS not in mesh.field_data or not np.isclose(
                mesh[GV_FIELD_RADIUS], radius
            )
    else:
        new_radius = radius + radius * zlevel * zscale
        update = new_radius and not np.isclose(distance(mesh), new_radius)

    if update:
        lonlat = from_cartesian(mesh)
        if cloud:
            zlevel += lonlat[:, 2]
        xyz = to_cartesian(
            lonlat[:, 0], lonlat[:, 1], radius=radius, zlevel=zlevel, zscale=zscale
        )
        if not inplace:
            mesh = mesh.copy()
        mesh.points = xyz
        if cloud:
            mesh.field_data[GV_FIELD_ZSCALE] = np.array([zscale])
        else:
            radius = new_radius
        mesh.field_data[GV_FIELD_RADIUS] = np.array([radius])

    return mesh


def slice_cells(
    mesh: pv.PolyData,
    meridian: float | None = None,
    antimeridian: bool | None = False,
    rtol: float | None = None,
    atol: float | None = None,
) -> pv.PolyData:
    """Cut the mesh along the `meridian`, breaking cell connectivity.

    Create a seam along the `meridian` of the geolocated `mesh`, from the
    north-pole to the south-pole, breaking cell connectivity thus allowing
    the mesh to be correctly transformed (projected) or texture mapped.

    Cells bisected by the `meridian` of choice will be remeshed i.e., split
    and triangulated.

    Parameters
    ----------
    mesh : PolyData
        The mesh to be sliced along the `meridian`.
    meridian : float, optional
        The meridian (degrees longitude) to slice along. Defaults to
        :data:`geovista.common.CENTRAL_MERIDIAN`.
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
        emsg = f"Require a {str(pv.PolyData)!r} mesh, got {str(type(mesh))!r}."
        raise TypeError(emsg)

    if point_cloud(mesh) or mesh.n_lines:
        # no cell remeshing required for a point-cloud or line mesh
        return mesh

    if meridian is None:
        meridian = CENTRAL_MERIDIAN

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
        lonlat = from_cartesian(mesh_whole, rtol=rtol, atol=atol)
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
            neighbours = cast(result.extract_cells(list(cids)))
            xy0 = from_cartesian(neighbours)
            neighbours.points = xy0
            xdelta = []
            for cid in range(neighbours.n_cells):
                # XXX: pyvista 0.38.0: cell_points(cid) -> get_cell(cid).points
                cxpts = neighbours.get_cell(cid).points[:, 0]
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
                warnings.warn(wmsg, stacklevel=2)
                remeshed_ids = np.hstack([remeshed_ids, bad_cids])

    if meshes:
        result.remove_cells(np.unique(remeshed_ids), inplace=True)
        # reinstate field data purged by remove_cells
        for field in mesh.field_data.keys():
            result.field_data[field] = copy.deepcopy(mesh.field_data[field])
        result = combine(result, *meshes)

    result.set_active_scalars(name=None)
    result.set_active_scalars(info.name, preference=info.association.name.lower())

    return result


def slice_lines(
    mesh: pv.PolyData, n_points: int | None = None, copy: bool | None = False
) -> pv.PolyData:
    """Cut the line mesh along the antimeridian, breaking line connectivity.

    The connectivity of any line segment in the mesh traversing the antimeridian will be
    broken. Each end-point of the segment will be connected to a new interior point,
    located at the point of intersection between the line segment and the antimeridian
    i.e., the segment will be split into two separate, disjointed segments. If the
    end-point of a segment lies on the antimeridian, then it is replaced with an
    identical but distinct co-located point.

    This operation is typically performed prior to reprojection in order to create a
    seam in the line segments.

    The mesh is sliced with a z-x plane formed by extruding a line on the x-axis along
    the z-axis.

    Parameters
    ----------
    mesh : PolyData
        The line mesh that requires to be sliced.
    n_points : int, optional
        The number of intermediate points for the line that will be extruded to form a
        plane which will slice the `mesh` e.g., with ``n_points=1``, a mid-point will be
        calculated for the line, which will then consist of 2 line segments i.e., the 2
        end-points and 1 mid-point. Defaults to :data:`SPLINE_N_POINTS`.
    copy : bool, default=False
        Return a deepcopy of the ``mesh`` when there are no points of intersection with
        the antimeridian. Otherwise, the original ``mesh`` is returned.

    Returns
    -------
    PolyData
        The line mesh with a seam along the antimeridian, if bisected.

    Notes
    -----
    .. versionadded:: 0.3.0

    """
    if projected(mesh):
        emsg = "Cannot slice a mesh that has been projected."
        raise ValueError(emsg)

    if mesh.n_lines == 0:
        # there are no lines to slice
        return mesh

    if n_points is None:
        n_points = SPLINE_N_POINTS

    if n_points < 1:
        wmsg = f"Ignoring 'n_points={n_points}', defaulting to 'n_points=1'."
        warnings.warn(wmsg, stacklevel=2)

    # check whether the line is completely aligned with the slice plane
    # that passes through the anti-meridian
    lonlat = from_cartesian(mesh)
    antimeridian = np.isclose(np.abs(lonlat[:, 0]), 180)

    # nop - all points intersect
    if np.all(antimeridian):
        if copy:
            mesh = mesh.copy(deep=True)
        return mesh

    radius = distance(mesh)
    line = pv.Line(pointa=(radius, 0, 0), pointb=(-radius, 0, 0))
    spline = pv.Spline(line.points, n_points=n_points + 2)
    intersection = mesh.slice_along_line(spline)
    lonlat = from_cartesian(intersection)
    antimeridian = np.isclose(np.abs(lonlat[:, 0]), 180)

    # nop - there are no points of intersection
    if antimeridian.sum() == 0:
        if copy:
            mesh = mesh.copy(deep=True)
        return mesh

    # antimeridian points-of-interest (N, 3)
    poi_xyz = intersection.points[antimeridian]

    # there is 1 cid per intersection poi (N,)
    poi_cids = mesh.find_closest_cell(poi_xyz)
    # there are 2 pids per cid i.e., by defn, each line has 2 end-points
    cid_pids = [mesh.get_cell(cid).point_ids for cid in poi_cids]
    # flatten the pids (2N,)
    cid_pids_1d = np.concatenate(cid_pids)
    # flatten the cartesian points (2N, 3)
    cid_xyz_1d = np.concatenate([mesh.points[pids] for pids in cid_pids])

    # use explicit typing for clarity ...
    split_cids: list[int] = []
    split_xyz: list[ArrayLike] = []
    detach_cids: list[int] = []
    detach_pids: list[int] = []

    for xyz, cid in zip(poi_xyz, poi_cids):
        mask = np.all(np.isclose(cid_xyz_1d, xyz), axis=1)
        if np.any(mask):
            # we want to detach the connectivity of a single line segment at the pid
            # i.e., replace the pid with a new co-located xyz point
            intersection_pid = np.unique(cid_pids_1d[mask])
            if (count := intersection_pid.size) > 1:
                # detected a loop containing different line segments with
                # coincident end-points at the intersection poi
                emsg = f"Expected only 1 line segment end-point, got {count} instead."
                raise ValueError(emsg)

            detach_cids.append(cid)
            detach_pids.append(intersection_pid[0])
        else:
            # we want to break the connectivity of the line segment @ xyz
            # i.e., split the segment into two new segments about xyz
            split_cids.append(cid)
            split_xyz.append(xyz)

    result = pv.PolyData()
    points = mesh.points.copy()
    lines = mesh.lines.copy().reshape(-1, 3)

    if split_cids:
        # for M points of intersection, introduce 2xM new xyz cartesian intersection
        # points and M cells i.e.,
        #        cid                    cid                       cid(new)
        # pid(0) --- pid(1)  =>  pid(0) --- pid(new0) & pid(new1) -------- pid(1)
        #                             [step1]                     [step2]
        # where, pid(new0) and pid(new1) are distinct pids but reference identical, but
        # not the same cartesian xyz point
        #
        # [step1]
        n_points = points.shape[0]
        split_points = np.vstack(split_xyz)
        points = np.vstack([points, split_points])  # append M points
        new_pids = np.arange(n_points, points.shape[0])
        split_lines = lines[split_cids]
        lines[split_cids, 2] = new_pids  # inplace M cells
        # [step2]
        n_points = points.shape[0]
        points = np.vstack([points, split_points])  # append M points
        new_pids = np.arange(n_points, points.shape[0])
        split_lines[:, 1] = new_pids
        lines = np.vstack([lines, split_lines])  # append M new cells

    if detach_cids:
        # for M points of intersection, introduce M new xyz cartesian intersection
        # points i.e.,
        #        cid0        cid1                    cid0                   cid1
        # pid(0) ---- pid(1) ---- pid(2)  =>  pid(0) ---- pid(new) & pid(1) ---- pid(2)
        #                                                                   [nop]
        # where, pid(new) and pid(1) are distinct pids but reference identical, but not
        # the same cartesian xyz point
        #
        # find the location of the pids
        line_pids = lines[detach_cids, 1:]
        pids = np.asanyarray(detach_pids).reshape(-1, 1)
        pids = np.broadcast_to(pids, (pids.size, 2))
        delta = line_pids - pids
        replace_idx = np.where(delta == 0)
        # create new identical points and reference them with new pids
        n_points = points.shape[0]
        points = np.vstack([points, points[detach_pids]])  # append M points
        new_pids = np.arange(n_points, points.shape[0])
        line_pids[replace_idx] = new_pids
        lines[detach_cids, 1:] = line_pids  # inplace M cells

    if mesh.field_data.keys():
        for key in mesh.field_data.keys():
            result.field_data[key] = mesh.field_data[key].copy()

    # TDB: given mesh.points, perform linear interpolation for new intersection points

    result.points = points
    result.lines = lines

    return result


def slice_mesh(
    mesh: pv.PolyData,
    rtol: float | None = None,
    atol: float | None = None,
) -> pv.PolyData:
    """Cut the mesh along the antimeridian, breaking line connectivity.

    A point-cloud cannot be sliced as there are no cells or lines, and will be
    returned unaltered. Otherwise, a new instance of the mesh will be returned
    regardless of whether it has been bisected or not.

    Also see :func:`geovista.core.slice_lines` and :func:`geovista.core.slice_cells`
    for further details.

    Parameters
    ----------
    mesh : PolyData
        The mesh that requires to be sliced.
    rtol : float, optional
        The relative tolerance for values close to longitudinal
        :func:`geovista.common.wrap` base + period.
    atol : float, optional
        The absolute tolerance for values close to longitudinal
        :func:`geovista.common.wrap` base + period.

    Returns
    -------
    PolyData
        The mesh with a seam along the antimeridian, if bisected.

    Notes
    -----
    .. versionadded:: 0.3.0

    """
    if projected(mesh):
        emsg = "Cannot slice a mesh that has been projected."
        raise ValueError(emsg)

    result = (
        slice_lines(mesh, copy=True)
        if mesh.n_lines
        else slice_cells(mesh, antimeridian=True, rtol=rtol, atol=atol)
    )

    return result
