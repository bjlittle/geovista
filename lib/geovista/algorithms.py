from pyproj import Transformer
import pyvista as pv
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase

from .bridge import Transform
from .common import ZLEVEL_FACTOR, to_xy0
from .core import add_texture_coords, cut_along_meridian, resize
from .crs import WGS84, from_wkt, get_central_meridian, set_central_meridian
from .filters import cast_UnstructuredGrid_to_PolyData as cast
from .geometry import COASTLINE_RESOLUTION, get_coastlines
from .log import get_logger
from .raster import wrap_texture
from .samples import lfric

logger = get_logger(__name__)


def add_mesh_handler(
    mesh,
    tgt_crs,
    radius=None,
    zfactor=ZLEVEL_FACTOR,
    zlevel=0,
    texture=None,
    remove_nan=True,
):
    if isinstance(mesh, pv.RectilinearGrid):
        if mesh.dimensions[-1] > 1:
            raise ValueError("Cannot handle 3D RectilinearGrids.")
        mesh = Transform.from_1d(mesh.x, mesh.y, data=mesh.active_scalars)

    src_crs = from_wkt(mesh)
    project = src_crs and src_crs != tgt_crs
    meridian = get_central_meridian(tgt_crs) or 0

    if project:
        if meridian:
            mesh.rotate_z(-meridian, inplace=True)
            tgt_crs = set_central_meridian(tgt_crs, 0)
        try:
            mesh = cut_along_meridian(mesh, antimeridian=True)
        except ValueError:
            pass

    if texture is not None:
        mesh = add_texture_coords(mesh, antimeridian=True)
        texture = wrap_texture(texture, central_meridian=meridian)

    if project:
        lonlat = to_xy0(mesh, radius=radius, closed_interval=True)
        transformer = Transformer.from_crs(src_crs, tgt_crs, always_xy=True)
        xs, ys = transformer.transform(lonlat[:, 0], lonlat[:, 1], errcheck=True)
        mesh.points[:, 0] = xs
        mesh.points[:, 1] = ys
        zoffset = 0
        if zlevel:
            xmin, xmax, ymin, ymax, _, _ = mesh.bounds
            xdelta, ydelta = abs(xmax - xmin), abs(ymax - ymin)
            delta = max(xdelta, ydelta)
            zoffset = zlevel * zfactor * delta
            logger.debug("delta=%f, zfactor=%f, zlevel=%d", delta, zfactor, zlevel)
        logger.debug("zoffset=%f", zoffset)
        mesh.points[:, 2] = zoffset

    return mesh


class MeshHandler(VTKPythonAlgorithmBase):
    def __init__(
        self,
        tgt_crs,
        radius=None,
        zfactor=ZLEVEL_FACTOR,
        zlevel=0,
        texture=None,
        outputType="vtkPolyData",
    ):
        VTKPythonAlgorithmBase.__init__(
            self,
            nInputPorts=1,
            nOutputPorts=1,
            outputType=outputType,
        )
        self.tgt_crs = tgt_crs
        self.radius = radius
        self.zfactor = zfactor
        self.zlevel = zlevel
        self.texture = texture

    def GetOutput(self, port=0):
        output = pv.wrap(self.GetOutputDataObject(port))
        if output.active_scalars is None and output.n_arrays:
            if len(output.point_data):
                output.set_active_scalars(output.point_data.keys()[0])
            elif len(output.cell_data):
                output.set_active_scalars(output.cell_data.keys()[0])
        return output

    def RequestData(self, request, inInfo, outInfo):
        pdi = pv.wrap(self.GetInputData(inInfo, 0, 0)).copy(deep=True)
        pdo = self.GetOutputData(outInfo, 0)
        mesh = add_mesh_handler(
            pdi,
            self.tgt_crs,
            radius=self.radius,
            zfactor=self.zfactor,
            zlevel=self.zlevel,
            texture=self.texture,
        )
        pdo.ShallowCopy(mesh)
        return 1
