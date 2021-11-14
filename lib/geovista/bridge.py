from typing import Optional, Tuple, Union

import numpy as np
from numpy.typing import ArrayLike
import pyvista as pv

from .common import nan_mask, to_xyz, wrap
from .log import get_logger

__all__ = ["Transform"]

# Configure the logger.
logger = get_logger(__name__)

# type aliases
Shape = Tuple[int]

#: Default array name for data on the mesh points/vertices/nodes.
DEFAULT_NAME_POINTS = "point_data"

#: Default array name for data on the mesh cells/faces.
DEFAULT_NAME_CELLS = "cell_data"

#: The field array name of a mesh containing point or cell data.
GV_DATA_NAME = "gvName"


class Transform:
    @staticmethod
    def _as_compatible_data(data: ArrayLike, n_points: int, n_cells: int) -> np.ndarray:
        """
        TBD

        Parameters
        ----------
        data : ArrayLike

        shape : tuple of int


        Returns
        -------
        ndarray


        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if data is not None:
            data = np.asanyarray(data)

            if data.size not in (n_points, n_cells):
                emsg = (
                    f"Require mesh data with either '{n_points:,d}' points or "
                    f"'{n_cells:,d}' cells, got '{data.size:,d}' values."
                )
                raise ValueError(emsg)

            data = nan_mask(np.ravel(data))

        return data

    @staticmethod
    def _as_contiguous_1d(
        lons: ArrayLike, lats: ArrayLike
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Verify and return a contiguous (N+1,) longitude and (M+1,) latitude
        bounds array, that will be then used afterwards to build a (M, N)
        contiguous quad-mesh consisting of M*N faces.

        Parameters
        ----------
        lons : ArrayLike
            A (N+1,) or (N, 2) longitude (degrees) array i.e., N faces in
            longitude.
        lats : ArrayLike
            A (M+1,) or (M, 2) latitude (degrees) array i.e., M faces in
            latitude.

        Returns
        -------
        tuple of ndarray
            The longitudes and latitudes as contiguous 1-D bounds arrays.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        lons = np.asanyarray(lons)
        lats = np.asanyarray(lats)

        if lons.ndim not in (1, 2) or (lons.ndim == 2 and lons.shape[1] != 2):
            emsg = (
                "Require a 1-D '(N+1,)' longitude array, or 2-D '(N, 2)' "
                f"longitude array, got {lons.ndim}-D '{lons.shape}'."
            )
            raise ValueError(emsg)

        if lats.ndim not in (1, 2) or (lats.ndim == 2 and lats.shape[1] != 2):
            emsg = (
                "Require a 1-D '(M+1,)' latitude array, or 2-D '(M, 2)' "
                f"latitude array, got {lats.ndim}-D '{lats.shape}'."
            )
            raise ValueError(emsg)

        if lons.ndim == 1 and lons.size < 2:
            emsg = (
                "Require a 1-D longitude array with minimal shape '(2,)' i.e, "
                "one face with two longitude bounds."
            )
            raise ValueError(emsg)

        if lats.ndim == 1 and lats.size < 2:
            emsg = (
                "Require a 1-D latitude array with minimal shape '(2,)' i.e., "
                "one face with two latitude bounds."
            )
            raise ValueError(emsg)

        def _contiguous(bnds: ArrayLike, kind: str) -> np.ndarray:
            left, right = bnds[:-1, 1], bnds[1:, 0]

            if not np.allclose(left, right):
                emsg = (
                    f"The {kind} bounds array, shape '{bnds.shape}', is not "
                    "contiguous."
                )
                raise ValueError(emsg)

            parts = ([bnds[0, 0]], left, [bnds[-1, -1]])

            return np.concatenate(parts)

        if lons.ndim == 2:
            lons = _contiguous(lons, "longitudes") if lons.size > 2 else lons[0]

        if lats.ndim == 2:
            lats = _contiguous(lats, "latitudes") if lats.size > 2 else lats[0]

        return lons, lats

    @staticmethod
    def _connectivity_M1N1(shape: Shape) -> np.ndarray:
        """
        TBD

        Parameters
        ----------
        shape : tuple of int


        Returns
        -------
        ndarray


        Notes
        -----
        ..versionadded:: 0.1.0

        """
        assert len(shape) == 2
        npts = np.product(shape)
        idxs = np.arange(npts).reshape(shape)
        faces_c1 = np.ravel(idxs[:-1, :-1]).reshape(-1, 1)
        faces_c2 = np.ravel(idxs[:-1, 1:]).reshape(-1, 1)
        faces_c3 = np.ravel(idxs[1:, 1:]).reshape(-1, 1)
        faces_c4 = np.ravel(idxs[1:, :-1]).reshape(-1, 1)
        faces = np.hstack([faces_c1, faces_c2, faces_c3, faces_c4])
        return faces

    @staticmethod
    def _connectivity_MN4(shape: Shape) -> np.ndarray:
        """
        TBD

        Parameters
        ----------
        shape : tuple of int
            ...

        Returns
        -------
        ndarray
            ...

        Notes
        -----
        ..versionadded:: 0.1.0

        """
        assert len(shape) == 2
        npts = np.product(shape) * 4
        idxs = np.arange(npts).reshape(-1, 4)
        return idxs

    @staticmethod
    def _verify_2d(lons: ArrayLike, lats: ArrayLike) -> None:
        """
        Verify the fitness of the provided longitudes and latitudes to create
        a (M, N) quad-mesh consisting of M*N faces.

        Parameters
        ----------
        lons : ArrayLike
            A (N+1, M+1) or (N, M, 4) longitude (degrees) array.
        lats : ArrayLike
            A (N+1, M+1) or (N, M, 4) latitude (degrees) array.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if lons.shape != lats.shape:
            emsg = (
                "Require longitudes and latitudes with the same shape, got "
                f"'{lons.shape}' and '{lats.shape}' respectively."
            )
            raise ValueError(emsg)

        if lons.ndim not in (2, 3) or (lons.ndim == 3 and lons.shape[2] != 4):
            emsg = (
                "Require a 2-D '(M+1, N+1)' longitude array, or 3-D "
                f"'(M, N, 4)' longitude array, got {lons.ndim}-D "
                f"'{lons.shape}'."
            )
            raise ValueError(emsg)

        if lons.ndim == 2 and (lons.shape[0] < 2 or lons.shape[1] < 2):
            emsg = (
                "Require a quad-mesh to have at least one face with four "
                "points/vertices i.e., minimal shape '(2, 2)', got "
                f"longitudes/latitudes with shape '{lons.shape}'."
            )
            raise ValueError(emsg)

    @staticmethod
    def _verify_connectivity(connectivity: Shape) -> None:
        """
        Ensure that the connectivity shape tuple is 2-D and minimal.

        Parameters
        ----------
        connectivity : Shape
            The 2-D shape of the connectivity, which must be at least (1, 3)
            for the minimal mesh consisting of one triangular face.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if len(connectivity) != 2:
            emsg = (
                "Require a 2-D '(M, N)' connectivity array, defining the "
                "N indices for each of the M faces of the mesh, got "
                f"{len(connectivity)}-D '{connectivity}' array."
            )
            raise ValueError(emsg)

        if connectivity[1] < 3:
            emsg = (
                "Require a connectivity array defining at least 3 vertices "
                "(triangles) per mesh face i.e., minimal shape '(M, 3)', got "
                f"connectivity with shape '{connectivity}'."
            )
            raise ValueError(emsg)

    @staticmethod
    def _verify_unstructured(lons: ArrayLike, lats: ArrayLike) -> None:
        """
        TBD

        Parameters
        ----------
        lons : ArrayLike

        lats : ArrayLike


        Notes
        -----
        ..versionadded:: 0.1.0

        """
        if lons.shape != lats.shape:
            emsg = (
                "Require longitudes and latitudes with the same shape, got "
                f"'{lons.shape}' and '{lats.shape}' respectively."
            )
            raise ValueError(emsg)

        if lons.ndim != 1:
            emsg = f"Require a 1-D longitude and latitude array, got {lons.ndim}-D."
            raise ValueError(emsg)

        if lons.size < 3:
            emsg = (
                "Require a mesh to have at least one face with three "
                "points/vertices i.e., minimal shape '(3,)', got "
                f"longitudes/latitudes with shape '{lons.shape}'."
            )
            raise ValueError(emsg)

    @classmethod
    def from_1d(
        cls,
        lons: ArrayLike,
        lats: ArrayLike,
        data: Optional[ArrayLike] = None,
        name: Optional[str] = None,
        clean: Optional[bool] = False,
    ) -> pv.PolyData:
        """
        Build a quad-faced mesh from contiguous 1-D longitudes and latitudes.

        This allows the construction of a uniform or rectilinear quad-faced
        (M, N) mesh grid, where the mesh is M latitude faces by N longitude
        faces, resulting in a mesh consisting of M*N faces.

        Parameters
        ----------
        lons : ArrayLike
            A 1-D array of longitudes (degrees) defining the contiguous
            face longitude boundaries of the mesh. Creating a mesh with N
            faces in the longitude requires a (N+1,) array. Alternatively, a
            (N, 2) contiguous bounds array may be provided. Note that,
            longitudes will be automatically wrapped to the closed interval
            [-180, 180].
        lats : ArrayLike
            A 1-D array of latitudes (degrees) in the closed interval [-90, 90],
            defining the contiguous face latitude boundaries of the mesh.
            Creating a mesh with M faces in the latitude requires a (M+1,)
            array. Alternatively, a (M, 2) contiguous bounds array may be
            provided.
        data : ArrayLike, optional
            Data to be optionally attached to the mesh. The data must match
            either the shape of the fully formed mesh points (M, N), or the
            number of mesh faces, M*N.
        name : str, optional
            The name of the optional data array to be attached to the mesh. If
            ``data`` is provided but with no ``name``, defaults to either
            :data:`DEFAULT_NAME_POINTS` or :data:`DEFAULT_NAME_CELLS`.
        clean : bool, default=False
            Specify whether to merge duplicate points, remove unused points,
            and/or remove degenerate cells in the resultant mesh.

        Returns
        -------
        PolyData
            The contiguous quad-faced mesh.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        lons, lats = cls._as_contiguous_1d(lons, lats)
        mlons, mlats = np.meshgrid(lons, lats, indexing="xy")

        return Transform.from_2d(mlons, mlats, data=data, name=name, clean=clean)

    @classmethod
    def from_2d(
        cls,
        lons: ArrayLike,
        lats: ArrayLike,
        data: Optional[ArrayLike] = None,
        name: Optional[str] = None,
        clean: Optional[bool] = False,
    ) -> pv.PolyData:
        """
        Build a quad-faced mesh from 2-D longitudes and latitudes.

        This allows the construction of a uniform, rectilinear or curvilinear
        quad-faced (M, N) mesh grid, where the mesh is M latitude faces by N
        longitude faces, resulting in a mesh consisting of M*N faces.

        The provided longitudes and latitudes define the four geospatial
        vertices of each mesh quad-face.

        Parameters
        ----------
        lons : ArrayLike
            A 2-D array of longitudes (degrees) defining the face longitude
            boundaries of the mesh. Creating a (M, N) mesh requires a
            (M+1, N+1) longitude array. Alternatively, a (M, N, 4) array
            may be provided. Note that, longitudes will be automatically
            wrapped to the closed interval [-180, 180].
        lats : ArrayLike
            A 2-D array of latitudes (degrees) in the closed interval [-90, 90],
            defining the face latitude boundaries of the mesh. Creating a
            (M, N) mesh requires a (M+1, N+1) latitude array. Alternatively,
            a (M, N, 4) array may be provided.
        data : ArrayLike, optional
            Data to be optionally attached to the mesh. The data must match
            either the shape of the fully formed mesh points (M, N), or the
            number of mesh faces, M*N.
        name : str, optional
            The name of the optional data array to be attached to the mesh. If
            ``data`` is provided but with no ``name``, defaults to either
            :data:`DEFAULT_NAME_POINTS` or :data:`DEFAULT_NAME_CELLS`.
        clean : bool, default=False
            Specify whether to merge duplicate points, remove unused points,
            and/or remove degenerate cells in the resultant mesh.

        Returns
        -------
        PolyData
            The quad-faced mesh.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        lons = np.asanyarray(lons)
        lats = np.asanyarray(lats)
        cls._verify_2d(lons, lats)
        shape = lons.shape

        if len(shape) == 2:
            # we have shape (M+1, N+1)
            r, c = points_shape = shape
            cells_shape = (r - 1, c - 1)
        else:
            # we have shape (M, N, 4)
            r, c = cells_shape = shape[:-1]
            points_shape = (r + 1, c + 1)

        # generate connectivity (topology) map of indices into the geometry
        connectivity = (
            cls._connectivity_M1N1(points_shape)
            if lons.ndim == 2
            else cls._connectivity_MN4(cells_shape)
        )

        return Transform.from_unstructured(
            lons, lats, connectivity, data=data, name=name, clean=clean
        )

    @classmethod
    def from_unstructured(
        cls,
        lons: ArrayLike,
        lats: ArrayLike,
        connectivity: Union[ArrayLike, Shape],
        data: Optional[ArrayLike] = None,
        start_index: Optional[int] = 0,
        name: Optional[ArrayLike] = None,
        clean: Optional[bool] = False,
    ) -> pv.PolyData:
        """
        Build a mesh from unstructured 1-D longitudes and latitudes.

        The connectivity of the unstructured mesh is required in order to
        explicitly define the face topology relationship, which is defined in
        terms of indices into the provided mesh geometry.

        Note that, the connectivity must define a mesh comprised of faces based
        on the same primitive shape e.g., a mesh of triangles, or a mesh of
        quads etc. Support is not provided for mixed face meshes. Also, any
        optional mesh data must be provided in the same order as the mesh face
        connectivity.

        Parameters
        ----------
        lons : ArrayLike
            A 1-D array of longitudes (degrees) defining the longitudes of all
            face vertices in the mesh. Note that, longitudes will be
            automatically wrapped to the closed interval [-180, 180].
        lats : ArrayLike
            A 1-D array of latitudes (degrees) in the closed interval [-90, 90],
            defining the latitudes of all face vertices in the mesh.
        connectivity : ArrayLike or Shape
            Defines the topology of each face in the unstructured mesh in terms
            of indices into the provided ``lons`` and ``lats`` mesh geometry
            arrays. The ``connectivity`` is a 2-D `(M, N)` array, where `M` is
            the number of mesh faces, and `N` is the number of
            points/vertices/nodes per face. Alternatively, an `(M, N)` tuple
            of the connectivity shape may be provided instead, given that the
            ``lons`` and ``lats`` define M*N points in the mesh geometry.
        data : ArrayLike, optional
            Data to be optionally attached to the mesh.
        start_index : int, default=0
            Specify the base index of the provided ``connectivity`` in the
            closed interval [0, 1]. For example, if ``start_index=1``, then
            the ``start_index`` will be subtracted from the ``connectivity``
            to result in 0-based indices into the provided mesh geometry.
        name : str, optional
            The name of the optional data array to be attached to the mesh. If
            ``data`` is provided but with no ``name``, defaults to either
            :data:`DEFAULT_NAME_POINTS` or :data:`DEFAULT_NAME_CELLS`.
        clean : bool, default=False
            Specify whether to merge duplicate points, remove unused points,
            and/or remove degenerate cells in the resultant mesh.

        Returns
        -------
        PolyData
            The N-faced mesh.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        lons = np.asanyarray(lons).ravel()
        lats = np.asanyarray(lats).ravel()
        cls._verify_unstructured(lons, lats)

        # ensure longitudes (degrees) are in closed interval [-180, 180]
        lons = wrap(lons)

        if isinstance(connectivity, tuple):
            cls._verify_connectivity(connectivity)
            n_points = np.product(connectivity)

            if n_points != lons.size:
                emsg = (
                    f"Connectivity shape '{connectivity}' requires "
                    f"'{n_points:,d}' longitude/latitude points, only "
                    f"'{lons.size:,d}' available."
                )
                raise ValueError(emsg)

            logger.debug(
                f"connectivity shape {connectivity} generating {n_points:,d} indicies"
            )
            connectivity = np.arange(n_points).reshape(connectivity)
            ignore_start_index = True
            logger.debug("ignoring start_index")
        else:
            connectivity = np.asanyarray(connectivity)
            cls._verify_connectivity(connectivity.shape)
            ignore_start_index = False

        # reduce any singularities at the poles to a singleton point
        poles = np.abs(lats) == 90
        if np.any(poles):
            lons[poles] = 0

        if start_index not in [0, 1]:
            emsg = (
                "Require a 'start_index` in the closed interval [0, 1], got "
                f"'{start_index}'."
            )
            raise ValueError(emsg)

        if start_index and not ignore_start_index:
            connectivity -= start_index

        # convert lat/lon to geocentric xyz
        geometry = to_xyz(lons, lats)

        # create face connectivity serialization e.g., for a quad-mesh, for
        # each face we have (4, V1, V2, V3, V4), where "4" is the number of
        # vertices defining the face, followed by the four indices specifying
        # each of the face vertices into the mesh geometry.
        n_faces, n_vertices = connectivity.shape
        faces = np.hstack(
            [
                np.broadcast_to(np.array([n_vertices], dtype=np.int8), (n_faces, 1)),
                connectivity,
            ]
        )

        # create the mesh
        mesh = pv.PolyData(geometry, faces=faces, n_faces=n_faces)

        # attach any optional data to the mesh
        if data is not None:
            data = cls._as_compatible_data(data, mesh.n_points, mesh.n_cells)

            if not name:
                name = (
                    DEFAULT_NAME_POINTS
                    if data.size == mesh.n_points
                    else DEFAULT_NAME_CELLS
                )
            if not isinstance(name, str):
                name = str(name)

            mesh.field_data[GV_DATA_NAME] = np.array([name])
            mesh[name] = data

        # clean the mesh
        if clean:
            mesh.clean(inplace=True)

        return mesh

    def __init__(
        self,
        lons: ArrayLike,
        lats: ArrayLike,
        connectivity: Optional[Union[ArrayLike, Shape]] = None,
        start_index: Optional[int] = 0,
        clean: Optional[bool] = False,
    ):
        lons = np.asanyarray(lons)
        lats = np.asanyarray(lats)

        if connectivity is None:
            if lons.ndim <= 1 or lats.ndim <= 1:
                mesh = self.from_1d(lons, lats, clean=clean)
            else:
                mesh = self.from_2d(lons, lats, clean=clean)
        else:
            mesh = self.from_unstructured(
                lons,
                lats,
                connectivity,
                start_index=start_index,
                clean=clean,
            )

        self._mesh = mesh
        self._n_points = mesh.n_points
        self._n_cells = mesh.n_cells

    def __call__(
        self, data: Optional[ArrayLike] = None, name: Optional[str] = None
    ) -> pv.PolyData:
        """
        TBD

        Parameters
        ----------
        data : ArrayLike, optional


        Returns
        -------
        PolyData


        Notes
        _____
        ..versionadded:: 0.1.0

        """
        if data is not None:
            data = self._as_compatible_data(data, self._n_points, self._n_cells)

        mesh = pv.PolyData()
        mesh.copy_structure(self._mesh)

        if data is not None:
            if not name:
                name = (
                    DEFAULT_NAME_POINTS
                    if data.size == self._n_points
                    else DEFAULT_NAME_CELLS
                )

            mesh.field_data[GV_DATA_NAME] = np.array([name])
            mesh[name] = data

        return mesh
