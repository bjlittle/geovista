"""Coordinate reference system (CRS) transformation functions.

Notes
-----
.. versionadded:: 0.3.0

"""
from __future__ import annotations

from copy import deepcopy

import numpy as np
from numpy.typing import ArrayLike
from pyproj import CRS, Transformer
import pyvista as pv

from .common import GV_FIELD_ZSCALE, ZLEVEL_SCALE, from_cartesian, point_cloud
from .crs import (
    WGS84,
    CRSLike,
    from_wkt,
    get_central_meridian,
    set_central_meridian,
    to_wkt,
)

__all__ = [
    "transform_mesh",
    "transform_point",
    "transform_points",
]


def transform_mesh(
    mesh: pv.PolyData,
    tgt_crs: CRSLike,
    slice_connectivity: bool | None = True,
    rtol: float | None = None,
    atol: float | None = None,
    zlevel: float | ArrayLike | None = None,
    zscale: float | None = None,
    inplace: bool | None = False,
) -> pv.PolyData:
    """Transform the mesh from its source CRS to the target CRS.

    Parameters
    ----------
    mesh : PolyData
        The mesh to be transformed from its source coordinate reference system (CRS) to
        the given `tgt_crs`.
    tgt_crs : CRSLike
        The target coordinate reference system (CRS) of the transformation.
    slice_connectivity : bool, default=True
        Slice the mesh prior to transformation in order to break mesh connectivity and
        create a seam in the mesh. Also see :func:`geovista.core.slice_mesh`.
    rtol : float, optional
        The relative tolerance for values close to longitudinal
        :func:`geovista.common.wrap` base + period.
    atol : float, optional
        The absolute tolerance for values close to longitudinal
        :func:`geovista.common.wrap` base + period.
    zlevel : int or ArrayLike, default=0
        The z-axis level. Used in combination with the `zscale` to offset the
        `radius`/vertical by a proportional amount e.g., ``radius * zlevel * zscale``.
        If `zlevel` is not a scalar, then its shape must match or broadcast
        with the shape of the ``mesh.points``.
    zscale : float, optional
        The proportional multiplier for z-axis `zlevel`. Defaults to
        :data:`geovista.common.ZLEVEL_SCALE`.
    inplace : bool, default=False
        Update the `mesh` in-place. Can only perform an in-place operation when
        ``slice_connectivity=False``

    Returns
    -------
    PolyData
        The mesh transformed to the target coordinate reference system (CRS).

    Notes
    -----
    .. versionadded:: 0.3.0

    """
    from .core import slice_mesh

    src_crs = from_wkt(mesh)

    if src_crs is None:
        emsg = "Cannot transform mesh, no coordinate reference system (CRS) attached."
        raise ValueError(emsg)

    # sanity check the target crs
    tgt_crs = CRS.from_user_input(tgt_crs)

    original_tgt_crs = deepcopy(tgt_crs)
    transform_required = src_crs != tgt_crs
    central_meridian = get_central_meridian(tgt_crs) or 0
    cloud = point_cloud(mesh)

    if zlevel is None:
        zlevel = 0

    if zscale is None:
        if cloud and GV_FIELD_ZSCALE in mesh.field_data:
            zscale = mesh[GV_FIELD_ZSCALE]
        else:
            zscale = ZLEVEL_SCALE

    if transform_required:
        # slice the mesh to break connectivity, but not for a point-cloud
        if slice_connectivity:
            if central_meridian:
                mesh.rotate_z(-central_meridian, inplace=True)
                tgt_crs = set_central_meridian(tgt_crs, 0)

            if not cloud:
                # the sliced_mesh is guaranteed to be a new instance,
                # even if not bisected
                sliced_mesh = slice_mesh(mesh, rtol=rtol, atol=atol)
            else:
                sliced_mesh = mesh.copy()

            if central_meridian:
                # undo rotation of original mesh
                mesh.rotate_z(central_meridian, inplace=True)

            mesh = sliced_mesh

        # now perform the CRS transformation
        if src_crs == WGS84:
            xyz = from_cartesian(mesh, closed_interval=True, rtol=rtol, atol=atol)
        else:
            xyz = mesh.points

        transformed = transform_points(
            src_crs=src_crs, tgt_crs=tgt_crs, xs=xyz[:, 0], ys=xyz[:, 1]
        )
        xs, ys = transformed[:, 0], transformed[:, 1]
        zs = 0

        if not inplace and not slice_connectivity:
            mesh = mesh.copy(deep=True)

        mesh.points[:, 0] = xs
        mesh.points[:, 1] = ys

        if zlevel or cloud:
            xmin, xmax, ymin, ymax, _, _ = mesh.bounds
            xdelta, ydelta = abs(xmax - xmin), abs(ymax - ymin)
            # TODO: make this scale factor configurable at the API/module level
            # current strategy is slightly flawed in that there isn't consistent
            # scaling across all geometries added to the render
            delta = max(xdelta, ydelta) // 4

            if cloud:
                # extract the zlevel encoded from the non-transformed points
                zlevel += xyz[:, 2]

            zs = zlevel * zscale * delta

        mesh.points[:, 2] = zs

        # TODO: check whether to clean other field_data metadata
        to_wkt(mesh, original_tgt_crs)

    return mesh


