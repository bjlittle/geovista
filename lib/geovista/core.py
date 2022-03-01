from collections.abc import Iterable
from enum import Enum, auto, unique
from typing import List, Optional

import numpy as np
import pyvista as pv

from .common import VTK_CELL_IDS, VTK_POINT_IDS, to_xy0, wrap
from .filters import cast_UnstructuredGrid_to_PolyData as cast
from .log import get_logger

__all__ = ["Slicer", "combine"]

# Configure the logger.
logger = get_logger(__name__)

#: Preference for a slice to be west of the chosen meridian.
CUT_WEST: str = "west"

#: Preference for a slice to be true to the chosen meridian.
CUT_EXACT: str = "exact"

#: Preference for a slice to be east of the chosen meridian.
CUT_EAST: str = "east"


@unique
class SlicerBias(Enum):
    west = -1
    exact = auto()
    east = auto()


def combine(
    meshes: List[pv.PolyData],
    data: Optional[bool] = True,
    clean: Optional[bool] = False,
) -> pv.PolyData:
    """
    Combine two or more meshes into one mesh.

    Only meshes with faces will be combined. Support is not provided for combining
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
        and/or remove degenerate cells in the resultant mesh.

    Returns
    -------
    PolyData
        The input meshes combined into a single :class:`pyvista.PolyData`.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if not isinstance(meshes, Iterable):
        meshes = [meshes]

    if len(meshes) == 1:
        return meshes[0]

    first: pv.PolyData = meshes[0]
    combined_points, combined_faces = [], []
    active_scalars = []
    n_points, n_faces = 0, 0

    if data:
        # determine the common point, cell and field array names
        # attached to the input meshes - these will be combined and
        # attached to the resultant combined mesh
        common_point_data = set(first.point_data.keys())
        common_cell_data = set(first.cell_data.keys())
        common_field_data = set(first.field_data.keys())

    for i, mesh in enumerate(meshes):
        if not isinstance(mesh, pv.PolyData):
            dtype = repr(type(mesh)).split(" ")[1][:-1]
            emsg = (
                f"Can only combine 'pyvista.PolyData' meshes, input mesh "
                f"#{i+1} has type {dtype}."
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

        combined_points.append(mesh.points)
        N = sorted(set(np.diff(mesh._offset_array)))

        if len(N) != 1:
            npts = f"{', '.join([str(n) for n in N[:-1]])} and {N[-1]}"
            emsg = (
                "Cannot combine meshes with a surface containing mixed face "
                f"types, input mesh #{i+1} has faces with {npts} points."
            )
            raise TypeError(emsg)

        (N,) = N
        connectivity = mesh._connectivity_array.reshape(-1, N)
        faces_N = np.broadcast_to(
            np.array([N], dtype=np.int8), (connectivity.shape[0], 1)
        )

        if n_points:
            # offset the current mesh connectivity by previous combined
            # mesh points
            connectivity += n_points

        # create the current mesh face connectivity
        faces = np.hstack([faces_N, connectivity])
        combined_faces.append(np.ravel(faces))
        # accumulate running totals of combined mesh points and faces
        n_points += mesh.points.shape[0]
        n_faces += faces_N.shape[0]

        if data:
            # perform intersection to determine common names
            common_point_data &= set(mesh.point_data.keys())
            common_cell_data &= set(mesh.cell_data.keys())
            common_field_data &= set(mesh.field_data.keys())
            if mesh.active_scalars_name:
                active_scalars.append(mesh.active_scalars_name)

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
        for name in active_scalars:
            if name in common_point_data or name in common_cell_data:
                combined.active_scalars_name = first.active_scalars_name
                break

    # remove degenerate points and faces
    if clean:
        combined.clean(inplace=True)

    return combined


class Slicer:
    def __init__(
        self,
        mesh: pv.PolyData,
        meridian: float,
        offset: Optional[float] = None,
    ):
        """
        TBD

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

        # TBD: require a more robust and definitive approach
        zmin, zmax = mesh.bounds[4], mesh.bounds[5]
        if np.isclose(zmax - zmin, 0):
            emsg = "Cannot slice mesh appears to be a planar projection."
            raise ValueError(emsg)

        self.mesh = mesh
        mesh[VTK_CELL_IDS] = np.arange(mesh.n_cells)
        mesh[VTK_POINT_IDS] = np.arange(mesh.n_points)
        self.xmin, self.xmax = mesh.bounds[0], mesh.bounds[1]

        if offset is None:
            # default to a crude approximation of a projected equatorial
            # arcsecond of longitude
            offset = ((self.xmax - self.xmin) / 2) / (3600 * 90)

        self.meridian = wrap(meridian)[0]
        self.offset = abs(offset)
        logger.debug(
            f"meridian={self.meridian}, offset={self.offset}", extra=self._extra
        )
        self.slices = {bias.name: self._intersection(bias.value) for bias in SlicerBias}

        n_cells = self.slices[CUT_EXACT].n_cells
        self.west_ids = set(self.slices[CUT_WEST][VTK_CELL_IDS]) if n_cells else set()
        self.east_ids = set(self.slices[CUT_EAST][VTK_CELL_IDS]) if n_cells else set()
        self.split_ids = self.west_ids.intersection(self.east_ids)
        logger.debug(
            f"west={len(self.west_ids)}, east={len(self.east_ids)}, "
            f"split={len(self.split_ids)}",
            extra=self._extra,
        )

    def _intersection(self, bias: float) -> pv.PolyData:
        """
        TBD

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
        xyz = pv.Line((self.xmin, y, 0), (self.xmax, y, 0))
        xyz.rotate_z(self.meridian, inplace=True)
        spline = pv.Spline(xyz.points, 1)
        mesh = self.mesh.slice_along_line(spline)
        mesh.active_scalars_name = None
        logger.debug(
            f"n_cells={mesh.n_cells}, n_points={mesh.n_points}", extra=self._extra
        )
        return mesh

    def extract(
        self,
        bias: Optional[str] = None,
        whole_cells: Optional[bool] = True,
        split_cells: Optional[bool] = True,
        clip: Optional[bool] = True,
    ) -> pv.PolyData:
        """
        TBD

        Parameters
        ----------
        bias
        whole_cells
        split_cells
        clip

        Returns
        -------

        Notes
        -----
        .. versionadded :: 0.1.0

        """
        if bias is None:
            bias = CUT_WEST

        if bias.lower() not in SlicerBias.__members__:
            options = [f"'{option.name}'" for option in SlicerBias]
            options = f"{', '.join(options[:-1])} or {options[-1]}"
            emsg = f"Expected a slice bias of either {options}, got '{bias}'."
            raise ValueError(emsg)

        # there is no intersection between the z-plane extruded by
        # the spline and the mesh
        if (mesh := self.slices[CUT_EXACT].n_cells) == 0:
            return mesh

        extract_ids = set()
        mesh = pv.PolyData()

        if whole_cells:
            whole_ids = set(self.slices[bias][VTK_CELL_IDS]).difference(self.split_ids)
            logger.debug(f"{bias=}, whole={len(whole_ids)}", extra=self._extra)
            extract_ids = whole_ids

        if split_cells:
            logger.debug(f"split={len(self.split_ids)}", extra=self._extra)
            extract_ids = extract_ids.union(self.split_ids)

        logger.debug(f"extract={len(extract_ids)}", extra=self._extra)

        if extract_ids:
            mesh = self.mesh.extract_cells(np.array(list(extract_ids)))
            mesh.active_scalars_name = None
            logger.debug(
                f"mesh: {bias=}, n_cells={mesh.n_cells}, " f"n_points={mesh.n_points}",
                extra=self._extra,
            )
            if clip:
                # cc = mesh.cell_centers()
                # points = to_xy0(cc.points)
                # if np.isclose(meridian, -180):
                #     match = (180 - np.abs(points[:, 0])) < 90
                # else:
                #     match = np.abs(points[:, 0] - meridian) < 90
                # mesh = cast(mesh.extract_cells(match))
                points = to_xy0(mesh.points)
                match = np.abs(points[:, 0] - self.meridian) < 90
                mesh = cast(mesh.extract_points(match))
                logger.debug(
                    f"clip: {bias=}, n_cells={mesh.n_cells}, "
                    f"n_points={mesh.n_points}",
                    extra=self._extra,
                )
        else:
            logger.debug("no cells extracted from slice", extra=self._extra)

        return mesh
