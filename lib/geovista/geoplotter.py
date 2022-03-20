from typing import Any, Optional

from pyproj import CRS, Transformer
import pyvista as pv
from pyvista.utilities import abstract_class
import pyvistaqt as pvqt
import vtk

from .common import to_xy0
from .core import add_texture_coords, cut_along_meridian
from .crs import WGS84, from_wkt, get_central_meridian
from .geometry import COASTLINE_RESOLUTION, get_coastlines
from .log import get_logger

__all__ = ["GeoBackgroundPlotter", "GeoMultiPlotter", "GeoPlotter", "logger"]

# configure the logger
logger = get_logger(__name__)


@abstract_class
class GeoBasePlotter:
    def _init(self, kwargs):
        if "crs" in kwargs:
            crs = kwargs.pop("crs")
            crs = CRS.from_user_input(crs)
        else:
            crs = WGS84
        self.crs = crs

    def add_base_layer(self, **kwargs: Optional[Any]) -> vtk.vtkActor:
        """
        TBD

        Parameters
        ----------
        kwargs : Any, optional


        Returns
        -------
        vtkActor


        Notes
        -----
        .. versionadded:: 0.1.0

        """
        # TODO: provide robust zorder support
        mesh = pv.Sphere(radius=1 - (5e-3), theta_resolution=360, phi_resolution=180)
        if "texture" in kwargs:
            mesh = add_texture_coords(mesh, antimeridian=True)
        return self.add_mesh(mesh, **kwargs)

    def add_coastlines(
        self, resolution: Optional[str] = COASTLINE_RESOLUTION, **kwargs: Optional[Any]
    ) -> vtk.vtkActor:
        """
        TBD

        Parameters
        ----------
        resolution : str, default=COASTLINE_RESOLUTION

        kwargs : Any, optional


        Returns
        -------
        vtkActor


        Notes
        -----
        .. versionadded:: 0.1.0

        """
        mesh = get_coastlines(resolution=resolution)
        return self.add_mesh(mesh, **kwargs)

    def add_mesh(self, mesh, **kwargs):
        if isinstance(mesh, pv.PolyData):
            src_crs = from_wkt(mesh)
            project = src_crs and src_crs != self.crs
            if project:
                meridian = get_central_meridian(self.crs)
                mesh = cut_along_meridian(mesh, meridian=meridian, antimeridian=True)
            if "texture" in kwargs:
                mesh = add_texture_coords(mesh, antimeridian=True)
            if project:
                ll = to_xy0(mesh, closed_interval=True)
                transformer = Transformer.from_crs(src_crs, self.crs, always_xy=True)
                xs, ys = transformer.transform(ll[:, 0], ll[:, 1])
                mesh.points[:, 0] = xs
                mesh.points[:, 1] = ys
                mesh.points[:, 2] = 0

        return super().add_mesh(mesh, **kwargs)


class GeoBackgroundPlotter(GeoBasePlotter, pvqt.BackgroundPlotter):
    def __init__(self, *args, **kwargs):
        self._init(kwargs)
        super().__init__(*args, **kwargs)


class GeoMultiPlotter(GeoBasePlotter, pvqt.MultiPlotter):
    def __init__(self, *args, **kwargs):
        self._init(kwargs)
        super().__init__(*args, **kwargs)


class GeoPlotter(GeoBasePlotter, pv.Plotter):
    def __init__(self, *args, **kwargs):
        self._init(kwargs)
        super().__init__(*args, **kwargs)
