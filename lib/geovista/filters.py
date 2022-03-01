from datetime import datetime
from typing import Optional, Tuple

import numpy as np
import pyvista as pv
from pyvista import _vtk
from pyvista.core.filters import _get_output
from vtk import vtkObject

from .common import triangulated
from .log import get_logger

__all__ = [
    "GV_REMESH_IDS",
    "cast_UnstructuredGrid_to_PolyData",
    "remesh",
]

# Configure the logger.
logger = get_logger(__name__)

# Type aliases.
Remesh = Tuple[pv.PolyData, pv.PolyData, pv.PolyData]

#: Name of the geovista remesh filter cell indices array.
GV_REMESH_IDS = "gvRemeshCellIds"


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
    mesh: pv.PolyData, ribbon: pv.PolyData, warnings: Optional[bool] = False
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

    m0: pv.PolyData = mesh.copy(deep=True)
    r1 = pv.PolyData()
    r1.copy_structure(ribbon)

    if not triangulated(m0):
        m0.triangulate(inplace=True)
        logger.debug("mesh: triangulate")

    if GV_REMESH_IDS in m0.cell_data:
        del m0.cell_data[GV_REMESH_IDS]

    m0.cell_data[GV_REMESH_IDS] = np.arange(m0.n_cells)

    if not triangulated(r1):
        r1.triangulate(inplace=True)
        logger.debug("ribbon: triangulate")

    # https://vtk.org/doc/nightly/html/classvtkIntersectionPolyDataFilter.html
    alg = _vtk.vtkIntersectionPolyDataFilter()
    alg.SetInputDataObject(0, m0)
    alg.SetInputDataObject(1, r1)
    alg.SetComputeIntersectionPointArray(True)
    alg.SetSplitFirstOutput(True)
    alg.SetSplitSecondOutput(False)
    start = datetime.now()
    alg.Update()
    end = datetime.now()
    logger.debug(
        f"remesh: lines={alg.GetNumberOfIntersectionLines()}, "
        f"points={alg.GetNumberOfIntersectionPoints()} "
        f"[{(end-start).total_seconds()} secs]"
    )

    intersection: pv.PolyData = _get_output(alg, oport=0)
    remeshed: pv.PolyData = _get_output(alg, oport=1)

    if not warnings:
        vtkObject.GlobalWarningDisplayOn()

    return m0, intersection, remeshed
