# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Coordinate reference system (CRS) transformation functions.

Notes
-----
.. versionadded:: 0.3.0

"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, cast

import lazy_loader as lazy

from .common import (
    GV_FIELD_RADIUS,
    GV_FIELD_ZSCALE,
    GV_POINT_ZLEVEL,
    ZLEVEL_SCALE,
    from_cartesian,
    point_cloud,
    to_cartesian,
    wrap,
)
from .crs import (
    WGS84,
    CRSLike,
    from_wkt,
    get_central_meridian,
    planar,
    set_central_meridian,
    to_wkt,
)

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import ArrayLike, NDArray
    import pyproj
    import pyvista as pv

# lazy import third-party dependencies
np = lazy.load("numpy")
pyproj = lazy.load("pyproj")

__all__ = [
    "transform_mesh",
    "transform_point",
    "transform_points",
]

#: The name a per-point zlevel travels through the seam slice under, prefixed
#: with underscores until no array of the mesh has it.
_ZLEVEL = "gvTransformZLevel"


def transform_mesh(
    mesh: pv.PolyData,
    /,
    tgt_crs: CRSLike,
    *,
    slice_connectivity: bool | None = True,
    radius: float | None = None,
    zlevel: float | ArrayLike | None = None,
    zscale: float | None = None,
    rtol: float | None = None,
    atol: float | None = None,
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
        May be anything accepted by :meth:`pyproj.crs.CRS.from_user_input`.
    slice_connectivity : bool, default=True
        Slice the mesh prior to transformation in order to break mesh connectivity and
        create a seam in the mesh. Also see :func:`geovista.core.slice_mesh`.
    radius : float, optional
        The radius of the sphere. Defaults to the radius a point cloud carries,
        otherwise :data:`geovista.common.RADIUS`.
    zlevel : int or ArrayLike, default=0
        The z-axis level. Used in combination with the `zscale` to offset the
        `radius`/vertical by a proportional amount e.g., ``radius * zlevel * zscale``.
        If `zlevel` is not a scalar, then its shape must match or broadcast
        with the shape of the ``mesh.points``. For a point cloud, `zlevel` adds to
        the z-level each of its points already carries.
    zscale : float, optional
        The proportional multiplier for z-axis `zlevel`. Defaults to the multiplier
        a point cloud carries, otherwise :data:`geovista.common.ZLEVEL_SCALE`.
    rtol : float, optional
        The relative tolerance for longitudes close to the 'wrap meridian' -
        see :func:`geovista.common.wrap` for more.
    atol : float, optional
        The absolute tolerance for longitudes close to the 'wrap meridian' -
        see :func:`geovista.common.wrap` for more.
    inplace : bool, default=False
        Update the `mesh` in-place. Can only perform an in-place operation when
        ``slice_connectivity=False``.

    Returns
    -------
    PolyData
        The mesh transformed to the target coordinate reference system (CRS).

    Notes
    -----
    A point cloud keeps its z-levels from one transform to the next. On the sphere
    they are encoded in the radius of each point, and in a planar CRS they are
    carried in the :data:`geovista.common.GV_POINT_ZLEVEL` point array.

    .. versionadded:: 0.3.0

    """
    from .core import slice_mesh  # noqa: PLC0415

    src_crs = from_wkt(mesh)

    if src_crs is None:
        emsg = "Cannot transform mesh, no coordinate reference system (CRS) attached."
        raise ValueError(emsg)

    # override: only slice connectivity for a spherical src crs, as slicing
    # operates on cartesian xyz points, which only a WGS84 mesh carries
    if slice_connectivity:
        slice_connectivity = not planar(src_crs)

    # sanity check the target crs
    tgt_crs = pyproj.CRS.from_user_input(tgt_crs)

    original_tgt_crs = deepcopy(tgt_crs)
    transform_required = src_crs != tgt_crs
    central_meridian = get_central_meridian(tgt_crs) or 0
    cloud = point_cloud(mesh)

    level = np.asanyarray(0 if zlevel is None else zlevel)

    if zscale is None:
        if cloud and GV_FIELD_ZSCALE in mesh.field_data:
            zscale = float(mesh[GV_FIELD_ZSCALE][0])
        else:
            zscale = ZLEVEL_SCALE

    if radius is None and cloud and GV_FIELD_RADIUS in mesh.field_data:
        radius = float(mesh[GV_FIELD_RADIUS][0])

    if transform_required:
        if level.ndim:
            try:
                level = np.broadcast_to(level, (mesh.n_points,))
            except ValueError:
                emsg = (
                    f"Cannot transform mesh, 'zlevel' with shape {level.shape} does "
                    f"not broadcast to its {mesh.n_points:,} points."
                )
                raise ValueError(emsg) from None

        # slice the mesh to break connectivity, but not for a point-cloud
        if slice_connectivity:
            if central_meridian:
                mesh.rotate_z(-central_meridian, inplace=True)
                rebased = set_central_meridian(tgt_crs, 0)
                # both helpers locate the same parameter, and refuse the same
                # non-degree prime meridian, so one that reads can be rewritten
                assert rebased is not None
                tgt_crs = rebased

            carry: str | None = None
            if not cloud:
                # the sliced_mesh is guaranteed to be a new instance, even if not
                # bisected, and a per-point zlevel travels through the slice as
                # point data, so a point the seam duplicates keeps its level. It
                # travels under a name no array of the caller's has, so only what
                # is added here is removed, and as floats, so a level the seam
                # interpolates is not rounded
                if level.ndim:
                    carry = _ZLEVEL
                    while carry in mesh.point_data:
                        carry = f"_{carry}"
                    mesh.point_data[carry] = level.astype(float)
                try:
                    sliced_mesh = slice_mesh(mesh, rtol=rtol, atol=atol)
                finally:
                    if carry is not None:
                        mesh.point_data.pop(carry, None)
            else:
                sliced_mesh = mesh.copy()

            if central_meridian:
                # undo rotation of original mesh
                mesh.rotate_z(central_meridian, inplace=True)

            if carry is not None:
                if carry not in sliced_mesh.point_data:
                    # slice_lines rebuilds the lines it splits without their point
                    # data, so the levels are lost (issue 2583)
                    emsg = (
                        "Cannot transform mesh, a per-point 'zlevel' cannot yet "
                        "follow lines sliced at the seam. Use a scalar 'zlevel'."
                    )
                    raise ValueError(emsg)
                level = np.asarray(sliced_mesh.point_data.pop(carry))

            mesh = sliced_mesh

        # now perform the CRS transformation
        if src_crs == WGS84:
            xyz = from_cartesian(mesh, closed_interval=True, rtol=rtol, atol=atol)
        else:
            xyz = mesh.points

        if cloud:
            # a cloud carries a z-level at each point, which zlevel adds to
            level = level + _carried_zlevels(mesh, xyz, src_crs)

        transformed = transform_points(
            src_crs=src_crs, tgt_crs=tgt_crs, xs=xyz[:, 0], ys=xyz[:, 1]
        )

        xs, ys = transformed[:, 0], transformed[:, 1]
        zs: float | NDArray[Any] = 0.0

        if not inplace and not slice_connectivity:
            mesh = mesh.copy(deep=True)

        if tgt_crs == WGS84:
            xs, ys, zs = to_cartesian(
                xs, ys, radius=radius, zlevel=level, zscale=zscale, stacked=False
            )

        # pyvista 0.49 annotates "pyvista_ndarray.__setitem__" to refuse the tuple
        # index it accepts at runtime, so the points are set through a cast
        points = cast("NDArray[Any]", mesh.points)
        points[:, 0] = xs
        points[:, 1] = ys

        # a planar target offsets z by the level, whereas on the sphere the level
        # is already in the radius that to_cartesian applied
        if tgt_crs != WGS84 and (np.any(level) or cloud):
            xmin, xmax, ymin, ymax, _, _ = mesh.bounds
            xdelta, ydelta = abs(xmax - xmin), abs(ymax - ymin)
            # TODO @bjlittle: Make this scale factor configurable at the API/module
            #                 level, as current strategy is slightly flawed in that
            #                 there isn't consistent scaling across all geometries
            #                 added to the render scene.
            delta = max(xdelta, ydelta) // 4
            zs = level * zscale * delta

        points[:, 2] = zs

        if cloud:
            _record_zlevels(mesh, level, tgt_crs)

        # TODO @bjlittle: Check whether to clean other field_data metadata.
        to_wkt(mesh, original_tgt_crs)

    return mesh


def transform_point(
    src_crs: CRSLike,
    tgt_crs: CRSLike,
    x: ArrayLike,
    y: ArrayLike,
    z: ArrayLike | None = None,
    *,
    trap: bool | None = True,
) -> NDArray[Any]:
    """Transform the spatial point from the source to the target CRS.

    Parameters
    ----------
    src_crs : CRSLike
        The source Coordinate Reference System (CRS) of the provided `x`,
        `y` and `z` spatial point. May be anything accepted by
        :meth:`pyproj.crs.CRS.from_user_input`.
    tgt_crs : CRSLike
        The target Coordinate Reference System (CRS) of the transform for
        the spatial point. May be anything accepted by
        :meth:`pyproj.crs.CRS.from_user_input`.
    x : ArrayLike
        The spatial point x-value, in canonical `src_crs` units, to be
        transformed from the `src_crs` to the `tgt_crs`. Must be a scalar
        or a single valued 1D array.
    y : ArrayLike
        The spatial point y-value, in canonical `src_crs` units, to be
        transformed from the `src_crs` to the `tgt_crs`. Must be a scalar
        or a single valued 1D array.
    z : ArrayLike, optional
        The spatial point z-value, in canonical `src_crs` units, to be
        transformed from the `src_crs` to the `tgt_crs`. Must be a scalar
        or a single valued 1D array.
    trap : bool, default=True
        Raise an exception if an error occurs during CRS transformation
        of the spatial point. Otherwise, ``inf`` will be returned for
        the erroneous point.

    Returns
    -------
    ndarray
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
    return result[0, :]


def transform_points(
    src_crs: CRSLike,
    tgt_crs: CRSLike,
    xs: ArrayLike,
    ys: ArrayLike,
    zs: ArrayLike | None = None,
    *,
    trap: bool | None = True,
) -> NDArray[Any]:
    """Transform the spatial points from the source to the target CRS.

    Parameters
    ----------
    src_crs : CRSLike
        The source Coordinate Reference System (CRS) of the provided `xs`,
        `ys` and `zs` spatial points. May be anything accepted by
        :meth:`pyproj.crs.CRS.from_user_input`.
    tgt_crs : CRSLike
        The target Coordinate Reference System (CRS) of the transform for
        the spatial points. May be anything accepted by
        :meth:`pyproj.crs.CRS.from_user_input`.
    xs : ArrayLike
        The spatial points x-values, in canonical `src_crs` units, to be
        transformed from the `src_crs` to the `tgt_crs`. May be scalar,
        1D or 2D.
    ys : ArrayLike
        The spatial points y-values, in canonical `src_crs` units, to be
        transformed from the `src_crs` to the `tgt_crs`. May be scalar,
        1D or 2D.
    zs : ArrayLike, optional
        The spatial points z-values, in canonical `src_crs` units, to be
        transformed from the `src_crs` to the `tgt_crs`. May be scalar,
        1D or 2D.
    trap : bool, default=True
        Raise an exception if an error occurs during CRS transformation
        of the spatial points. Otherwise, ``inf`` will be returned for
        erroneous points.

    Returns
    -------
    ndarray
        The transformed spatial points in the canonical units of the target
        CRS. The shape of the result will either be ``(1, 3)``, ``(M, 3)``
        or ``(M, N, 3)`` depending on whether the provided spatial points
        were scalar, 1D or 2D, respectively.

    Notes
    -----
    .. versionadded:: 0.4.0

    """
    xs = np.atleast_1d(xs)
    ys = np.atleast_1d(ys)

    if zs is not None:
        zs = np.atleast_1d(zs)

    # sanity check the crs's
    src_crs = pyproj.CRS.from_user_input(src_crs)
    tgt_crs = pyproj.CRS.from_user_input(tgt_crs)

    # sanity check spatial arrays
    if (xndim := xs.ndim) > 2 or (yndim := ys.ndim) > 2:
        emsg = "Cannot transform points, 'xs' and 'ys' must be 1D or 2D only."
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
            emsg = "Cannot transform points, 'zs' must be 1D or 2D only."
            raise ValueError(emsg)

        if zndim != 1:
            zs = zs.flatten()

        if zs.size != xs.size:
            emsg = (
                "Cannot transform points, 'xs' and 'zs' require same length "
                f"got {xs.size:,} and {zs.size:,} respectively."
            )
            raise ValueError(emsg)

    def combine(
        xs: ArrayLike, ys: ArrayLike, zs: ArrayLike | None = None
    ) -> NDArray[Any]:
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
        ndarray
            The (N, 3) array combined from `xs`, `ys`, and `zs`.

        Notes
        -----
        .. versionadded:: 0.4.0

        """
        # ensure to promote unpacked scalars
        xs = np.atleast_1d(xs)
        ys = np.atleast_1d(ys)
        zs = np.zeros_like(xs) if zs is None else np.atleast_1d(zs)

        assert xs.shape == ys.shape == zs.shape, (
            "Cannot combine points, non-uniform shapes."
        )

        if tgt_crs == WGS84:
            # ensure longitudes (degrees) are in half-closed interval [-180, 180)
            xs = wrap(xs)

            # reduce any singularity points at the poles to a common longitude
            poles = np.isclose(np.abs(ys), 90)
            if np.any(poles):
                xs[poles] = 0

        return np.vstack([xs, ys, zs]).T

    if src_crs == tgt_crs:
        result = combine(xs, ys, zs)
    else:
        transformer = pyproj.Transformer.from_crs(src_crs, tgt_crs, always_xy=True)
        if xs.size == 1:
            # unpack to avoid "conversion of an array with ndim > 0 to a scalar"
            # deprecation (numpy 1.25)
            xs, ys = xs[0], ys[0]
            if zs is not None:
                zs = zs[0]
        if zs is None:
            txs, tys = transformer.transform(xs, ys, errcheck=bool(trap))
            tzs = None
        else:
            txs, tys, tzs = transformer.transform(xs, ys, zs, errcheck=bool(trap))

        result = combine(txs, tys, tzs)

    if xndim == 2:
        shape.append(3)
        result = result.reshape(tuple(shape))

    return result


def _carried_zlevels(
    mesh: pv.PolyData, xyz: NDArray[Any], src_crs: pyproj.CRS
) -> NDArray[Any]:
    """Determine the z-level each point of a point cloud carries.

    On the sphere the z-level of a point is encoded in its radius, which
    :func:`geovista.common.from_cartesian` decodes. In a planar CRS it is read
    from the :data:`geovista.common.GV_POINT_ZLEVEL` point array, recorded by the
    transform that put the cloud there, and is zero where that array is absent.

    Parameters
    ----------
    mesh : :class:`~pyvista.PolyData`
        The point cloud, in its source CRS.
    xyz : :class:`~numpy.ndarray`
        The points of the cloud, as decoded by
        :func:`geovista.common.from_cartesian` on the sphere, or as they are in a
        planar CRS.
    src_crs : :class:`~pyproj.crs.CRS`
        The source CRS of the point cloud.

    Returns
    -------
    :class:`~numpy.ndarray`
        The z-level of each point.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if src_crs == WGS84:
        return np.asarray(xyz[:, 2])

    if GV_POINT_ZLEVEL in mesh.point_data:
        return np.asarray(mesh.point_data[GV_POINT_ZLEVEL])

    return np.zeros(mesh.n_points)


def _record_zlevels(
    mesh: pv.PolyData, levels: NDArray[Any], tgt_crs: pyproj.CRS
) -> None:
    """Record or drop the z-levels of a point cloud, for its target CRS.

    In a planar CRS the z-levels are recorded in the
    :data:`geovista.common.GV_POINT_ZLEVEL` point array, for the next transform
    to read. On the sphere the radius of each point holds its z-level, so the
    array is dropped.

    Parameters
    ----------
    mesh : :class:`~pyvista.PolyData`
        The point cloud, in its target CRS.
    levels : :class:`~numpy.ndarray`
        The z-level of each point, or one z-level for them all.
    tgt_crs : :class:`~pyproj.crs.CRS`
        The target CRS of the point cloud.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if tgt_crs == WGS84:
        mesh.point_data.pop(GV_POINT_ZLEVEL, None)
    else:
        # set as an array rather than by item, which would make the levels the
        # active scalars of a cloud that has none
        mesh.point_data.set_array(
            np.broadcast_to(levels, (mesh.n_points,)).astype(float), GV_POINT_ZLEVEL
        )
