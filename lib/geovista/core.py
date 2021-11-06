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
    TBD

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
    n_points, n_faces = 0, 0
    if data:
        point_data = set(first.point_data.keys())
        cell_data = set(first.cell_data.keys())
        field_data = set(first.field_data.keys())

    for i, mesh in enumerate(meshes):
        if not isinstance(mesh, pv.PolyData):
            dtype = repr(type(mesh)).split(" ")[1][:-1]
            emsg = (
                f"Can only combine 'pyvista.PolyData' meshes, mesh {i+1} "
                f"has type {dtype}."
            )
            raise TypeError(emsg)

        combined_points.append(mesh.points)
        N = sorted(set(np.diff(mesh._offset_array)))

        if len(N) != 1:
            npts = f"{', '.join([str(n) for n in N[:-1]])} and {N[-1]}"
            emsg = (
                "Cannot combine meshes with a surface containing mixed face "
                f"types, mesh {i+1} has faces with {npts} points."
            )
            raise TypeError(emsg)

        (N,) = N
        connectivity = mesh._connectivity_array.reshape(-1, N)
        faces_N = np.broadcast_to(
            np.array([N], dtype=np.int8), (connectivity.shape[0], 1)
        )

        if n_points:
            connectivity += n_points

        faces = np.hstack([faces_N, connectivity])
        combined_faces.append(np.ravel(faces))
        n_points += mesh.points.shape[0]
        n_faces += faces_N.shape[0]

        if data:
            point_data |= set(mesh.point_data.keys())
            cell_data |= set(mesh.cell_data.keys())
            field_data |= set(mesh.field_data.keys())

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
        combine_data(point_data)
        combine_data(cell_data)
        combine_data(field_data, field=True)
        combined.active_scalars_name = first.active_scalars_name

    combined.clean(inplace=True)

    return combined
