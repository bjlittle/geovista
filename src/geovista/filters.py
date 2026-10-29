# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Filters to analyse, transform and process geolocated meshes.

These filters leverage and build upon the rich, powerful ecosystem of the
`Visualization Toolkit (VTK) <https://vtk.org/>`_.

Notes
-----
.. versionadded:: 0.1.0

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import lazy_loader as lazy

from .common import (
    GV_CELL_IDS,
    GV_POINT_IDS,
    GV_REMESH_POINT_IDS,
    REMESH_JOIN,
    REMESH_SEAM,
    _current,
    distance,
    from_cartesian,
    sanitize_vtk,
    triangulated,
    wrap,
)
from .common import cast_UnstructuredGrid_to_PolyData as cast

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray
    import pyvista as pv

    # this is a type alias
    Remesh = tuple[pv.PolyData, pv.PolyData, pv.PolyData]

# lazy import third-party dependencies
np = lazy.load("numpy")
pv = lazy.load("pyvista")

__all__ = [
    "REMESH_SEAM_EAST",
    "VTK_BAD_TRIANGLE_MASK",
    "VTK_BOUNDARY_MASK",
    "VTK_FREE_EDGE_MASK",
    "remesh",
]

REMESH_SEAM_EAST: int = REMESH_SEAM - 1
"""Marker for remesh filter eastern cell boundary point."""

VTK_BAD_TRIANGLE_MASK: str = "BadTriangle"
"""``vtkIntersectionPolyDataFilter`` bad triangle cell array name."""

VTK_BOUNDARY_MASK: str = "BoundaryPoints"
"""``vtkIntersectionPolyDataFilter`` intersection point array name."""

VTK_FREE_EDGE_MASK: str = "FreeEdge"
"""``vtkIntersectionPolyDataFilter`` free edge cell array name."""


