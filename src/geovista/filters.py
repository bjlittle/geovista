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

from typing import TYPE_CHECKING

import lazy_loader as lazy

from .common import (
    GV_CELL_IDS,
    GV_POINT_IDS,
    GV_REMESH_POINT_IDS,
    REMESH_JOIN,
    REMESH_SEAM,
    distance,
    from_cartesian,
    sanitize_data,
    triangulated,
    wrap,
)
from .common import cast_UnstructuredGrid_to_PolyData as cast

if TYPE_CHECKING:
    import pyvista as pv

    # type aliases.
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


def remesh(
    mesh: pv.PolyData,
    meridian: float,
    boundary: bool | None = False,
    check: bool | None = False,
    rtol: float | None = None,
    atol: float | None = None,
) -> Remesh:
    """Slice `mesh` along `meridian` and triangulate any sliced cells.

    See the
    `vtkIntersectionPolyDataFilter <https://vtk.org/doc/nightly/html/classvtkIntersectionPolyDataFilter.html>`_
    documentation for more.

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
    radius = distance(mesh)

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
    alg = pv._vtk.vtkIntersectionPolyDataFilter()
    alg.SetInputDataObject(0, poly0)
    alg.SetInputDataObject(1, poly1)
    # BoundaryPoints (points) mask array
    alg.SetComputeIntersectionPointArray(True)
    # BadTriangle and FreeEdge (cells) mask arrays
    alg.SetCheckMesh(check)
    alg.SetSplitFirstOutput(True)
    alg.SetSplitSecondOutput(False)
    alg.Update()

    remeshed: pv.PolyData = pv.core.filters._get_output(alg, oport=1)

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
        west_mask = lower_mask | upper_mask
        east_mask = ~west_mask

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
        sanitize_data(remeshed, remeshed_west, remeshed_east)

    return remeshed, remeshed_west, remeshed_east