def transform_point(
    src_crs: CRSLike,
    tgt_crs: CRSLike,
    x: int | float,
    y: int | float,
    z: int | float | None = None,
    trap: bool | None = True,
) -> ArrayLike:
    """Transform the spatial point from the source to the target CRS.

    Parameters
    ----------
    src_crs : CRSLike
        The source Coordinate Reference System (CRS) of the provided `x`,
        `y` and `z` spatial point. May be anything accepted by
        :meth:`pyproj.CRS.from_user_input`.
    tgt_crs : CRSLike
        The target Coordinate Reference System (CRS) of the transform for
        the spatial point. May be anything accepted by
        :meth:`pyproj.CRS.from_user_input`.
    x : ArrayLike
        The spatial point x-value, in canonical `src_crs` units, to be
        transformed from the `src_crs` to the `tgt_crs`. May be scalar
        or 1-D.
    y : ArrayLike
        The spatial point y-value, in canonical `src_crs` units, to be
        transformed from the `src_crs` to the `tgt_crs`. May be scalar
        or 1-D.
    z : ArrayLike, optional
        The spatial point z-value, in canonical `src_crs` units, to be
        transformed from the `src_crs` to the `tgt_crs`. May be scalar
        or 1-D.
    trap : bool, default=True
        Raise an exception if an error occurs during CRS transformation
        of the spatial point. Otherwise, ``inf`` will be returned for
        the erroneous point.

    Returns
    -------
    ArrayLike
        The transformed spatial point in the canonical units of the target
        CRS. The shape of the result will be ``(3,)``.

    Notes
    -----
    .. versionadded:: 0.4.0

    """
    result = transform_points(
        src_crs=src_crs, tgt_crs=tgt_crs, xs=x, ys=y, zs=z, trap=trap
    )
    shape = result.shape
    assert shape == (1, 3), f"Cannot transform point, got unexpected shape {shape}."
    return result[0]