def _cut_point_data(remeshed: pv.PolyData, original: pv.PolyData, /) -> None:
    """Interpolate the point data of the points a cut adds, in place.

    ``vtkIntersectionPolyDataFilter`` interpolates the point data of some of the
    points it adds from the wrong points, so each floating point array is given,
    at each added point, the value interpolated over the triangle of the
    `original` it lies in. A point on an edge takes the values of that edge's
    ends alone, so a height missing elsewhere on its triangle stays missing
    there (heights spec §4.1).

    Parameters
    ----------
    remeshed : pyvista.PolyData
        The mesh the cut made, whose points begin with those of `original`, and
        whose point data is rewritten in place at the points after them.
    original : pyvista.PolyData
        The triangulated mesh that was cut.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    start = original.n_points
    if remeshed.n_points == start:
        return

    added = np.asarray(remeshed.points[start:], dtype=np.float64)
    points = np.asarray(original.points, dtype=np.float64)

    # the barycentric weights of each added point, in the triangle it lies in
    cells = np.asarray(original.find_closest_cell(added), dtype=int).reshape(-1)
    triangles = original.regular_faces[cells]
    first = points[triangles[:, 0]]
    sides = (points[triangles[:, 1]] - first, points[triangles[:, 2]] - first)
    offset = added - first
    d00, d01, d11 = (
        np.einsum("ij,ij->i", one, two)
        for one, two in (
            (sides[0], sides[0]),
            (sides[0], sides[1]),
            (sides[1], sides[1]),
        )
    )
    d20, d21 = (np.einsum("ij,ij->i", offset, side) for side in sides)
    denominator = d00 * d11 - d01 * d01
    # a degenerate triangle, such as one at a pole, keeps the values given
    valid = np.abs(denominator) > np.finfo(np.float64).eps * (d00 * d11)
    safe = np.where(valid, denominator, 1.0)
    second = (d11 * d20 - d01 * d21) / safe
    third = (d00 * d21 - d01 * d20) / safe
    weights = np.clip(np.column_stack([1.0 - second - third, second, third]), 0, None)
    # a vertex the point does not reach, to rounding, takes no part, so that a
    # missing value there never reaches it
    weights[weights < 1e-9] = 0.0
    weights /= weights.sum(axis=1, keepdims=True)

    for name in original.point_data:
        values = np.asarray(original.point_data[name])
        if name not in remeshed.point_data or not np.issubdtype(
            values.dtype, np.floating
        ):
            continue
        corners = values[triangles].astype(np.float64)
        shape = weights.shape + (1,) * (corners.ndim - 2)
        weighted = np.where(
            weights.reshape(shape) > 0, weights.reshape(shape) * corners, 0.0
        ).sum(axis=1)
        # written into the array itself, which leaves the active scalars alone
        target = remeshed.point_data[name]
        target[start:][valid] = weighted[valid]


def remesh(
    mesh: pv.PolyData,
    /,
    meridian: float,
    *,
    boundary: bool | None = False,
    check: bool | None = False,
    rtol: float | None = None,
    atol: float | None = None,
) -> Remesh:
    """Slice `mesh` along `meridian` and triangulate any sliced cells.

    See :vtk:`vtkIntersectionPolyDataFilter` for more details.

    Parameters
    ----------
    mesh : PolyData
        The surface to be remeshed.
    meridian : float
        The meridian along which to remesh, in degrees longitude.
    boundary : bool, default=False
        Whether to attach the remeshed boundary points mask to the
        resultant mesh.
    check : bool, default=False
        Whether to check the remeshed surface for bad cells and
        free edges.
    rtol : float, optional
        The relative tolerance for longitudes close to the 'wrap meridian' -
        see :func:`geovista.common.wrap` for more.
    atol : float, optional
        The absolute tolerance for longitudes close to the 'wrap meridian' -
        see :func:`geovista.common.wrap` for more.

    Returns
    -------
    tuple of PolyData
        The remeshed surface, the remeshed surface left/west of the
        slice, and the remeshed surface right/east of the slice.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if mesh.n_cells == 0:
        emsg = "Cannot remesh an empty mesh"
        raise ValueError(emsg)

    meridian = wrap(meridian)[0]
    radius = float(distance(mesh))

    poly0: pv.PolyData = mesh.copy(deep=True)

    if GV_CELL_IDS not in poly0.cell_data:
        poly0.cell_data[GV_CELL_IDS] = np.arange(poly0.n_cells)

    if GV_POINT_IDS not in poly0.point_data:
        poly0.point_data[GV_POINT_IDS] = np.arange(poly0.n_points)

    if not triangulated(poly0):
        poly0.triangulate(inplace=True)

    # Ensure to explicitly use default direction=(0, 0, 1) for
    # the plane with a post x-axis rotation of 90 degrees.
    # See https://github.com/bjlittle/geovista/issues/447
    poly1 = pv.Plane(
        center=(radius / 2, 0, 0),
        i_resolution=1,
        j_resolution=1,
        i_size=radius,
        j_size=radius * 2,
        direction=(0, 0, 1),
    )
    poly1.rotate_x(90, inplace=True)
    poly1.rotate_z(meridian, inplace=True)
    poly1.triangulate(inplace=True)

    # https://vtk.org/doc/nightly/html/classvtkIntersectionPolyDataFilter.html
    alg = pv._vtk.vtkIntersectionPolyDataFilter()  # noqa: SLF001
    alg.SetInputDataObject(0, poly0)
    alg.SetInputDataObject(1, poly1)
    # BoundaryPoints (points) mask array
    alg.SetComputeIntersectionPointArray(True)  # noqa: FBT003
    # BadTriangle and FreeEdge (cells) mask arrays
    alg.SetCheckMesh(check)
    alg.SetSplitFirstOutput(True)  # noqa: FBT003
    alg.SetSplitSecondOutput(False)  # noqa: FBT003
    alg.Update()

    remeshed = pv.PolyData(alg.GetOutput(1))
    remeshed.copy_meta_from(poly0, deep=True)

    # the point data of the points the cut adds, such as their heights
    _cut_point_data(remeshed, poly0)

    if remeshed.n_cells == 0:
        # no remeshing has been performed as the meridian does not intersect the mesh
        remeshed_west, remeshed_east = pv.PolyData(), pv.PolyData()
    else:
        # split the triangulated remesh into its halves, west and east of the meridian
        centers = remeshed.cell_centers()
        lons = from_cartesian(centers, rtol=rtol, atol=atol)[:, 0]
        delta = lons - meridian
        lower_mask = (delta < 0) & (delta > -180)
        upper_mask = delta > 180
        # pyvista 0.49 annotates "extract_cells" to refuse a numpy boolean mask,
        # which it accepts at runtime, so the masks are typed as any array
        west_mask: NDArray[Any] = lower_mask | upper_mask
        east_mask: NDArray[Any] = ~west_mask

        # the vtkIntersectionPolyDataFilter is configured to *always* generate
        # the boundary mask point array as we require it internally, regardless
        # of whether the caller wants it or not afterwards
        boundary_mask = np.asarray(remeshed.point_data[VTK_BOUNDARY_MASK], dtype=bool)
        if not boundary:
            del remeshed.point_data[VTK_BOUNDARY_MASK]

        boundary_mask |= np.isclose(from_cartesian(remeshed)[:, 0], meridian)

        remeshed.point_data[GV_REMESH_POINT_IDS] = np.empty(
            remeshed.n_points, dtype=int
        )
        remeshed.point_data[GV_REMESH_POINT_IDS].fill(REMESH_JOIN)

        remeshed[GV_REMESH_POINT_IDS][boundary_mask] = REMESH_SEAM
        remeshed_west = cast(remeshed.extract_cells(west_mask))

        remeshed[GV_REMESH_POINT_IDS][boundary_mask] = REMESH_SEAM_EAST
        remeshed_east = cast(remeshed.extract_cells(east_mask))

        del remeshed.point_data[GV_REMESH_POINT_IDS]
        sanitize_vtk(remeshed, remeshed_west, remeshed_east)

    # each mesh returned carries only current fields
    return (
        _current(remeshed, mesh),
        _current(remeshed_west, mesh),
        _current(remeshed_east, mesh),
    )
