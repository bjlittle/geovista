from collections.abc import Iterable
from typing import List, Optional

import numpy as np
import pyvista as pv

from .log import get_logger

__all__ = ["combine"]

# Configure the logger.
logger = get_logger(__name__)


def combine(meshes: List[pv.PolyData], data: Optional[bool] = True) -> pv.PolyData:
    """
    Combine two or more meshes into one mesh.

    Only meshes with faces will be combined. Support is not provided for combining
    meshes that consist of only points or lines.

    Note that, no check is performed to ensure that mesh faces do not overlap.
    However, meshes may share coincident points. Coincident point data from the
    first input mesh will overwrite all other mesh data sharing the same
    coincident point.

    Parameters
    ----------
    meshes : iterable of PolyData
        The meshes to be combined into a single :class:`pyvista.PolyData` mesh.
    data : bool, default=True
        Whether to also combine and attach common data from the meshes onto
        the resultant mesh.

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
    combined.clean(inplace=True)

    return combined
