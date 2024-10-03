# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Transform structured grids and unstructured meshes to PyVista format.

This module provides the :class:`~geovista.bridge.Transform` factory class for
transforming rectilinear, curvilinear, and unstructured geospatial data
into geolocated :doc:`PyVista <pyvista:index>` mesh instances.

Notes
-----
.. versionadded:: 0.1.0

- :doc:`pyvista:user-guide/what-is-a-mesh`

"""

from __future__ import annotations

from pathlib import Path, PurePath
from typing import TYPE_CHECKING, TypeAlias
import warnings

import lazy_loader as lazy

from .common import (
    GV_FIELD_NAME,
    GV_FIELD_RADIUS,
    GV_FIELD_ZSCALE,
    RADIUS,
    ZLEVEL_SCALE,
    cast_UnstructuredGrid_to_PolyData,
    nan_mask,
    to_cartesian,
    wrap,
)
from .crs import WGS84, CRSLike, to_wkt
from .transform import transform_points

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import ArrayLike
    import pyvista as pv

# lazy import third-party dependencies
np = lazy.load("numpy")
pv = lazy.load("pyvista")
pyproj = lazy.load("pyproj")
rio = lazy.load("rasterio")

__all__ = [
    "BRIDGE_CLEAN",
    "NAME_CELLS",
    "NAME_POINTS",
    "PathLike",
    "RIO_SIEVE_SIZE",
    "Shape",
    "Transform",
]

# type aliases
PathLike: TypeAlias = str | PurePath
"""Type alias for an asset file path."""

Shape: TypeAlias = tuple[int]
"""Type alias for a tuple of integers."""

# constants
BRIDGE_CLEAN: bool = False
"""Whether mesh cleaning performed by the bridge."""

NAME_CELLS: str = "cell_data"
"""Default array name for data on the mesh cells."""

NAME_POINTS: str = "point_data"
"""Default array name for data on the mesh points."""

RIO_SIEVE_SIZE: int = 800
"""The default size of the :func:`rasterio.features.sieve` filter."""


class Transform:  # numpydoc ignore=PR01
    """Build a mesh from spatial points, connectivity, data and CRS metadata.

    Notes
    -----
    .. versionadded:: 0.1.0

    """

    @staticmethod
    def _as_compatible_data(
        data: ArrayLike, n_points: int, n_cells: int, rgb: bool = False
    ) -> np.ndarray:
        """Ensure data is compatible with the number of mesh points or cells.

        Note that, masked values will be filled with NaNs.

        Parameters
        ----------
        data : ArrayLike
            The intended data payload of the mesh.
        n_points : int
            The number of nodes in the mesh.
        n_cells : int
            The number of cells in the mesh.
        rgb : bool, default=False
            Whether the data is an ``RGB`` or ``RGBA`` image.

        Returns
        -------
        ndarray
            The verified data.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if data is not None:
            data = np.asanyarray(data)

            if rgb and data.ndim < 2:
                emsg = f"RGB/RGBA image data must be at least 2-D, got {data.ndim}-D."
                raise ValueError(emsg)

            size = data.size // data.shape[-1] if rgb else data.size

            if size not in (n_points, n_cells):
                emsg = (
                    f"Require mesh data with either '{n_points:,d}' points or "
                    f"'{n_cells:,d}' cells, got '{data.size:,d}' values."
                )
                raise ValueError(emsg)

            data = nan_mask(np.ravel(data))

            if rgb:
                # reshape to be (N, 3) or (N, 4) for RGB or RGBA image data
                data = data.reshape(size, -1)

        return data

    @staticmethod
    def _as_contiguous_1d(
        xs: ArrayLike, ys: ArrayLike
    ) -> tuple[np.ndarray, np.ndarray]:
        """Construct contiguous 1-D x-axis and y-axis bounds arrays.

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
        xs, ys = np.asanyarray(xs), np.asanyarray(ys)

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
            """Verify and construct a contiguous bounds array.

            Parameters
            ----------
            bnds : ArrayLike
                The bounds array.
            kind : str
                The kind of bounds array e.g., 'x-axis' or 'y-axis'.

            Returns
            -------
            ndarray
                The contiguous bounds array.

            """
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
    def _create_connectivity_m1n1(shape: Shape) -> np.ndarray:
        """Create 2-D quad-mesh connectivity from node `shape`.

        The connectivity ordering of the quad-mesh face nodes (points) is
        anti-clockwise, as follows:

            3---2
            |   |
            0---1

        Assumes that the associated face node spatial coordinates are
        appropriately ordered.

        Parameters
        ----------
        shape : Shape
            The shape of the 2-D mesh nodes.

        Returns
        -------
        ndarray
            The connectivity array of the face-to-node offsets (zero based).

        Notes
        -----
        ..versionadded:: 0.1.0

        For VTK Quadrilateral cell type node ordering see
        https://kitware.github.io/vtk-examples/site/VTKBook/05Chapter5/#54-cell-types

        """
        # sanity check - internally this should always be the case
        assert len(shape) == 2

        npts = np.prod(shape)
        idxs = np.arange(npts, dtype=np.uint32).reshape(shape)

        nodes_c0 = np.ravel(idxs[1:, :-1]).reshape(-1, 1)
        nodes_c1 = np.ravel(idxs[1:, 1:]).reshape(-1, 1)
        nodes_c2 = np.ravel(idxs[:-1, 1:]).reshape(-1, 1)
        nodes_c3 = np.ravel(idxs[:-1, :-1]).reshape(-1, 1)

        return np.hstack([nodes_c0, nodes_c1, nodes_c2, nodes_c3])

    @staticmethod
    def _create_connectivity_mn4(shape: Shape) -> np.ndarray:
        """Create 2-D quad-mesh connectivity from face `shape`.

        The connectivity ordering of the quad-mesh face nodes (points) is
        anti-clockwise, as follows:

            3---2
            |   |
            0---1

        Assumes that the associated face node spatial coordinates are
        appropriately ordered.

        Parameters
        ----------
        shape : Shape
            The shape of the 2-D mesh faces.

        Returns
        -------
        ndarray
            The connectivity array of face-to-node offsets (zero-based).

        Notes
        -----
        ..versionadded:: 0.1.0

        For VTK Quadrilateral cell type node ordering see
        https://kitware.github.io/vtk-examples/site/VTKBook/05Chapter5/#54-cell-types

        """
        # sanity check - internally this should always be the case
        assert len(shape) == 2

        # we know that we can only be dealing with a quad mesh
        npts = np.prod(shape) * 4

        return np.arange(npts, dtype=np.uint32).reshape(-1, 4)

    @staticmethod
    def _verify_2d(xs: ArrayLike, ys: ArrayLike) -> None:
        """Ensure compatible quad-mesh dimensionality and shape.

        Verify the fitness of the provided x-values and y-values to create
        a (M, N) quad-mesh consisting of M*N faces.

        Parameters
        ----------
        xs : ArrayLike
            A (M+1, N+1) or (M, N, 4) x-axis array.
        ys : ArrayLike
            A (M+1, N+1) or (M, N, 4) y-axis array.

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
                "Require 2-D x-values with shape '(M+1, N+1)', or 3-D "
                f"x-values with shape '(M, N, 4)', got {xs.ndim}-D with "
                f"shape '{xs.shape}'."
            )
            raise ValueError(emsg)

        if xs.ndim == 2 and (xs.shape[0] < 2 or xs.shape[1] < 2):
            emsg = (
                "Require a quad-mesh with at least one face and four "
                "points/vertices i.e., minimal shape '(2, 2)', got "
                f"x-values/y-values with shape '{xs.shape}'."
            )
            raise ValueError(emsg)

    @staticmethod
    def _verify_connectivity(connectivity: Shape) -> None:
        """Ensure compatible 2-D connectivity.

        The connectivity shape must be 2-D and contain at least the minimal number of
        indices to construct a mesh with a single triangular face.

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
                f"{len(connectivity)}-D connectivity array with shape "
                f"'{connectivity}'."
            )
            raise ValueError(emsg)

        if connectivity[1] < 3:
            emsg = (
                "Require a connectivity array defining at least 3 vertices "
                "per mesh face (triangles) i.e., minimal shape '(M, 3)', got "
                f"connectivity with shape '{connectivity}'."
            )
            raise ValueError(emsg)

    @classmethod
    def from_1d(
        cls,
        xs: ArrayLike,
        ys: ArrayLike,
        data: ArrayLike | None = None,
        name: str | None = None,
        crs: CRSLike | None = None,
        rgb: bool | None = False,
        radius: float | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        clean: bool | None = None,
    ) -> pv.PolyData:
        """Build a quad-faced mesh from contiguous 1-D x-values and y-values.

        This allows the construction of a uniform or rectilinear quad-faced
        ``(M, N)`` mesh grid, where the mesh has ``M``-faces in the y-axis, and
        ``N``-faces in the x-axis, resulting in a mesh consisting of ``M*N`` faces.

        The provided `xs` and `ys` will be projected from their `crs` to
        geographic longitude and latitude values.

        Parameters
        ----------
        xs : ArrayLike
            A 1-D array of x-values, in canonical `crs` units, defining the
            contiguous face x-value boundaries of the mesh. Creating a mesh
            with ``N``-faces in the `crs` x-axis requires a ``(N+1,)`` array.
            Alternatively, a ``(N, 2)`` contiguous bounds array may be provided.
        ys : ArrayLike
            A 1-D array of y-values, in canonical `crs` units, defining the
            contiguous face y-value boundaries of the mesh. Creating a mesh
            with ``M``-faces in the `crs` y-axis requires a ``(M+1,)`` array.
            Alternatively, a ``(M, 2)`` contiguous bounds array may be provided.
        data : ArrayLike, optional
            Data to be optionally attached to the mesh. The size of the data
            must match either the shape of the fully formed mesh points
            ``(M+1)*(N+1)``,
            or the number of mesh faces, ``M*N`` (but see the `rgb` parameter).
        name : str, optional
            The name of the optional data array to be attached to the mesh. If
            `data` is provided but with no `name`, defaults to either
            :data:`NAME_POINTS` or :data:`NAME_CELLS`.
        crs : CRSLike, optional
            The Coordinate Reference System of the provided `xs` and `ys`. May
            be anything accepted by :meth:`pyproj.crs.CRS.from_user_input`. Defaults
            to ``EPSG:4326`` i.e., ``WGS 84``.
        rgb : bool, default=False
            Whether `data` is an ``RGB`` or ``RGBA`` image. When ``rgb=True``,
            `data` is expected to have an extra dimension for the colour
            channels (length ``3`` or ``4``).
        radius : float, optional
            The radius of the sphere. Defaults to :data:`~geovista.common.RADIUS`.
        zlevel : int, default=0
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`~geovista.common.ZLEVEL_SCALE`.
        clean : bool, optional
            Specify whether to merge duplicate points, remove unused points,
            and/or remove degenerate cells in the resultant mesh. See
            :meth:`pyvista.PolyDataFilters.clean`. Defaults to
            :data:`BRIDGE_CLEAN`.

        Returns
        -------
        PolyData
            The quad-faced spherical mesh.

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
            zlevel=zlevel,
            zscale=zscale,
            clean=clean,
            rgb=rgb,
        )

    @classmethod
    def from_2d(
        cls,
        xs: ArrayLike,
        ys: ArrayLike,
        data: ArrayLike | None = None,
        name: str | None = None,
        crs: CRSLike | None = None,
        rgb: bool | None = False,
        radius: float | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        clean: bool | None = None,
    ) -> pv.PolyData:
        """Build a quad-faced mesh from 2-D x-values and y-values.

        This allows the construction of a uniform, rectilinear or curvilinear
        quad-faced ``(M, N)`` mesh grid, where the mesh has ``M``-faces in the y-axis,
        and ``N``-faces in the x-axis, resulting in a mesh consisting of ``M*N`` faces.

        The provided `xs` and `ys` define the four vertices of each quad-face
        in the mesh for the native `crs`, which will then be projected to
        geographic longitude and latitude values.

        Parameters
        ----------
        xs : ArrayLike
            A 2-D array of x-values, in canonical `crs` units, defining the
            face x-value boundaries of the mesh. Creating a ``(M, N)`` mesh
            requires a ``(M+1, N+1)`` x-axis array. Alternatively, a ``(M, N, 4)``
            array may be provided.
        ys : ArrayLike
            A 2-D array of y-values, in canonical `crs` units, defining the
            face y-value boundaries of the mesh. Creating a ``(M, N)`` mesh
            requires a ``(M+1, N+1)`` y-axis array. Alternatively, a ``(M, N, 4)``
            array may be provided.
        data : ArrayLike, optional
            Data to be optionally attached to the mesh. The size of the data
            must match either the shape of the fully formed mesh points
            ``(M+1)*(N+1)``,
            or the number of mesh faces, ``M*N`` (but see the `rgb` parameter).
        name : str, optional
            The name of the optional data array to be attached to the mesh. If
            `data` is provided but with no `name`, defaults to either
            :data:`NAME_POINTS` or :data:`NAME_CELLS`.
        crs : CRSLike, optional
            The Coordinate Reference System of the provided `xs` and `ys`. May
            be anything accepted by :meth:`pyproj.crs.CRS.from_user_input`. Defaults
            to ``EPSG:4326`` i.e., ``WGS 84``.
        rgb : bool, default=False
            Whether `data` is an ``RGB`` or ``RGBA`` image. When ``rgb=True``,
            `data` is expected to have an extra dimension for the colour
            channels (length ``3`` or ``4``).
        radius : float, optional
            The radius of the sphere. Defaults to :data:`~geovista.common.RADIUS`.
        zlevel : int, default=0
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`~geovista.common.ZLEVEL_SCALE`.
        clean : bool, optional
            Specify whether to merge duplicate points, remove unused points,
            and/or remove degenerate cells in the resultant mesh. See
            :meth:`pyvista.PolyDataFilters.clean`. Defaults to
            :data:`BRIDGE_CLEAN`.

        Returns
        -------
        PolyData
            The quad-faced spherical mesh.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        xs, ys = np.asanyarray(xs), np.asanyarray(ys)
        cls._verify_2d(xs, ys)
        shape, ndim = xs.shape, xs.ndim

        if ndim == 2:
            # we have shape (M+1, N+1)
            rows, cols = points_shape = shape
            cells_shape = (rows - 1, cols - 1)
        else:
            # we have shape (M, N, 4)
            rows, cols = cells_shape = shape[:-1]
            points_shape = (rows + 1, cols + 1)

        # generate connectivity (topology) map of indices into the geometry
        connectivity = (
            cls._create_connectivity_m1n1(points_shape)
            if ndim == 2
            else cls._create_connectivity_mn4(cells_shape)
        )

        return Transform.from_unstructured(
            xs,
            ys,
            connectivity=connectivity,
            data=data,
            name=name,
            crs=crs,
            radius=radius,
            zlevel=zlevel,
            zscale=zscale,
            clean=clean,
            rgb=rgb,
        )

    @classmethod
    def from_points(
        cls,
        xs: ArrayLike,
        ys: ArrayLike,
        data: ArrayLike | None = None,
        name: str | None = None,
        crs: CRSLike | None = None,
        radius: float | None = None,
        zlevel: int | ArrayLike | None = None,
        zscale: float | None = None,
        clean: bool | None = None,
    ) -> pv.PolyData:
        """Build a point-cloud mesh from x-values, y-values and z-levels.

        Note that, any optional mesh `data` provided must be in the same order as the
        spatial points.

        Parameters
        ----------
        xs : ArrayLike
            A 1-D, 2-D or 3-D array of point-cloud x-values, in canonical `crs` units.
            Must have the same shape as the `ys`.
        ys : ArrayLike
            A 1-D, 2-D or 3-D array of point-cloud y-values, in canonical `crs` units.
            Must have the same shape as the `xs`.
        data : ArrayLike, optional
            Data to be optionally attached to the mesh points defined by
            `xs` and `ys`.
        name : str, optional
            The name of the optional data array to be attached to the mesh. If `data`
            is provided but with no `name`, defaults to :data:`NAME_POINTS`.
        crs : CRSLike, optional
            The Coordinate Reference System of the provided `xs` and `ys`. May
            be anything accepted by :meth:`pyproj.crs.CRS.from_user_input`. Defaults
            to ``EPSG:4326`` i.e., ``WGS 84``.
        radius : float, optional
            The radius of the mesh point-cloud. Defaults to
            :data:`~geovista.common.RADIUS`.
        zlevel : int or ArrayLike, default=0
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
            If `zlevel` is not a scalar, then its shape must match or broadcast
            with the shape of the `xs` and `ys`.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`~geovista.common.ZLEVEL_SCALE`.
        clean : bool, optional
            Specify whether to merge duplicate points. See
            :meth:`pyvista.PolyDataFilters.clean`. Defaults to
            :data:`BRIDGE_CLEAN`.

        Returns
        -------
        PolyData
            The point-cloud spherical mesh.

        Notes
        -----
        .. versionadded:: 0.2.0

        """
        radius = RADIUS if radius is None else abs(float(radius))
        zscale = ZLEVEL_SCALE if zscale is None else float(zscale)

        if crs is not None:
            crs = pyproj.CRS.from_user_input(crs)

            if crs != WGS84:
                transformed = transform_points(src_crs=crs, tgt_crs=WGS84, xs=xs, ys=ys)
                xs, ys = transformed[:, 0], transformed[:, 1]

        # ensure longitudes (degrees) are in half-closed interval [-180, 180)
        xs = wrap(xs)

        # reduce any singularity points at the poles to a common longitude
        poles = np.isclose(np.abs(ys), 90)
        if np.any(poles):
            xs[poles] = 0

        # convert lat/lon to cartesian xyz
        xyz = to_cartesian(xs, ys, radius=radius, zlevel=zlevel, zscale=zscale)

        # create the point-cloud mesh
        mesh = pv.PolyData(xyz)

        # attach the pyproj crs serialized as ogc wkt
        to_wkt(mesh, WGS84)

        # attach the original base radius and zscale
        mesh.field_data[GV_FIELD_RADIUS] = np.array([radius])
        mesh.field_data[GV_FIELD_ZSCALE] = np.array([zscale])

        # attach any optional data to the mesh
        if data is not None:
            data = cls._as_compatible_data(data, mesh.n_points, mesh.n_cells)

            if not name:
                name = NAME_POINTS
            if not isinstance(name, str):
                name = str(name)

            mesh.field_data[GV_FIELD_NAME] = np.array([name])
            mesh[name] = data

        # clean the mesh
        if clean:
            mesh.clean(inplace=True)

        return mesh

    @classmethod
    def from_tiff(
        cls,
        fname: PathLike,
        name: str | None = None,
        band: int | None = 1,
        rgb: bool | None = False,
        sieve: bool | None = False,
        size: int | None = None,
        extract: bool | None = False,
        radius: float | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        clean: bool | None = None,
    ) -> pv.PolyData:
        """Build a quad-faced mesh from the GeoTIFF.

        Note that, the GeoTIFF data will be located on the ``points``
        of the resultant mesh.

        Parameters
        ----------
        fname : PathLike
            The file path to the GeoTIFF.
        name : str, optional
            The name of the GeoTIFF data array to be attached to the mesh.
            Defaults to :data:`NAME_POINTS`. Note that, ``{units}`` may be
            used as a placeholder for the units of the data array e.g.,
            ``"Elevation / {units}"``.
        band : int, optional
            The band index to read from the GeoTIFF. Note that, the `band`
            index is one-based. Defaults to the first band i.e., ``band=1``.
        rgb : bool, default=False
            Specify whether to read the GeoTIFF as an ``RGB`` or ``RGBA`` image.
            When ``rgb=True``, the `band` index is ignored.
        sieve : bool, default=False
            Specify whether to sieve the GeoTIFF mask to remove small connected
            regions. See :func:`rasterio.features.sieve` for more information.
        size : int, optional
            The size of the `sieve` filter. Defaults to :data:`RIO_SIEVE_SIZE`.
        extract : bool, default=False
            Specify whether to extract cells from the mesh with no masked points.
        radius : float, optional
            The radius of the mesh sphere. Defaults to :data:`~geovista.common.RADIUS`.
        zlevel : int, default=0
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`~geovista.common.ZLEVEL_SCALE`.
        clean : bool, optional
            Specify whether to merge duplicate points, remove unused points,
            and/or remove degenerate cells in the resultant mesh. See
            :meth:`pyvista.PolyDataFilters.clean`. Defaults to
            :data:`BRIDGE_CLEAN`.

        Returns
        -------
        PolyData
            The GeoTIFF spherical mesh.

        Notes
        -----
        .. versionadded:: 0.5.0

        .. attention:: Optional package dependency :mod:`rasterio` is required.

        Examples
        --------
        >>> from geovista import GeoPlotter, Transform
        >>> from geovista.pantry import fetch_raster
        >>> from geovista.pantry.textures import natural_earth_1

        Render the GeoTIFF ``RGB`` image as a geolocated mesh.

        First, :func:`rasterio.features.sieve` the GeoTIFF image to remove several
        unwanted masked regions within the interior of the image, due to a lack of
        dynamic range in the ``uint8`` image data. Then, extract the mesh to remove
        cells with no masked points.

        >>> fname = fetch_raster("bahamas_rgb.tif")
        >>> mesh = Transform.from_tiff(fname, rgb=True, sieve=True, extract=True)

        Now render the result:

        >>> plotter = GeoPlotter()
        >>> _ = plotter.add_mesh(mesh, rgb=True)
        >>> plotter.view_poi()
        >>> _ = plotter.add_base_layer(texture=natural_earth_1(), zlevel=0)
        >>> _ = plotter.add_coastlines(color="white")
        >>> plotter.show()

        """
        try:
            import rasterio as rio
        except ImportError:
            emsg = (
                "Optional dependency 'rasterio' is required to read GeoTIFF files. "
                "Use pip or conda to install."
            )
            raise ImportError(emsg) from None

        if isinstance(fname, str):
            fname = Path(fname)

        fname = fname.resolve(strict=True)
        band = None if rgb else band

        if size is None:
            size = RIO_SIEVE_SIZE

        with rio.open(fname, mode="r") as src:
            count = src.count

            if rgb:
                if count not in [3, 4]:
                    plural = "s" if count > 1 else ""
                    emsg = (
                        f"Require a GeoTIFF with 3 or 4 bands to read as "
                        f"an RGB or RGBA image, only {count} band{plural} "
                        "available."
                    )
                    raise ValueError(emsg)
            elif band < 1 or band > count:
                if count == 1:
                    emsg = f"Require a band index of 1, got '{band}'."
                else:
                    emsg = (
                        f"Require a band index in the closed interval [1, {count}], "
                        f"got '{band}'."
                    )
                raise ValueError(emsg)

            if name is not None:
                name = str(name)
                if "{units}" in name:
                    units = str(src.units[0] if rgb else src.units[band - 1])
                    name = name.format(units=units)

            data = src.read(masked=extract) if rgb else src.read(band, masked=extract)

            if extract:
                # ignore the mask on the alpha channel, if present
                mask = data[0].mask & data[1].mask & data[2].mask if rgb else data.mask
                # ensure there is masked data prior to extracting unmasked points
                extract = np.sum(mask) > 0
                data = data.data

            if rgb:
                data = np.dstack(data).reshape(-1, count)

            # transform from pixel offsets to crs coordinates
            cols, rows = np.meshgrid(
                np.arange(src.width), np.arange(src.height), indexing="xy"
            )
            # rasterio 1.4.0 (regression) expects 1-D arrays, fixed in 1.4.1
            # see https://github.com/rasterio/rasterio/issues/3191
            xs, ys = rio.transform.xy(src.transform, rows.flatten(), cols.flatten())

            # ensure we have arrays, rather than a list of arrays
            xs, ys = np.asanyarray(xs), np.asanyarray(ys)

            # ensure shape is maintained (rasterio 1.4.1 regression)
            if xs.shape != src.shape:
                xs = xs.reshape(src.shape)

            if ys.shape != src.shape:
                ys = ys.reshape(src.shape)

            # create the geotiff mesh
            mesh = cls.from_2d(
                xs,
                ys,
                data=data,
                name=name,
                crs=src.crs,
                rgb=rgb,
                radius=radius,
                zlevel=zlevel,
                zscale=zscale,
                clean=clean,
            )

            if extract:
                if sieve:
                    from rasterio.features import sieve as riosieve

                    # convert boolean mask to conform to GDAL RFC 15 for sieve
                    # see https://trac.osgeo.org/gdal/wiki/rfc15_nodatabitmask
                    dtype = np.dtype(src.dtypes[0])
                    muint = 2 ** (dtype.itemsize * 8) - 1
                    mask = (~mask * muint).astype(dtype)
                    mask = riosieve(mask, size=size)
                    # convert back to boolean mask
                    mask = ~mask.astype(bool)

                # extract cells with no masked points
                mesh = mesh.extract_points(~np.ravel(mask), adjacent_cells=False)
                mesh = cast_UnstructuredGrid_to_PolyData(mesh)

            return mesh

    @classmethod
    def from_unstructured(
        cls,
        xs: ArrayLike,
        ys: ArrayLike,
        connectivity: ArrayLike | Shape | None = None,
        data: ArrayLike | None = None,
        start_index: int | None = None,
        name: str | None = None,
        crs: CRSLike | None = None,
        rgb: bool | None = None,
        radius: float | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        clean: bool | None = None,
    ) -> pv.PolyData:
        """Build a mesh from unstructured 1-D x-values and y-values.

        The `connectivity` defines the topology of faces within the
        unstructured mesh. This is represented in terms of indices into the
        provided `xs` and `ys` mesh geometry.

        Note that any optional mesh `data` provided must be in the same order
        as the mesh face `connectivity`, or in the same order as the points
        described by `xs` & `ys` (data can be on points or on cells).

        Parameters
        ----------
        xs : ArrayLike
            A 1-D array of x-values, in canonical `crs` units, defining the
            vertices of each face in the mesh.
        ys : ArrayLike
            A 1-D array of y-values, in canonical `crs` units, defining the
            vertices of each face in the mesh.
        connectivity : ArrayLike or Shape, optional
            Defines the topology of each face in the unstructured mesh in terms
            of indices into the provided `xs` and `ys` mesh geometry
            arrays. The `connectivity` is a 2-D ``(M, N)`` array, where ``M`` is
            the number of mesh faces, and ``N`` is the number of nodes per
            face. Alternatively, an ``(M, N)`` tuple defining the connectivity
            shape may be provided instead, given that the `xs` and `ys` define
            ``M*N`` points (at most) in the mesh geometry. If no connectivity is
            provided, and the `xs` and `ys` are 2-D, then their shape is used
            to determine the connectivity. Also, note that masked connectivity
            may be used to define a mesh consisting of different shaped faces.
        data : ArrayLike, optional
            Data to be optionally attached to the mesh face or nodes.
        start_index : int, default=0
            Specify the base index of the provided `connectivity` in the
            closed interval [0, 1]. For example, if `start_index=1`, then
            the `start_index` will be subtracted from the `connectivity`
            to result in 0-based indices into the provided mesh geometry.
            If no `start_index` is provided, then it will be determined
            from the `connectivity`.
        name : str, optional
            The name of the optional data array to be attached to the mesh. If
            `data` is provided but with no `name`, defaults to either
            :data:`NAME_POINTS` or :data:`NAME_CELLS`.
        crs : CRSLike, optional
            The Coordinate Reference System of the provided `xs` and `ys`. May
            be anything accepted by :meth:`pyproj.crs.CRS.from_user_input`. Defaults
            to ``EPSG:4326`` i.e., ``WGS 84``.
        rgb : bool, default=False
            Whether `data` is an ``RGB`` or ``RGBA`` image. When ``rgb=True``,
            `data` is expected to have an extra dimension for the colour
            channels (length ``3`` or ``4``).
        radius : float, optional
            The radius of the mesh sphere. Defaults to :data:`~geovista.common.RADIUS`.
        zlevel : int, default=0
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`~geovista.common.ZLEVEL_SCALE`.
        clean : bool, optional
            Specify whether to merge duplicate points, remove unused points,
            and/or remove degenerate cells in the resultant mesh. See
            :meth:`pyvista.PolyDataFilters.clean`. Defaults to
            :data:`BRIDGE_CLEAN`.

        Returns
        -------
        PolyData
            The ``(M*N)``-faced spherical mesh.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        xs, ys = np.asanyarray(xs), np.asanyarray(ys)
        shape = xs.shape

        if ys.shape != shape:
            emsg = (
                "Require x-values and y-values with the same shape, got "
                f"'{shape}' and '{ys.shape}' respectively."
            )
            raise ValueError(emsg)

        if xs.size < 3:
            emsg = (
                "Require a mesh to have at least one face with three "
                "points/vertices i.e., minimal shape '(3,)', got "
                f"x-values/y-values with shape '{shape}'."
            )
            raise ValueError(emsg)

        xs, ys = xs.ravel(), ys.ravel()

        if crs is not None:
            crs = pyproj.CRS.from_user_input(crs)

            if crs != WGS84:
                transformed = transform_points(src_crs=crs, tgt_crs=WGS84, xs=xs, ys=ys)
                xs, ys = transformed[:, 0], transformed[:, 1]

        # ensure longitudes (degrees) are in half-closed interval [-180, 180)
        xs = wrap(xs)

        if connectivity is None:
            # default to the shape of the points
            connectivity = shape

            # generate connectivity from masked points
            if (
                np.ma.is_masked(xs)
                and np.ma.is_masked(ys)
                and np.array_equal(xs.mask, ys.mask)
            ):
                connectivity = np.ma.arange(np.ma.prod(shape), dtype=np.uint32).reshape(
                    shape
                )
                connectivity.mask = xs.mask

        if isinstance(connectivity, tuple):
            cls._verify_connectivity(connectivity)
            npts = np.prod(connectivity)

            if npts != xs.size:
                emsg = (
                    f"Connectivity with shape '{connectivity}' requires "
                    f"'{npts:,d}' x-values/y-values, but only "
                    f"'{xs.size:,d}' have been provided."
                )
                raise ValueError(emsg)

            connectivity = np.arange(npts, dtype=np.uint32).reshape(connectivity)
            ignore_start_index = True
        else:
            # require to copy connectivity, otherwise results in a memory
            # corruption within vtk
            connectivity = np.asanyarray(connectivity).copy()
            cls._verify_connectivity(connectivity.shape)
            ignore_start_index = False

        if not ignore_start_index:
            if start_index is None:
                start_index = connectivity.min()

            if start_index not in [0, 1]:
                emsg = (
                    "Require a 'start_index' in the closed interval [0, 1], got "
                    f"'{start_index}'."
                )
                raise ValueError(emsg)

            if start_index:
                connectivity -= start_index

        # reduce any singularity points at the poles to a common longitude
        poles = np.isclose(np.abs(ys), 90)
        if np.any(poles):
            xs[poles] = 0

        radius = RADIUS if radius is None else abs(float(radius))
        zscale = ZLEVEL_SCALE if zscale is None else float(zscale)
        zlevel = 0 if zlevel is None else int(zlevel)
        radius += radius * zlevel * zscale

        # convert lat/lon to cartesian xyz
        geometry = to_cartesian(xs, ys, radius=radius)

        if np.ma.is_masked(connectivity):
            # create face connectivity from masked vertex indices, thus
            # supporting varied mesh face geometry e.g., triangular, quad,
            # pentagon (et al) cells within a single mesh.
            connectivity = np.atleast_2d(connectivity)
            if (ndim := connectivity.ndim) > 2:
                emsg = f"Masked connectivity must be at most 2-D, got {ndim}-D."
                raise ValueError(emsg)
            n_faces = connectivity.shape[0]
            n_vertices = np.ma.sum(~connectivity.mask, axis=1)
            # ensure at least three vertices per face
            valid_faces_mask = n_vertices > 2
            if not np.all(valid_faces_mask):
                n_invalid = n_faces - np.sum(valid_faces_mask)
                plural = "s" if n_invalid > 1 else ""
                wmsg = (
                    f"geovista masked connectivity defines {n_invalid:,} face{plural} "
                    "with no vertices."
                )
                warnings.warn(wmsg, stacklevel=2)
                n_vertices = n_vertices[valid_faces_mask]
                connectivity = connectivity[valid_faces_mask]
            faces = np.ma.hstack([n_vertices.reshape(-1, 1), connectivity]).ravel()
            faces = faces[~faces.mask].data
        else:
            # create face connectivity serialization e.g., for a quad-mesh,
            # each face we have (4, V0, V1, V2, V3), where "4" is the number
            # of vertices defining the face, followed by the four indices (Vn)
            # specifying each of the face vertices in an anti-clockwise order
            # into the mesh geometry.
            n_faces, n_vertices = connectivity.shape
            faces = np.hstack(
                [
                    np.broadcast_to(
                        np.array([n_vertices], dtype=np.int8), (n_faces, 1)
                    ),
                    connectivity,
                ]
            )

        # create the mesh
        mesh = pv.PolyData(geometry, faces=faces)

        # attach the pyproj crs serialized as ogc wkt
        to_wkt(mesh, WGS84)

        # attach the radius
        mesh.field_data[GV_FIELD_RADIUS] = np.array([radius])

        # attach any optional data to the mesh
        if data is not None:
            data = cls._as_compatible_data(data, mesh.n_points, mesh.n_cells, rgb)
            if not name:
                size = data.size // data.shape[-1] if rgb else data.size
                name = NAME_POINTS if size == mesh.n_points else NAME_CELLS
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
        connectivity: ArrayLike | Shape | None = None,
        start_index: int | None = None,
        crs: CRSLike | None = None,
        radius: float | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        clean: bool | None = None,
    ) -> None:
        """Build a mesh from spatial points, connectivity, data and CRS metadata.

        Convenience factory to build multiple identical meshes but with different face
        or node data.

        Parameters
        ----------
        xs : ArrayLike
            A 1-D array of x-values, in canonical `crs` units, defining the
            vertices of each face in the mesh.
        ys : ArrayLike
            A 1-D array of y-values, in canonical `crs` units, defining the
            vertices of each face in the mesh.
        connectivity : ArrayLike or Shape, optional
            Defines the topology of each face in the unstructured mesh in terms
            of indices into the provided `xs` and `ys` mesh geometry
            arrays. The `connectivity` is a 2-D ``(M, N)`` array, where ``M`` is
            the number of mesh faces, and ``N`` is the number of nodes per
            face. Alternatively, an ``(M, N)`` tuple defining the connectivity
            shape may be provided instead, given that the `xs` and `ys` define
            ``M*N`` points (at most) in the mesh geometry. If no connectivity is
            provided, and the `xs` and `ys` are 2-D, then their shape is used
            to determine the connectivity.  Also, note that masked connectivity
            may be used to define a mesh consisting of different shaped faces.
        start_index : int, default=0
            Specify the base index of the provided `connectivity` in the
            closed interval [0, 1]. For example, if `start_index=1`, then
            the `start_index` will be subtracted from the `connectivity`
            to result in 0-based indices into the provided mesh geometry.
            If no `start_index` is provided, then it will be determined
            from the `connectivity`.
        crs : CRSLike, optional
            The Coordinate Reference System of the provided `xs` and `ys`. May
            be anything accepted by :meth:`pyproj.crs.CRS.from_user_input`. Defaults
            to ``EPSG:4326`` i.e., ``WGS 84``.
        radius : float, optional
            The radius of the mesh sphere. Defaults to :data:`~geovista.common.RADIUS`.
        zlevel : int, default=0
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`~geovista.common.ZLEVEL_SCALE`.
        clean : bool, optional
            Specify whether to merge duplicate points, remove unused points,
            and/or remove degenerate cells in the resultant mesh. See
            :meth:`pyvista.PolyDataFilters.clean`. Defaults to
            :data:`BRIDGE_CLEAN`.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        xs, ys = np.asanyarray(xs), np.asanyarray(ys)

        if connectivity is None:
            if xs.ndim <= 1 or ys.ndim <= 1:
                mesh = self.from_1d(
                    xs,
                    ys,
                    crs=crs,
                    radius=radius,
                    zlevel=zlevel,
                    zscale=zscale,
                    clean=clean,
                )
            else:
                mesh = self.from_2d(
                    xs,
                    ys,
                    crs=crs,
                    radius=radius,
                    zlevel=zlevel,
                    zscale=zscale,
                    clean=clean,
                )
        else:
            mesh = self.from_unstructured(
                xs,
                ys,
                connectivity=connectivity,
                start_index=start_index,
                crs=crs,
                radius=radius,
                clean=clean,
                zlevel=zlevel,
                zscale=zscale,
            )

        self._mesh = mesh
        self._n_points = mesh.n_points
        self._n_cells = mesh.n_cells

    def __call__(
        self, data: ArrayLike | None = None, name: str | None = None
    ) -> pv.PolyData:
        """Build the mesh and attach the provided `data` to faces or nodes.

        Parameters
        ----------
        data : ArrayLike, optional
            Data to be optionally attached to the mesh face or nodes.
        name : str, optional
            The name of the optional data array to be attached to the mesh. If
            `data` is provided but with no `name`, defaults to either
            :data:`NAME_POINTS` or :data:`NAME_CELLS`.

        Returns
        -------
        PolyData
            The spherical mesh.

        Notes
        -----
        ..versionadded:: 0.1.0

        """
        if data is not None:
            data = self._as_compatible_data(data, self._n_points, self._n_cells)

        mesh = pv.PolyData()
        mesh.copy_structure(self._mesh)

        if data is not None:
            if not name:
                name = NAME_POINTS if data.size == self._n_points else NAME_CELLS

            mesh.field_data[GV_FIELD_NAME] = np.array([name])
            mesh[name] = data

        return mesh
