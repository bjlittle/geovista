"""Plotting algorithms."""
import traceback
from typing import Any
from warnings import warn

from pyproj import Transformer
import pyvista as pv

try:
    from pyvista.plotting.utilities.algorithms import set_algorithm_input
except ImportError:
    from pyvista.utilities import set_algorithm_input
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase

from .bridge import Transform
from .common import GV_FIELD_ZSCALE, ZLEVEL_SCALE, distance, from_cartesian, point_cloud
from .core import add_texture_coords, cut_along_meridian, resize
from .crs import from_wkt, get_central_meridian, set_central_meridian


def add_mesh_handler(mesh: Any, tgt_crs: Any, **kwargs: Any | None):
    """Handle static meshes."""
    if isinstance(mesh, pv.RectilinearGrid):
        if mesh.dimensions[-1] > 1:
            raise ValueError("Cannot handle 3D RectilinearGrids.")
        mesh = Transform.from_1d(
            mesh.x, mesh.y, data=mesh.active_scalars, name=mesh.active_scalars_name
        )

    if isinstance(mesh, pv.PolyData):
        atol = float(kwargs.pop("atol")) if "atol" in kwargs else None
        radius = abs(float(kwargs.pop("radius"))) if "radius" in kwargs else None
        rtol = float(kwargs.pop("rtol")) if "rtol" in kwargs else None
        zlevel = int(kwargs.pop("zlevel")) if "zlevel" in kwargs else 0
        cloud = point_cloud(mesh)

        if "zscale" in kwargs:
            zscale = float(kwargs.pop("zscale"))
        elif cloud and GV_FIELD_ZSCALE in mesh.field_data:
            zscale = mesh[GV_FIELD_ZSCALE][0]
        else:
            zscale = ZLEVEL_SCALE

        src_crs = from_wkt(mesh)
        project = src_crs and src_crs != tgt_crs
        meridian = get_central_meridian(tgt_crs) or 0

        # TODO: implement projection support for line meshes
        if project and mesh.n_lines:
            wmsg = (
                "Line projection support not yet available, "
                "scheduled for geovista=0.3.0."
            )
            warn(wmsg, stacklevel=2)
            return

        if project and not cloud:
            if meridian:
                mesh.rotate_z(-meridian, inplace=True)
                tgt_crs = set_central_meridian(tgt_crs, 0)
            cut_mesh = cut_along_meridian(mesh, antimeridian=True, rtol=rtol, atol=atol)
            if meridian:
                # undo rotation
                mesh.rotate_z(meridian, inplace=True)
            mesh = cut_mesh

        if "texture" in kwargs and kwargs["texture"] is not None:
            mesh = add_texture_coords(mesh, antimeridian=True)

        if project:
            lonlat = from_cartesian(mesh, closed_interval=True, rtol=rtol, atol=atol)
            transformer = Transformer.from_crs(src_crs, tgt_crs, always_xy=True)
            xs, ys = transformer.transform(lonlat[:, 0], lonlat[:, 1], errcheck=True)
            zs = 0

            if cloud:
                mesh = mesh.copy(deep=True)

            mesh.points[:, 0] = xs
            mesh.points[:, 1] = ys

            if zlevel or cloud:
                xmin, xmax, ymin, ymax, _, _ = mesh.bounds
                xdelta, ydelta = abs(xmax - xmin), abs(ymax - ymin)
                # TODO: make this configurable at the API/module level
                delta = min(xdelta, ydelta) // 4

                if cloud:
                    zlevel += lonlat[:, 2]

                zs = zlevel * zscale * delta

            mesh.points[:, 2] = zs
        else:
            if zlevel:
                if not cloud:
                    radius = distance(mesh)

                mesh = resize(mesh, radius=radius, zlevel=zlevel, zscale=zscale)

    return mesh


class MeshHandler(VTKPythonAlgorithmBase):
    """Algorithm mesh handler for plotter."""

    def __init__(
        self,
        tgt_crs,
        outputType="vtkPolyData",
        **kwargs,
    ):
        VTKPythonAlgorithmBase.__init__(
            self,
            nInputPorts=1,
            nOutputPorts=1,
            outputType=outputType,
        )
        self.kwargs = kwargs
        self.tgt_crs = tgt_crs

    def GetOutput(self, port=0):
        """Get output of the algorithm."""
        output = pv.wrap(self.GetOutputDataObject(port))
        if output.active_scalars is None and output.n_arrays:
            if len(output.point_data):
                output.set_active_scalars(output.point_data.keys()[0])
            elif len(output.cell_data):
                output.set_active_scalars(output.cell_data.keys()[0])
        return output

    def RequestData(self, request, inInfo, outInfo):
        """Request data pipeline step."""
        try:
            pdi = pv.wrap(self.GetInputData(inInfo, 0, 0)).copy(deep=True)
            pdo = self.GetOutputData(outInfo, 0)
            mesh = add_mesh_handler(pdi, self.tgt_crs, **self.kwargs)
            pdo.ShallowCopy(mesh)
        except Exception as e:
            traceback.print_exc()
            raise e
        return 1


def mesh_alogirthm_handler(inp, *kwargs):
    """Mesh algorithm handler."""
    alg = MeshHandler(**kwargs)
    set_algorithm_input(alg, inp)
    return alg
