"""Coordinate reference system (CRS) transformation functions.

Notes
-----
.. versionadded:: 0.3.0

"""
from __future__ import annotations

from copy import deepcopy

from numpy.typing import ArrayLike
from pyproj import CRS, Transformer
import pyvista as pv

from .common import GV_FIELD_ZSCALE, ZLEVEL_SCALE, from_cartesian, point_cloud
from .core import slice_mesh
from .crs import WGS84, from_wkt, get_central_meridian, set_central_meridian, to_wkt

__all__ = [
    "transform_mesh",
]


def transform_mesh(
    mesh: pv.PolyData,
    tgt_crs: CRS,
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
    tgt_crs : CRS
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
    src_crs = from_wkt(mesh)

    if src_crs is None:
        emsg = "Cannot transform mesh, no coordinate reference system (CRS) attached."
        raise ValueError(emsg)

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
        if slice_connectivity and not cloud:
            if central_meridian:
                mesh.rotate_z(-central_meridian, inplace=True)
                tgt_crs = set_central_meridian(tgt_crs, 0)

            # the sliced_mesh is guaranteed to be a new instance, even if not bisected
            sliced_mesh = slice_mesh(mesh, rtol=rtol, atol=atol)

            if central_meridian:
                # undo rotation of original mesh
                mesh.rotate_z(central_meridian, inplace=True)

            mesh = sliced_mesh

        # now perform the CRS transformation
        if src_crs == WGS84:
            xyz = from_cartesian(mesh, closed_interval=True, rtol=rtol, atol=atol)
        else:
            xyz = mesh.points

        transformer = Transformer.from_crs(src_crs, tgt_crs, always_xy=True)
        xs, ys = transformer.transform(xyz[:, 0], xyz[:, 1], errcheck=True)
        zs = 0

        if not inplace and (cloud or not slice_connectivity):
            mesh = mesh.copy(deep=True)

        mesh.points[:, 0] = xs
        mesh.points[:, 1] = ys

        if zlevel or cloud:
            xmin, xmax, ymin, ymax, _, _ = mesh.bounds
            xdelta, ydelta = abs(xmax - xmin), abs(ymax - ymin)
            # TODO: make this scale factor configurable at the API/module level
            delta = min(xdelta, ydelta) // 4

            if cloud:
                zlevel += xyz[:, 2]

            zs = zlevel * zscale * delta

        mesh.points[:, 2] = zs

        # TODO: check whether to clean other field_data metadata
        to_wkt(mesh, original_tgt_crs)

    return mesh
