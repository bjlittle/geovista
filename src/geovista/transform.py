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
import math
from typing import TYPE_CHECKING, Any, cast
import warnings

import lazy_loader as lazy

from .common import (
    GV_FIELD_ZSCALE,
    GV_POINT_ZLEVEL,
    ZLEVEL_SCALE,
    _retired,
    _to_cartesian,
    distance,
    from_cartesian,
    point_cloud,
    sanitize_legacy,
    wrap,
)
from .crs import (
    WGS84,
    CRSLike,
    _prime_meridian,
    from_wkt,
    get_central_meridian,
    planar,
    set_central_meridian,
    to_wkt,
)
from .globe import Globe, _resolve

if TYPE_CHECKING:
    from collections.abc import Callable

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

#: The name of the field array that marks a mesh on the sphere whose points have
#: been moved onto the datum of the target CRS, so that it is not moved twice.
_DATUM = "gvTransformDatum"

#: The bounds of an area of use for the whole globe, in degrees.
_GLOBE: tuple[float, float, float, float] = (-180.0, -90.0, 180.0, 90.0)

#: The tolerance, in degrees, within which a point counts as on an edge of an area of
#: use, so that rounding does not put it outside.
_EDGE = 1e-9


def transform_mesh(
    mesh: pv.PolyData,
    /,
    tgt_crs: CRSLike,
    *,
    slice_connectivity: bool | None = True,
    globe: Globe | None = None,
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
    globe : :class:`~geovista.globe.Globe`, optional
        The globe to place the mesh on, at its render radius, which the mesh
        transformed records. Defaults to the globe the `mesh` records, else
        ``Globe()``.
    zlevel : int or ArrayLike, default=0
        The z-axis level. Used in combination with the `zscale` to offset the
        render radius/vertical by a proportional amount e.g.,
        ``render_radius * zlevel * zscale``. In a planar CRS the offset is
        ``zlevel * zscale`` times the radius of the Earth in the units of that CRS,
        the same proportion as on the sphere.
        If `zlevel` is not a scalar, then it must broadcast to the shape
        ``(mesh.n_points,)``. For a point cloud, `zlevel` adds to
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
    carried in the :data:`geovista.common.GV_POINT_ZLEVEL` point array. The cloud
    also carries the `globe` and `zscale` that encode them, so a value given here
    becomes its own.

    A mesh already in the target CRS is not transformed, so no point moves and
    its globe is unchanged. Use :func:`geovista.core.resize` to change its globe.

    .. versionadded:: 0.3.0

    """
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
    cloud = point_cloud(mesh)

    if zscale is None:
        if cloud and GV_FIELD_ZSCALE in mesh.field_data:
            zscale = float(mesh[GV_FIELD_ZSCALE][0])
        else:
            zscale = ZLEVEL_SCALE

    # the globe given, else the one the mesh records, else the default
    globe = (Globe.from_mesh(mesh) or Globe()) if globe is None else _resolve(globe)
    radius = globe.render_radius

    if not transform_required:
        # a mesh returned carries only current fields, so a retired one is
        # cleaned from a copy, unless asked in place
        if _retired(mesh):
            if not inplace:
                mesh = mesh.copy()
            sanitize_legacy(mesh)
        return mesh

    if transform_required:
        level = _point_levels(mesh, zlevel)

        if src_crs == WGS84:
            # the datum operation is taken where each point is, before the mesh is
            # rotated to the central meridian or cut, see issue #2714. A cut leaves
            # the mesh given as it was, so then it is moved as a copy
            mesh = _apply_datum(
                mesh, tgt_crs, inplace=bool(inplace) and not slice_connectivity
            )

        # points moved onto the target's datum are only projected from here
        projection_crs = tgt_crs.geodetic_crs if _DATUM in mesh.field_data else None

        # slice the mesh to break connectivity, but not for a point-cloud
        if slice_connectivity:
            mesh, tgt_crs, level = _slice_seam(
                mesh, tgt_crs, level=level, rtol=rtol, atol=atol
            )

        # now perform the CRS transformation
        if src_crs == WGS84:
            xyz = from_cartesian(mesh, closed_interval=True, rtol=rtol, atol=atol)
        else:
            xyz = mesh.points

        if cloud:
            # a cloud carries a z-level at each point, which zlevel adds to
            level = level + _carried_zlevels(mesh, xyz, src_crs)

        src_xs, src_ys = xyz[:, 0], xyz[:, 1]

        if projection_crs is not None:
            # the sphere is in degrees east of Greenwich, whatever the datum, so
            # the points are given in the units of the target's geographic CRS
            src_xs, src_ys = _from_greenwich(projection_crs, src_xs, src_ys)

        transformed = transform_points(
            src_crs=projection_crs or src_crs, tgt_crs=tgt_crs, xs=src_xs, ys=src_ys
        )

        xs, ys = transformed[:, 0], transformed[:, 1]
        zs: float | NDArray[Any] = 0.0

        if not inplace and not slice_connectivity:
            mesh = mesh.copy(deep=True)

        if tgt_crs == WGS84:
            xs, ys, zs = _to_cartesian(
                xs, ys, radius=radius, zlevel=level, zscale=zscale, stacked=False
            )

        # pyvista 0.49 annotates "pyvista_ndarray.__setitem__" to refuse the tuple
        # index it accepts at runtime, so the points are set through a cast
        points = cast("NDArray[Any]", mesh.points)
        points[:, 0] = xs
        points[:, 1] = ys

        # zlevel spec §3.1 -- a planar target offsets z by the level times the
        # radius of the Earth in its own units, whereas on the sphere the level
        # is already in the radius that to_cartesian applied
        if tgt_crs != WGS84 and (np.any(level) or cloud):
            zs = level * zscale * _earth_radius(tgt_crs)

        points[:, 2] = zs

        if cloud:
            _record_zlevels(mesh, level, tgt_crs, zscale=zscale)

        # TODO @bjlittle: Check whether to clean other field_data metadata.
        mesh.field_data.pop(_DATUM, None)
        to_wkt(mesh, original_tgt_crs)
        # the globe the mesh is placed on, on a map too, so that it returns to it
        globe.to_mesh(mesh)
        sanitize_legacy(mesh)

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
        transformer = _transformer(src_crs, tgt_crs, xs, ys)
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


def _transformer(
    src_crs: pyproj.CRS, tgt_crs: pyproj.CRS, xs: NDArray[Any], ys: NDArray[Any]
) -> pyproj.Transformer:
    """Choose the one operation that transforms every point between two CRSs.

    Between CRSs on different datums, PROJ chooses an operation for each point,
    the best whose area of use holds it, and so neighbouring points can take
    different ones. Past the edge of a datum grid that falls back to no datum
    shift at all, a step of 129 m on the British National Grid, so one operation is
    chosen for every point instead. See :issue:`2714`.

    It is the most accurate operation whose area of use covers every point. Where
    none does, it is the most accurate operation that can transform every point,
    with a warning. PROJ's ballpark operation, which applies no datum shift, is
    used only when there is no other. An operation whose grid is not installed, as
    none is with pyproj's wheels, is passed over, as PROJ itself passes it over.

    Parameters
    ----------
    src_crs : :class:`~pyproj.crs.CRS`
        The source CRS of the points.
    tgt_crs : :class:`~pyproj.crs.CRS`
        The target CRS of the points.
    xs : :class:`~numpy.ndarray`
        The x-values of the points, in canonical `src_crs` units.
    ys : :class:`~numpy.ndarray`
        The y-values of the points, in canonical `src_crs` units.

    Returns
    -------
    :class:`~pyproj.transformer.Transformer`
        The transformer of the chosen operation, with the axis order x then y.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    candidates = _datum_operations(src_crs, tgt_crs)

    if not candidates:
        # no datum to change, or nothing but the ballpark operation to change it
        return pyproj.Transformer.from_crs(src_crs, tgt_crs, always_xy=True)

    finite = np.isfinite(xs) & np.isfinite(ys)
    xs, ys = xs[finite], ys[finite]
    lonlats: tuple[NDArray[Any], NDArray[Any]] | None = None

    for candidate in candidates:
        bounds = _bounds(candidate)
        # an operation for the whole globe covers any points, unlocated
        if bounds == _GLOBE:
            return candidate
        if lonlats is None:
            lonlats = _lonlats(src_crs, xs, ys)
        if _covers(bounds, *lonlats):
            return candidate

    for candidate in candidates:
        try:
            candidate.transform(xs, ys, errcheck=True)
        except pyproj.exceptions.ProjError:
            # a grid-based operation refuses a point beyond its grid
            continue
        accuracy = (
            f"accurate to {candidate.accuracy:g} m"
            if candidate.accuracy >= 0
            else "of unknown accuracy"
        )
        wmsg = (
            f"geovista transformed points from {src_crs.name!r} to "
            f"{tgt_crs.name!r} with {candidate.description!r}, {accuracy}, whose "
            "area of use does not cover every point, as no operation's does."
        )
        warnings.warn(wmsg, stacklevel=3)
        return candidate

    # no operation takes every point, so the most accurate refuses those it cannot
    return candidates[0]


def _apply_datum(
    mesh: pv.PolyData, tgt_crs: pyproj.CRS, *, inplace: bool = False
) -> pv.PolyData:
    """Move a mesh on the sphere onto the datum of the target CRS.

    A datum operation must be taken where each point is. Rotating a mesh to the
    target's central meridian first, as the seam slicing does, would take each
    shift from the wrong place, so the points are moved first, and only projected
    afterwards. See :issue:`2714`.

    Parameters
    ----------
    mesh : :class:`~pyvista.PolyData`
        The mesh, on the sphere of WGS84.
    tgt_crs : :class:`~pyproj.crs.CRS`
        The target CRS.
    inplace : bool, default=False
        Move the points of the `mesh` itself, rather than those of a copy.

    Returns
    -------
    :class:`~pyvista.PolyData`
        The mesh as it is when there is no datum to change, or it has been moved
        already. Otherwise the mesh, or a copy, with each point moved onto the datum
        of the target at the same radius, in degrees east of Greenwich, and marked
        as moved.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    geographic = tgt_crs.geodetic_crs

    if geographic is None or _DATUM in mesh.field_data:
        return mesh

    if not any(_moves(operation) for operation in _datum_operations(WGS84, geographic)):
        # no datum to change, or a null transformation between two of its names
        return mesh

    lonlat = from_cartesian(mesh)
    moved = transform_points(
        src_crs=WGS84, tgt_crs=geographic, xs=lonlat[:, 0], ys=lonlat[:, 1]
    )
    # a geographic CRS may measure in another unit, from another meridian, such as
    # NTF (Paris) in grads east of Paris, but the sphere is in degrees from Greenwich
    lons, lats = _to_greenwich(geographic, moved[:, 0], moved[:, 1])
    radius = np.asarray(distance(mesh, mean=False))

    result = mesh if inplace else mesh.copy()
    # pyvista 0.49 annotates "pyvista_ndarray.__setitem__" to refuse the slice
    # index it accepts at runtime, so the points are set through a cast
    points = cast("NDArray[Any]", result.points)
    # each point keeps its own radius, which carries any z-level it was lifted by
    points[:] = _to_cartesian(lons, lats, radius=1.0) * radius[:, np.newaxis]
    result.field_data[_DATUM] = np.array([1])

    return result


def _moves(operation: pyproj.Transformer) -> bool:
    """Determine whether a datum operation moves a point at all.

    Parameters
    ----------
    operation : :class:`~pyproj.transformer.Transformer`
        A datum operation between two geographic CRSs, with the axis order
        longitude then latitude.

    Returns
    -------
    bool
        Whether the point at the centre of the operation's area of use moves. A null
        transformation, between two names of one datum, moves no point.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    west, south, east, north = _bounds(operation)

    if west > east:
        # the area crosses the antimeridian
        east += 360.0

    lon, lat = float(wrap((west + east) / 2)[0]), (south + north) / 2
    x, y = operation.transform(lon, lat)
    return not (
        np.isclose(x, lon, rtol=0, atol=1e-12)
        and np.isclose(y, lat, rtol=0, atol=1e-12)
    )


def _datum_operations(
    src_crs: pyproj.CRS, tgt_crs: pyproj.CRS
) -> list[pyproj.Transformer]:
    """List the operations PROJ offers between CRSs on different datums.

    Parameters
    ----------
    src_crs : :class:`~pyproj.crs.CRS`
        The source CRS.
    tgt_crs : :class:`~pyproj.crs.CRS`
        The target CRS.

    Returns
    -------
    list of :class:`~pyproj.transformer.Transformer`
        The available operations, most accurate first, apart from PROJ's ballpark
        operation. An operation whose grid is not installed is unavailable. Empty
        when the CRSs share a datum, as a projection alone needs no choice, or when
        the ballpark operation is the only one.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    src_datum, tgt_datum = src_crs.datum, tgt_crs.datum

    if src_datum is None or tgt_datum is None or src_datum == tgt_datum:
        return []

    with warnings.catch_warnings():
        # PROJ warns when the most accurate operation's grid is not installed, as
        # none is with pyproj's wheels, but the most accurate of those available is
        # taken instead, as PROJ itself would take it
        warnings.filterwarnings(
            "ignore",
            message="Best transformation is not available",
            category=UserWarning,
        )
        group = pyproj.transformer.TransformerGroup(
            src_crs, tgt_crs, always_xy=True, allow_ballpark=False
        )

    operations = group.transformers

    # one datum can go by two names, such as WGS84 and EPSG:4326's ensemble of it,
    # and then PROJ offers an operation of conversions alone, which needs no choice
    if any(not _transforms(operation) for operation in operations):
        return []

    return sorted(operations, key=_accuracy)


def _transforms(operation: pyproj.Transformer) -> bool:
    """Determine whether an operation changes datum.

    Parameters
    ----------
    operation : :class:`~pyproj.transformer.Transformer`
        The operation.

    Returns
    -------
    bool
        Whether it, or any of its steps, is a transformation between datums, rather
        than a conversion, such as a projection, within one.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if steps := operation.operations:
        return any(step.type_name == "Transformation" for step in steps)

    return bool(operation.to_json_dict().get("type") == "Transformation")


def _bounds(operation: pyproj.Transformer) -> tuple[float, float, float, float]:
    """Find the bounds of an operation's area of use.

    Parameters
    ----------
    operation : :class:`~pyproj.transformer.Transformer`
        The operation.

    Returns
    -------
    tuple of float
        The west, south, east and north bounds of its area of use, in degrees, or
        those of the whole globe when PROJ does not know its area of use.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    try:
        west, south, east, north = operation.area_of_use.bounds
    except AttributeError:
        # pyproj annotates the area of use as always known, but PROJ leaves some
        # unknown, such as that of an operation from "+proj=eqc"
        return _GLOBE
    return west, south, east, north


def _accuracy(transformer: pyproj.Transformer) -> float:
    """Rank an operation by its accuracy.

    Parameters
    ----------
    transformer : :class:`~pyproj.transformer.Transformer`
        The operation.

    Returns
    -------
    float
        Its accuracy in metres, or infinity when it is unknown, which PROJ reports
        as -1, so that an unknown accuracy ranks last.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    return transformer.accuracy if transformer.accuracy >= 0 else math.inf


def _lonlats(
    crs: pyproj.CRS, xs: NDArray[Any], ys: NDArray[Any]
) -> tuple[NDArray[Any], NDArray[Any]]:
    """Find the longitudes and latitudes of points, to test an area of use.

    Parameters
    ----------
    crs : :class:`~pyproj.crs.CRS`
        The CRS of the points.
    xs : :class:`~numpy.ndarray`
        The x-values of the points, in canonical `crs` units.
    ys : :class:`~numpy.ndarray`
        The y-values of the points, in canonical `crs` units.

    Returns
    -------
    tuple of :class:`~numpy.ndarray`
        The longitudes and latitudes of the points, in degrees east of Greenwich, on
        the datum of the `crs`. An area of use is given on WGS84, but the difference
        between datums is far smaller than the precision of an area of use.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    geographic = crs.geodetic_crs or crs

    if not crs.is_geographic:
        transformer = pyproj.Transformer.from_crs(crs, geographic, always_xy=True)
        xs, ys = (np.asarray(values) for values in transformer.transform(xs, ys))

    # an area of use is in degrees east of Greenwich, which a geographic CRS need
    # not be, such as NTF (Paris) in grads east of Paris
    return _to_greenwich(geographic, xs, ys)


def _angles(crs: pyproj.CRS) -> tuple[float, float, float]:
    """Find how a geographic CRS measures its longitudes and latitudes.

    Parameters
    ----------
    crs : :class:`~pyproj.crs.CRS`
        The geographic CRS.

    Returns
    -------
    tuple of float
        The degrees east of Greenwich of its prime meridian, and the degrees in a
        unit of its longitude and of its latitude, as :mod:`pyproj` gives and takes
        them. Most are in degrees east of Greenwich, but not all, such as NTF
        (Paris), in grads east of Paris.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    # there is no prime meridian only where its unit is not angular, which none is
    prime_meridian = _prime_meridian(crs, crs.to_json_dict()) or 0.0
    degrees = {"east": 1.0, "north": 1.0}

    for axis in crs.axis_info:
        factor = axis.unit_conversion_factor
        # pyproj gives and takes the coordinates of an axis declared in radians in
        # degrees, as _earth_radius allows for, and those of an axis in any other
        # angular unit, such as grads, in that unit
        radians = factor == 1.0
        if axis.direction in degrees and axis.unit_name != "degree" and not radians:
            degrees[axis.direction] = math.degrees(factor)

    return prime_meridian, degrees["east"], degrees["north"]


def _to_greenwich(
    crs: pyproj.CRS, lons: NDArray[Any], lats: NDArray[Any]
) -> tuple[NDArray[Any], NDArray[Any]]:
    """Convert the longitudes and latitudes of a geographic CRS to degrees.

    Parameters
    ----------
    crs : :class:`~pyproj.crs.CRS`
        The geographic CRS.
    lons : :class:`~numpy.ndarray`
        The longitudes, in the unit of the `crs`, east of its prime meridian.
    lats : :class:`~numpy.ndarray`
        The latitudes, in the unit of the `crs`.

    Returns
    -------
    tuple of :class:`~numpy.ndarray`
        The longitudes, in degrees east of Greenwich, and the latitudes, in degrees.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    prime_meridian, east, north = _angles(crs)
    return lons * east + prime_meridian, lats * north


def _from_greenwich(
    crs: pyproj.CRS, lons: NDArray[Any], lats: NDArray[Any]
) -> tuple[NDArray[Any], NDArray[Any]]:
    """Convert longitudes and latitudes in degrees to those of a geographic CRS.

    Parameters
    ----------
    crs : :class:`~pyproj.crs.CRS`
        The geographic CRS.
    lons : :class:`~numpy.ndarray`
        The longitudes, in degrees east of Greenwich.
    lats : :class:`~numpy.ndarray`
        The latitudes, in degrees.

    Returns
    -------
    tuple of :class:`~numpy.ndarray`
        The longitudes, in the unit of the `crs`, east of its prime meridian, and the
        latitudes, in the unit of the `crs`.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    prime_meridian, east, north = _angles(crs)
    return (lons - prime_meridian) / east, lats / north


def _covers(
    bounds: tuple[float, float, float, float], lons: NDArray[Any], lats: NDArray[Any]
) -> bool:
    """Determine whether an area of use holds every point.

    Parameters
    ----------
    bounds : tuple of float
        The west, south, east and north bounds of an operation's area of use, in
        degrees.
    lons : :class:`~numpy.ndarray`
        The longitudes of the points, in degrees.
    lats : :class:`~numpy.ndarray`
        The latitudes of the points, in degrees.

    Returns
    -------
    bool
        Whether every point lies within the area of use.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    lons = wrap(lons)
    # a point on an edge, give or take rounding, lies within it
    west, south, east, north = (
        bounds[0] - _EDGE,
        bounds[1] - _EDGE,
        bounds[2] + _EDGE,
        bounds[3] + _EDGE,
    )

    # an area of use that crosses the antimeridian has its west edge east of its east
    if west <= east:
        inside = (lons >= west) & (lons <= east)
    else:
        inside = (lons >= west) | (lons <= east)

    inside &= (lats >= south) & (lats <= north)
    return bool(np.all(inside))


def _point_levels(
    mesh: pv.PolyData,
    zlevel: float | ArrayLike | None,
    *,
    action: str = "transform",
) -> NDArray[Any]:
    """Determine the z-level of a mesh, as a scalar or one for each of its points.

    Parameters
    ----------
    mesh : :class:`~pyvista.PolyData`
        The mesh the z-level is given for.
    zlevel : float or ArrayLike, optional
        The z-level, either a scalar or an array that broadcasts to the points of
        the `mesh`. Defaults to ``0``.
    action : str, default="transform"
        What is done to the `mesh`, for the error message.

    Returns
    -------
    :class:`~numpy.ndarray`
        The z-level as a 0-d array, or as one for each point of the `mesh`.

    Raises
    ------
    ValueError
        If an array `zlevel` does not broadcast to the points of the `mesh`.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    level = np.asanyarray(0 if zlevel is None else zlevel)

    if level.ndim:
        try:
            level = np.broadcast_to(level, (mesh.n_points,))
        except ValueError:
            emsg = (
                f"Cannot {action} mesh, 'zlevel' with shape {level.shape} does "
                f"not broadcast to its {mesh.n_points:,} points."
            )
            raise ValueError(emsg) from None

    return level


def _carry_levels(
    mesh: pv.PolyData,
    level: NDArray[Any],
    cut: Callable[[pv.PolyData], pv.PolyData],
) -> tuple[pv.PolyData, NDArray[Any]]:
    """Cut a mesh, carrying a z-level at each point through the cut.

    A per-point z-level travels through the cut as point data, so a point the
    cut duplicates keeps its level, and a point it interpolates takes a level
    between those of its neighbours. It travels under a name no array of the
    caller's has, so only what is added here is removed, and as floats, so an
    interpolated level is not rounded.

    Parameters
    ----------
    mesh : :class:`~pyvista.PolyData`
        The mesh to cut, which is left as it was.
    level : :class:`~numpy.ndarray`
        The z-level, as a 0-d array or as one for each point of the `mesh`, see
        :func:`_point_levels`.
    cut : callable
        Cuts the mesh it is given, returning the cut mesh.

    Returns
    -------
    tuple of :class:`~pyvista.PolyData` and :class:`~numpy.ndarray`
        The cut mesh, and the z-level, for each point of the cut mesh if one was
        given for each point of the `mesh`.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    carry: str | None = None

    if level.ndim:
        carry = _ZLEVEL
        while carry in mesh.point_data:
            carry = f"_{carry}"
        mesh.point_data[carry] = level.astype(float)

    try:
        result = cut(mesh)
        if carry is not None:
            # read before it is removed, in case the cut returned the mesh itself
            level = np.array(result.point_data[carry])
            result.point_data.pop(carry, None)
    finally:
        if carry is not None:
            mesh.point_data.pop(carry, None)

    return result, level


def _slice_seam(
    mesh: pv.PolyData,
    tgt_crs: pyproj.CRS,
    /,
    *,
    level: NDArray[Any],
    rtol: float | None = None,
    atol: float | None = None,
) -> tuple[pv.PolyData, pyproj.CRS, NDArray[Any]]:
    """Cut a mesh along the seam of a CRS, carrying a z-level at each point.

    The mesh is rotated so that the central meridian of the CRS is at zero, cut
    along the antimeridian, then rotated back, so the mesh given is left as it
    was. A point cloud has no connectivity to break, so it is copied instead.

    Parameters
    ----------
    mesh : :class:`~pyvista.PolyData`
        The mesh to cut, on the sphere.
    tgt_crs : :class:`~pyproj.crs.CRS`
        The CRS whose seam the `mesh` is cut along.
    level : :class:`~numpy.ndarray`
        The z-level, as a 0-d array or as one for each point of the `mesh`, see
        :func:`_point_levels`.
    rtol : float, optional
        The relative tolerance for longitudes close to the 'wrap meridian' -
        see :func:`geovista.common.wrap` for more.
    atol : float, optional
        The absolute tolerance for longitudes close to the 'wrap meridian' -
        see :func:`geovista.common.wrap` for more.

    Returns
    -------
    tuple of :class:`~pyvista.PolyData`, :class:`~pyproj.crs.CRS` and \
    :class:`~numpy.ndarray`
        The cut mesh, a new instance even if not bisected, still rotated; the
        CRS with its central meridian at zero, to transform the cut mesh to; and
        the z-level, for each point of the cut mesh if one was given for each
        point of the `mesh`.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    # core imports this module through search, so it is imported here
    from .core import slice_mesh  # noqa: PLC0415

    central_meridian = get_central_meridian(tgt_crs) or 0

    if central_meridian:
        mesh.rotate_z(-central_meridian, inplace=True)
        rebased = set_central_meridian(tgt_crs, 0)
        # both helpers locate the same parameter, and refuse the same
        # non-degree prime meridian, so one that reads can be rewritten
        assert rebased is not None
        tgt_crs = rebased

    if not point_cloud(mesh):
        sliced_mesh, level = _carry_levels(
            mesh, level, lambda mesh: slice_mesh(mesh, rtol=rtol, atol=atol)
        )
    else:
        sliced_mesh = mesh.copy()

    if central_meridian:
        # undo rotation of original mesh
        mesh.rotate_z(central_meridian, inplace=True)

    return sliced_mesh, tgt_crs, level


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
    mesh: pv.PolyData,
    levels: NDArray[Any],
    tgt_crs: pyproj.CRS,
    *,
    zscale: float,
) -> None:
    """Record the z-levels of a point cloud, and how they are encoded, for its CRS.

    In a planar CRS the z-levels are recorded in the
    :data:`geovista.common.GV_POINT_ZLEVEL` point array, for the next transform
    to read. On the sphere the radius of each point holds its z-level, so the
    array is dropped. The cloud carries the `zscale` that encoded its levels, since
    later transforms decode the levels with it and default to it, as they do to the
    globe that :func:`transform_mesh` records.

    Parameters
    ----------
    mesh : :class:`~pyvista.PolyData`
        The point cloud, in its target CRS.
    levels : :class:`~numpy.ndarray`
        The z-level of each point, or one z-level for them all.
    tgt_crs : :class:`~pyproj.crs.CRS`
        The target CRS of the point cloud.
    zscale : float
        The proportional multiplier the transform encoded the levels with.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    mesh.field_data[GV_FIELD_ZSCALE] = np.array([float(zscale)])

    if tgt_crs == WGS84:
        mesh.point_data.pop(GV_POINT_ZLEVEL, None)
    else:
        # set as an array rather than by item, which would make the levels the
        # active scalars of a cloud that has none
        mesh.point_data.set_array(
            np.broadcast_to(levels, (mesh.n_points,)).astype(float), GV_POINT_ZLEVEL
        )


def _earth_radius(crs: pyproj.CRS) -> float:
    """Determine the radius of the Earth, in the units of a CRS.

    A planar CRS offsets a z-level by this length, so that a level is the same
    proportion of the Earth's radius as it is on the sphere. For a geographic CRS
    the radius is one radian, expressed in the angular unit its coordinates come
    back in, which for a CRS declared in radians is degrees.

    Parameters
    ----------
    crs : :class:`~pyproj.crs.CRS`
        The planar CRS.

    Returns
    -------
    float
        The radius of the Earth, in the unit of the first axis of the CRS.

    Raises
    ------
    ValueError
        If the CRS has no ellipsoid, or its first axis has no unit.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    ellipsoid = crs.ellipsoid
    factor = crs.axis_info[0].unit_conversion_factor if crs.axis_info else None

    if ellipsoid is None or not factor:
        emsg = (
            f"Cannot determine the radius of the Earth in the units of {crs.name!r}, "
            "which has no ellipsoid or no axis unit."
        )
        raise ValueError(emsg)

    radius: float
    if crs.is_geographic:
        # pyproj returns the coordinates of a geographic CRS declared in radians
        # in degrees, and those of any other in its own angular unit
        radius = math.degrees(1.0) if factor == 1.0 else 1.0 / factor
    else:
        radius = ellipsoid.semi_major_metre / factor
    return radius
