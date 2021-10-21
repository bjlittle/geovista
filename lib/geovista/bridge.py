from typing import Optional, Union

import numpy as np
from numpy.typing import ArrayLike
import pyvista as pv

from .common import nan_mask, to_xyz, wrap
from .log import get_logger

#
# the bridge is under construction - walk carefully ;-)
#
# TODO: change the following pattern to be completely agnostic of cubes, in fact
# agnostic of any third-party that wants to use geovista. simply adopt the
# philosophy of providing the tools to massage their data into one of several
# use patterns that ultimately generate a mesh.
#

try:
    # XXX: currently require "iris/main" pre-3.2.0 functionality
    from iris.cube import Cube
    from iris.experimental.ugrid.mesh import Mesh
except ImportError:
    iris, Cube, Mesh = None, None, None


__all__ = ["Transform"]

# Configure the logger.
logger = get_logger(__name__)


class Transform:
    @classmethod
    def from_cube(
        cls, cube: Cube, location: Optional[bool] = True, cidxs: Optional[bool] = True
    ) -> pv.PolyData:
        """
        TBD

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if cube.mesh is None:
            emsg = "Require an iris cube with an unstructured mesh."
            raise TypeError(emsg)

        # TODO: relax this restriction to support an additional structured
        # cube dimension e.g., a 2D unstructured time-series cube.
        if cube.ndim != 1:
            emsg = (
                "Require a 1D iris cube with an unstructured mesh, "
                f"got a {cube.ndim}D cube instead."
            )
            raise ValueError(emsg)

        pdata = cls.from_mesh(cube.mesh, cidxs=cidxs)

        if location:
            if cube.location == "face":
                pdata.cell_data[cube.location] = nan_mask(cube.data)
            elif cube.location == "node":
                pdata.point_data[cube.location] = nan_mask(cube.data)
            else:
                emsg = f"Unstructured '{cube.location}' location data not supported."
                raise ValueError(emsg)

        return pdata

    @staticmethod
    def from_mesh(mesh: Mesh, cidxs: Optional[bool] = True) -> pv.PolyData:
        """
        TBD

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        face_node = mesh.face_node_connectivity
        indices = face_node.indices_by_src() - face_node.start_index
        coord_x, coord_y = mesh.node_coords

        # TODO: deal with masked coordinate points
        node_x = coord_x.points.data
        node_y = coord_y.points.data

        # TODO: ensure units are in degrees
        node_x = wrap(node_x)

        # TODO: support 2D planar projections

        # convert lat/lon to geocentric xyz
        vertices = to_xyz(node_x, node_y)

        # TODO: support non-quad mesh cells
        # create connectivity face serialization i.e., for each quad-mesh face
        # we have (4, N1, N2, N3, N4), where "4" is the number of connectivity
        # indices, followed by the four indices defining the face vertices.
        N_faces, N_nodes = indices.shape
        faces = np.hstack(
            [
                np.broadcast_to(np.array([N_nodes], dtype=np.int8), (N_faces, 1)),
                indices,
            ]
        )

        # create the mesh
        pdata = pv.PolyData(vertices, faces=faces, n_faces=N_faces)

        if cidxs:
            pdata.cell_data["cidxs"] = np.arange(pdata.n_cells, dtype=np.uint32)

        return pdata

    def __init__(
        self,
        data: Union[Cube, Mesh] = None,
        cidxs: Optional[bool] = True,
    ):
        """
        TBD

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if not isinstance(data, Cube) and not isinstance(data, Mesh):
            emsg = "Provide either an iris cube or an iris mesh."
            raise ValueError(emsg)

        if isinstance(data, Cube):
            pdata = self.from_cube(data, location=False, cidxs=cidxs)
        else:
            pdata = self.from_mesh(data, cidxs=cidxs)

        self._pdata = pdata
        self._cidxs = pdata.cell_data["cidxs"] if cidxs else None
        self._n_points = pdata.n_points
        self._n_cells = pdata.n_cells

    def __call__(self, data: Optional[Union[Cube, ArrayLike]] = None):
        """
        TBD

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if data is not None:
            if isinstance(data, Cube):
                data = data.data

            if data.ndim != 1:
                if data.size != self._n_cells or data.size != self._n_points:
                    emsg = (
                        f"Require a 1D array with either {self._n_points} (points) "
                        f"or {self._n_cells} (cells) values."
                    )
                    raise ValueError(emsg)
                data = np.ravel(data)

            data = nan_mask(data)

        pdata = pv.PolyData()
        pdata.copy_structure(self._pdata)

        if self._cidxs is not None:
            pdata.cell_data["cidxs"] = self._cidxs

        if data is not None:
            if data.size == self._n_cells:
                pdata.cell_data["face"] = data
            else:
                pdata.point_data["node"] = data

        return pdata
