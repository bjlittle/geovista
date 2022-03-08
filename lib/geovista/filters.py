from datetime import datetime
from typing import Optional, Tuple

import pyvista as pv
from pyvista import _vtk
from pyvista.core.filters import _get_output
from vtk import vtkObject

from .common import calculate_radius, to_xy0, triangulated, wrap
from .log import get_logger

__all__ = [
    "cast_UnstructuredGrid_to_PolyData",
    "remesh",
]

# Configure the logger.
logger = get_logger(__name__)

# Type aliases.
Remesh = Tuple[pv.PolyData, pv.PolyData, pv.PolyData]


def cast_UnstructuredGrid_to_PolyData(
    mesh: pv.UnstructuredGrid,
    clean: Optional[bool] = False,
) -> pv.PolyData:
    """
    TBD

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if not isinstance(mesh, pv.UnstructuredGrid):
        dtype = type(mesh).split(" ")[1][:-1]
        emsg = f"Expected a 'pyvista.UnstructuredGrid', got {dtype}."
        raise TypeError(emsg)

    # see https://vtk.org/pipermail/vtkusers/2011-March/066506.html
    alg = _vtk.vtkGeometryFilter()
    alg.AddInputData(mesh)
    alg.Update()
    result = _get_output(alg)

    if clean:
        result = result.clean()

    return result


def remesh(
    mesh: pv.PolyData,
    meridian: float,
    check: Optional[bool] = False,
    intersection: Optional[bool] = False,
    warnings: Optional[bool] = False,
) -> Remesh:
    """
    TBD

    Notes
    -----
    .. versionadded :: 0.1.0

    """
    if not warnings:
        # https://public.kitware.com/pipermail/vtkusers/2004-February/022390.html
        vtkObject.GlobalWarningDisplayOff()

    meridian = wrap(meridian)[0]
    radius = calculate_radius(mesh)
    logger.debug(f"{meridian=}, {radius=}")

    poly0: pv.PolyData = mesh.copy(deep=True)

    if not triangulated(poly0):
        start = datetime.now()
        poly0.triangulate(inplace=True)
        end = datetime.now()
        logger.debug(f"mesh: triangulated [{(end-start).total_seconds()} secs]")

    poly1 = pv.Plane(
        center=(radius / 2, 0, 0),
        i_resolution=1,
        j_resolution=1,
        i_size=radius,
        j_size=radius * 2,
        direction=(0, 1, 0),
    )
    poly1.rotate_z(meridian, inplace=True)
    poly1.triangulate(inplace=True)

    # https://vtk.org/doc/nightly/html/classvtkIntersectionPolyDataFilter.html
    alg = _vtk.vtkIntersectionPolyDataFilter()
    alg.SetInputDataObject(0, poly0)
    alg.SetInputDataObject(1, poly1)
    # BoundaryPoints (points) array
    alg.SetComputeIntersectionPointArray(intersection)
    # BadTriangle and FreeEdge (cells) arrays
    alg.SetCheckMesh(check)
    alg.SetSplitFirstOutput(True)
    alg.SetSplitSecondOutput(False)
    start = datetime.now()
    alg.Update()
    end = datetime.now()
    logger.debug(
        f"remeshed: lines={alg.GetNumberOfIntersectionLines()}, "
        f"points={alg.GetNumberOfIntersectionPoints()} "
        f"[{(end-start).total_seconds()} secs]"
    )

    remeshed: pv.PolyData = _get_output(alg, oport=1)

    if not warnings:
        vtkObject.GlobalWarningDisplayOn()

    if remeshed.n_cells == 0:
        # no remeshing has been performed as the meridian does not intersect the mesh
        remeshed_west, remeshed_east = pv.PolyData(), pv.PolyData()
        logger.debug(f"no remesh performed with {meridian=}")
    else:
        # split the triangulated remesh into its two halves i.e., the mesh containing those remeshed cells west of the
        # meridian, and the mesh containing those remeshed cells east of the meridian
        centers = remeshed.cell_centers()
        lons = to_xy0(centers.points)[:, 0]
        delta = lons - meridian
        lower_mask = (delta < 0) & (delta > -180)
        upper_mask = delta > 180
        western_mask = lower_mask | upper_mask
        eastern_mask = ~western_mask
        logger.debug(
            f"split: lower={lower_mask.sum()}, upper={upper_mask.sum()}, "
            f"west={western_mask.sum()}, east={eastern_mask.sum()}, "
            f"total={remeshed.n_cells}"
        )
        remeshed_west = remeshed.extract_cells(western_mask)
        remeshed_east = remeshed.extract_cells(eastern_mask)

    return remeshed, remeshed_west, remeshed_east