def transform_points(
    src_crs: CRSLike,
    tgt_crs: CRSLike,
    xs: ArrayLike,
    ys: ArrayLike,
    zs: ArrayLike | None = None,
    trap: bool | None = True,
) -> ArrayLike:
    """Transform the spatial points from the source to the target CRS.

    Parameters
    ----------
    src_crs : CRSLike
        The source Coordinate Reference System (CRS) of the provided `xs`,
        `ys` and `zs` spatial points. May be anything accepted by
        :meth:`pyproj.CRS.from_user_input`.
    tgt_crs : CRSLike
        The target Coordinate Reference System (CRS) of the transform for
        the spatial points. May be anything accepted by
        :meth:`pyproj.CRS.from_user_input`.
    xs : ArrayLike
        The spatial points x-values, in canonical `src_crs` units, to be
        transformed from the `src_crs` to the `tgt_crs`. May be scalar,
        1-D or 2-D.
    ys : ArrayLike
        The spatial points y-values, in canonical `src_crs` units, to be
        transformed from the `src_crs` to the `tgt_crs`. May be scalar,
        1-D or 2-D.
    zs : ArrayLike, optional
        The spatial points z-values, in canonical `src_crs` units, to be
        transformed from the `src_crs` to the `tgt_crs`. May be scalar,
        1-D or 2-D.
    trap : bool, default=True
        Raise an exception if an error occurs during CRS transformation
        of the spatial points. Otherwise, ``inf`` will be returned for
        erroneous points.

    Returns
    -------
    ArrayLike
        The transformed spatial points in the canonical units of the target
        CRS. The shape of the result will either be ``(1, 3)``, ``(M, 3)``
        or ``(M, N, 3)`` depending on whether the provided spatial points
        were scalar, 1-D or 2-D, respectively.

    Notes
    -----
    .. versionadded:: 0.4.0

    """
    xs = np.atleast_1d(xs)
    ys = np.atleast_1d(ys)

    if zs is not None:
        zs = np.atleast_1d(zs)

    # sanity check the crs's
    src_crs = CRS.from_user_input(src_crs)
    tgt_crs = CRS.from_user_input(tgt_crs)

    # sanity check spatial arrays
    if (xndim := xs.ndim) > 2 or (yndim := ys.ndim) > 2:
        emsg = "Cannot transform points, 'xs' and 'ys' must be 1-D or 2-D only."
        raise ValueError(emsg)

    shape = list(xs.shape)

    if xndim != 1:
        xs = xs.flatten()

    if yndim != 1:
        ys = ys.flatten()

    if xs.size != ys.size:
        emsg = (
            "Cannot transform points, 'xs' and 'ys' require same length, "
            f"got {xs.size:,} and {ys.size:,} respectively."
        )
        raise ValueError(emsg)

    if zs is not None:
        if (zndim := zs.ndim) > 2:
            emsg = "Cannot transform points, 'zs' must be 1-D or 2-D only."
            raise ValueError(emsg)

        if zndim != 1:
            zs = zs.flatten()

        if zs.size != xs.size:
            emsg = (
                "Cannot transform points, 'xs' and 'zs' require same length "
                f"got {xs.size:,} and {zs.size:,} respectively."
            )
            raise ValueError(emsg)

    def combine(xs: ArrayLike, ys: ArrayLike, zs: ArrayLike | None = None) -> ArrayLike:
        """Combine the provided points into a single array with shape (N, 3).

        Parameters
        ----------
        xs : ArrayLike
            The x-coordinate points with shape (N,).
        ys : ArrayLike
            The y-coordinate points with shape (N,).
        zs : ArrayLike, optional
            The z-coordinate points with shape (N,).

        Returns
        -------
        ArrayLike
            The (N, 3) array combined from `xs`, `ys`, and `zs`.

        Notes
        -----
        .. versionadded:: 0.4.0

        """
        if zs is None:
            zs = np.zeros_like(xs)

        assert (
            xs.shape == ys.shape == zs.shape
        ), "Cannot combine points, non-uniform shapes."
        return np.vstack([xs, ys, zs]).T

    if src_crs == tgt_crs:
        result = combine(xs, ys, zs)
    else:
        transformer = Transformer.from_crs(src_crs, tgt_crs, always_xy=True)
        transformed = transformer.transform(xs, ys, zs, errcheck=trap)

        if zs is None:
            (txs, tys), tzs = transformed, None
        else:
            txs, tys, tzs = transformed

        result = combine(txs, tys, tzs)

    if xndim == 2:
        shape.append(3)
        result = result.reshape(tuple(shape))

    return result
