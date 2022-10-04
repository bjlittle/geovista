from typing import Optional, Tuple, Union

import numpy as np
from numpy.typing import ArrayLike
from pyproj import CRS, Transformer
import pyvista as pv

from .common import GV_FIELD_CRS, GV_FIELD_NAME, ZLEVEL_FACTOR, nan_mask, to_xyz, wrap
from .crs import WGS84
from .log import get_logger

__all__ = ["Transform", "logger"]

# configure the logger
logger = get_logger(__name__)

# type aliases
Shape = Tuple[int]
CRSLike = Union[int, str, dict, CRS]

#: Default array name for data on the mesh points/vertices/nodes.
DEFAULT_NAME_POINTS = "point_data"

#: Default array name for data on the mesh cells/faces.
DEFAULT_NAME_CELLS = "cell_data"


class Transform:
    @staticmethod
    def _as_compatible_data(data: ArrayLike, n_points: int, n_cells: int) -> np.ndarray:
        """
        TODO

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
        xs: ArrayLike, ys: ArrayLike
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Verify and return a contiguous (N+1,) x-axis and (M+1,) y-axis
        bounds array, that will be then used afterwards to build a (M, N)
        contiguous quad-mesh consisting of M*N faces.

        Parameters
        ----------
        xs : ArrayLike
            A (N+1,) or (N, 2) x-axis array i.e., N-faces in the x-axis.
        ys : ArrayLike
            A (M+1,) or (M, 2) y-axis array i.e., M-faces in the y-axis.

        Returns
        -------
        tuple of ndarray
            The x-values and y-values as contiguous 1-D bounds arrays.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        xs = np.asanyarray(xs)
        ys = np.asanyarray(ys)

        if xs.ndim not in (1, 2) or (xs.ndim == 2 and xs.shape[1] != 2):
            emsg = (
                "Require a 1-D '(N+1,)' x-axis array, or 2-D '(N, 2)' "
                f"x-axis array, got {xs.ndim}-D '{xs.shape}'."
            )
            raise ValueError(emsg)

        if ys.ndim not in (1, 2) or (ys.ndim == 2 and ys.shape[1] != 2):
            emsg = (
                "Require a 1-D '(M+1,)' y-axis array, or 2-D '(M, 2)' "
                f"y-axis array, got {ys.ndim}-D '{ys.shape}'."
            )
            raise ValueError(emsg)

        if xs.ndim == 1 and xs.size < 2:
            emsg = (
                "Require a 1-D x-axis array with minimal shape '(2,)' i.e., "
                "one face with two x-value bounds."
            )
            raise ValueError(emsg)

        if ys.ndim == 1 and ys.size < 2:
            emsg = (
                "Require a 1-D y-axis array with minimal shape '(2,)' i.e., "
                "one face with two y-value bounds."
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

        if xs.ndim == 2:
            xs = _contiguous(xs, "x-axis") if xs.size > 2 else xs[0]

        if ys.ndim == 2:
            ys = _contiguous(ys, "y-axis") if ys.size > 2 else ys[0]

        return xs, ys

    @staticmethod
    def _connectivity_M1N1(shape: Shape) -> np.ndarray:
        """
        TODO

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
        TODO

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
        npts = np.product(shape) * 4
        idxs = np.arange(npts).reshape(-1, 4)
        return idxs

    @staticmethod
    def _verify_2d(xs: ArrayLike, ys: ArrayLike) -> None:
        """
        Verify the fitness of the provided x-values and y-values to create
        a (M, N) quad-mesh consisting of M*N faces.

        Parameters
        ----------
        xs : ArrayLike
            A (N+1, M+1) or (N, M, 4) x-axis array.
        ys : ArrayLike
            A (N+1, M+1) or (N, M, 4) y-axis array.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if xs.shape != ys.shape:
            emsg = (
                "Require x-values and y-values with the same shape, got "
                f"'{xs.shape}' and '{ys.shape}' respectively."
            )
            raise ValueError(emsg)

        if xs.ndim not in (2, 3) or (xs.ndim == 3 and xs.shape[2] != 4):
            emsg = (
                "Require a 2-D '(M+1, N+1)' x-axis array, or 3-D "
                f"'(M, N, 4)' x-axis array, got {xs.ndim}-D "
                f"'{xs.shape}'."
            )
            raise ValueError(emsg)

        if xs.ndim == 2 and (xs.shape[0] < 2 or xs.shape[1] < 2):
            emsg = (
                "Require a quad-mesh to have at least one face with four "
                "points/vertices i.e., minimal shape '(2, 2)', got "
                f"x-values/y-values with shape '{xs.shape}'."
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
                "N indices for each of the M-faces of the mesh, got "
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
    def _verify_unstructured(xs: ArrayLike, ys: ArrayLike) -> None:
        """
        TODO

        Parameters
        ----------
        xs : ArrayLike
        ys : ArrayLike

        Notes
        -----
        ..versionadded:: 0.1.0

        """
        if xs.shape != ys.shape:
            emsg = (
                "Require x-values and y-values with the same shape, got "
                f"'{xs.shape}' and '{ys.shape}' respectively."
            )
            raise ValueError(emsg)

        if xs.ndim != 1:
            emsg = f"Require a 1-D x-values and y-values array, got {xs.ndim}-D."
            raise ValueError(emsg)

        if xs.size < 3:
            emsg = (
                "Require a mesh to have at least one face with three "
                "points/vertices i.e., minimal shape '(3,)', got "
                f"x-values/y-values with shape '{xs.shape}'."
            )
            raise ValueError(emsg)

    @classmethod
    def from_1d(
        cls,
        xs: ArrayLike,
        ys: ArrayLike,
        data: Optional[ArrayLike] = None,
        name: Optional[str] = None,
        crs: Optional[CRSLike] = None,
        radius: Optional[float] = None,
        clean: Optional[bool] = False,
        zfactor: Optional[float] = None,
        zlevel: Optional[int] = None,
    ) -> pv.PolyData:
        """
        Build a quad-faced mesh from contiguous 1-D x-values and y-values.

        This allows the construction of a uniform or rectilinear quad-faced
        (M, N) mesh grid, where the mesh has M-faces in the y-axis, and
        N-faces in the x-axis, resulting in a mesh consisting of M*N faces.

        The provided `xs` and `ys` will be projected from their `crs` to
        geographic longitude and latitude values.

        Parameters
        ----------
        xs : ArrayLike
            A 1-D array of x-values, in canonical `crs` units, defining the
            contiguous face x-value boundaries of the mesh. Creating a mesh
            with N-faces in the `crs` x-axis requires a (N+1,) array.
            Alternatively, a (N, 2) contiguous bounds array may be provided.
        ys : ArrayLike
            A 1-D array of y-values, in canonical `crs` units, defining the
            contiguous face y-value boundaries of the mesh. Creating a mesh
            with M-faces in the `crs` y-axis requires a (M+1,) array.
            Alternatively, a (M, 2) contiguous bounds array may be provided.
        data : ArrayLike, optional
            Data to be optionally attached to the mesh. The data must match
            either the shape of the fully formed mesh points (M, N), or the
            number of mesh faces, M*N.
        name : str, optional
            The name of the optional data array to be attached to the mesh. If
            `data` is provided but with no `name`, defaults to either
            :data:`DEFAULT_NAME_POINTS` or :data:`DEFAULT_NAME_CELLS`.
        crs : CRSLike, optional
            The Coordinate Reference System of the provided `xs` and `ys`. May
            be anything accepted by :meth:`pyproj.CRS.from_user_input`. Defaults
            to ``EPSG:4326`` i.e., ``WGS 84``.
        radius : float, default=1.0
            The radius of the sphere. Defaults to an S2 unit sphere.
        clean : bool, default=False
            Specify whether to merge duplicate points, remove unused points,
            and/or remove degenerate cells in the resultant mesh.
        zfactor : float, optional
            The roportional multiplier for z-axis levels/offsets. Defaults
            to :data:`ZLEVEL_FACTOR`.
        zlevel : int, default=0
            The z-axis level/offset of the mesh, giving a computed ``radius``
            of ``radius + zlevel * zfactor``.

        Returns
        -------
        PolyData
            The contiguous quad-faced spherical mesh.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        xs, ys = cls._as_contiguous_1d(xs, ys)
        mxs, mys = np.meshgrid(xs, ys, indexing="xy")
        return Transform.from_2d(
            mxs,
            mys,
            data=data,
            name=name,
            crs=crs,
            radius=radius,
            clean=clean,
            zfactor=zfactor,
            zlevel=zlevel,
        )

    @classmethod
    def from_2d(
        cls,
        xs: ArrayLike,
        ys: ArrayLike,
        data: Optional[ArrayLike] = None,
        name: Optional[str] = None,
        crs: Optional[CRSLike] = None,
        radius: Optional[float] = None,
        clean: Optional[bool] = False,
        zfactor: Optional[float] = None,
        zlevel: Optional[int] = None,
    ) -> pv.PolyData:
        """
        Build a quad-faced mesh from 2-D x-values and y-values.

        This allows the construction of a uniform, rectilinear or curvilinear
        quad-faced (M, N) mesh grid, where the mesh has M-faces in the y-axis,
        and N-faces in the x-axis, resulting in a mesh consisting of M*N faces.

        The provided `xs` and `ys` define the four vertices of each quad-face
        in the mesh for the native `crs`, which will then be projected to
        geographic longitude and latitude values.

        Parameters
        ----------
        xs : ArrayLike
            A 2-D array of x-values, in canonical `crs` units, defining the
            face x-value boundaries of the mesh. Creating a (M, N) mesh
            requires a (M+1, N+1) x-axis array. Alternatively, a (M, N, 4)
            array may be provided.
        ys : ArrayLike
            A 2-D array of y-values, in canonical `crs` units, defining the
            face y-value boundaries of the mesh. Creating a (M, N) mesh
            requires a (M+1, N+1) y-axis array. Alternatively, a (M, N, 4)
            array may be provided.
        data : ArrayLike, optional
            Data to be optionally attached to the mesh. The data must match
            either the shape of the fully formed mesh points (M, N), or the
            number of mesh faces, M*N.
        name : str, optional
            The name of the optional data array to be attached to the mesh. If
            `data` is provided but with no `name`, defaults to either
            :data:`DEFAULT_NAME_POINTS` or :data:`DEFAULT_NAME_CELLS`.
        crs : CRSLike, optional
            The Coordinate Reference System of the provided `xs` and `ys`. May
            be anything accepted by :meth:`pyproj.CRS.from_user_input`. Defaults
            to ``EPSG:4326`` i.e., ``WGS 84``.
        radius : float, default=1.0
            The radius of the sphere. Defaults to an S2 unit sphere.
        clean : bool, default=False
            Specify whether to merge duplicate points, remove unused points,
            and/or remove degenerate cells in the resultant mesh.
        zfactor : float, optional
            The roportional multiplier for z-axis levels/offsets. Defaults
            to :data:`ZLEVEL_FACTOR`.
        zlevel : int, default=0
            The z-axis level/offset of the mesh, giving a computed ``radius``
            of ``radius + zlevel * zfactor``.

        Returns
        -------
        PolyData
            The quad-faced spherical mesh.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        xs = np.asanyarray(xs)
        ys = np.asanyarray(ys)
        cls._verify_2d(xs, ys)
        shape = xs.shape

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
            if xs.ndim == 2
            else cls._connectivity_MN4(cells_shape)
        )

        return Transform.from_unstructured(
            xs,
            ys,
            connectivity,
            data=data,
            name=name,
            crs=crs,
            radius=radius,
            clean=clean,
            zfactor=zfactor,
            zlevel=zlevel,
        )

    @classmethod
    def from_unstructured(
        cls,
        xs: ArrayLike,
        ys: ArrayLike,
        connectivity: Union[ArrayLike, Shape],
        data: Optional[ArrayLike] = None,
        start_index: Optional[int] = 0,
        name: Optional[ArrayLike] = None,
        crs: Optional[CRSLike] = None,
        radius: Optional[float] = None,
        clean: Optional[bool] = False,
        zfactor: Optional[float] = None,
        zlevel: Optional[int] = None,
    ) -> pv.PolyData:
        """
        Build a mesh from unstructured 1-D x-values and y-values.

        The `connectivity` of the unstructured mesh is required in order to
        explicitly define the face topology relationship, which is defined in
        terms of indices into the provided `xs` and `ys` mesh geometry.

        Note that, the `connectivity` must define a mesh comprised of faces based
        on the same primitive shape e.g., a mesh of triangles, or a mesh of
        quads etc. Support is not provided for mixed face meshes. Also, any
        optional mesh `data` provided must be in the same order as the mesh face
        `connectivity`.

        Parameters
        ----------
        xs : ArrayLike
            A 1-D array of x-values, in canonical `crs` units, defining the
            vertices of each face in the mesh.
        ys : ArrayLike
            A 1-D array of y-values, in canonical `crs` units, defining the
            vertices of each face in the mesh.
        connectivity : ArrayLike or Shape
            Defines the topology of each face in the unstructured mesh in terms
            of indices into the provided `xs` and `ys` mesh geometry
            arrays. The `connectivity` is a 2-D (M, N) array, where ``M`` is
            the number of mesh faces, and ``N`` is the number of
            points/vertices/nodes per face. Alternatively, an (M, N) tuple
            defining the connectivity shape may be provided instead, given that the
            `xs` and `ys` define M*N points in the mesh geometry.
        data : ArrayLike, optional
            Data to be optionally attached to the mesh.
        start_index : int, default=0
            Specify the base index of the provided `connectivity` in the
            closed interval [0, 1]. For example, if ``start_index=1``, then
            the `start_index` will be subtracted from the `connectivity`
            to result in 0-based indices into the provided mesh geometry.
        name : str, optional
            The name of the optional data array to be attached to the mesh. If
            `data` is provided but with no `name`, defaults to either
            :data:`DEFAULT_NAME_POINTS` or :data:`DEFAULT_NAME_CELLS`.
        crs : CRSLike, optional
            The Coordinate Reference System of the provided `xs` and `ys`. May
            be anything accepted by :meth:`pyproj.CRS.from_user_input`. Defaults
            to ``EPSG:4326`` i.e., ``WGS 84``.
        radius : float, default=1.0
            The radius of the mesh sphere. Defaults to an S2 unit sphere.
        clean : bool, default=False
            Specify whether to merge duplicate points, remove unused points,
            and/or remove degenerate cells in the resultant mesh.
        zfactor : float, optional
            The roportional multiplier for z-axis levels/offsets. Defaults
            to :data:`ZLEVEL_FACTOR`.
        zlevel : int, default=0
            The z-axis level/offset of the mesh, giving a computed ``radius``
            of ``radius + zlevel * zfactor``.

        Returns
        -------
        PolyData
            The N-faced spherical mesh.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        xs = np.asanyarray(xs).ravel()
        ys = np.asanyarray(ys).ravel()
        cls._verify_unstructured(xs, ys)

        if crs is not None:
            crs = CRS.from_user_input(crs)

            if crs != WGS84:
                transformer = Transformer.from_crs(crs, WGS84, always_xy=True)
                xs, ys = transformer.transform(xs, ys, errcheck=True)

        # ensure longitudes (degrees) are in closed interval [-180, 180)
        xs = wrap(xs)

        if isinstance(connectivity, tuple):
            cls._verify_connectivity(connectivity)
            n_points = np.product(connectivity)

            if n_points != xs.size:
                emsg = (
                    f"Connectivity shape '{connectivity}' requires "
                    f"'{n_points:,d}' x-values/y-values, only "
                    f"'{xs.size:,d}' available."
                )
                raise ValueError(emsg)

            logger.debug(
                "connectivity shape %s generating %d indices", connectivity, n_points
            )
            connectivity = np.arange(n_points).reshape(connectivity)
            ignore_start_index = True
            logger.debug("ignoring start_index")
        else:
            # require to copy connectivity, otherwise reqults in a memory
            # corruption within vtk
            connectivity = np.asanyarray(connectivity).copy()
            cls._verify_connectivity(connectivity.shape)
            ignore_start_index = False

        # reduce any singularities at the poles to a singleton point
        poles = np.isclose(np.abs(ys), 90)
        if np.any(poles):
            xs[poles] = 0

        if start_index not in [0, 1]:
            emsg = (
                "Require a 'start_index` in the closed interval [0, 1], got "
                f"'{start_index}'."
            )
            raise ValueError(emsg)

        if start_index and not ignore_start_index:
            connectivity -= start_index

        radius = 1.0 if radius is None else abs(radius)

        if zfactor is None:
            zfactor = ZLEVEL_FACTOR

        if zlevel is None:
            zlevel = 0

        radius += radius * zlevel * zfactor

        # convert lat/lon to cartesian xyz
        geometry = to_xyz(xs, ys, radius=radius)

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

        # attach the pyproj crs serialized as ogc wkt
        wkt = np.array([WGS84.to_wkt()])
        mesh.field_data[GV_FIELD_CRS] = wkt

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

            mesh.field_data[GV_FIELD_NAME] = np.array([name])
            mesh[name] = data

        # clean the mesh
        if clean:
            mesh.clean(inplace=True)

        return mesh

    def __init__(
        self,
        xs: ArrayLike,
        ys: ArrayLike,
        connectivity: Optional[Union[ArrayLike, Shape]] = None,
        start_index: Optional[int] = 0,
        crs: Optional[ArrayLike] = None,
        clean: Optional[bool] = False,
        zfactor: Optional[float] = None,
        zlevel: Optional[int] = None,
    ):
        xs = np.asanyarray(xs)
        ys = np.asanyarray(ys)

        if connectivity is None:
            if xs.ndim <= 1 or ys.ndim <= 1:
                mesh = self.from_1d(
                    xs, ys, crs=crs, clean=clean, zfactor=zfactor, zlevel=zlevel
                )
            else:
                mesh = self.from_2d(
                    xs, ys, crs=crs, clean=clean, zfactor=zfactor, zlevel=zlevel
                )
        else:
            mesh = self.from_unstructured(
                xs,
                ys,
                connectivity,
                start_index=start_index,
                crs=crs,
                clean=clean,
                zfactor=zfactor,
                zlevel=zlevel,
            )

        self._mesh = mesh
        self._n_points = mesh.n_points
        self._n_cells = mesh.n_cells

    def __call__(
        self, data: Optional[ArrayLike] = None, name: Optional[str] = None
    ) -> pv.PolyData:
        """
        TODO

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

            mesh.field_data[GV_FIELD_NAME] = np.array([name])
            mesh[name] = data

        return mesh
