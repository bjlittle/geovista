import pyvista as pv
from pyvista import _vtk
from pyvista.core.filters import _get_output

from .log import get_logger

__all__ = ["cast_unstructured_grid_to_polydata"]

# Configure the logger.
logger = get_logger(__name__)


def cast_unstructured_grid_to_polydata(mesh: pv.UnstructuredGrid) -> pv.PolyData:
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

    alg = _vtk.vtkGeometryFilter()
    alg.AddInputData(mesh)
    alg.Update()
    result = _get_output(alg).clean()

    return result
