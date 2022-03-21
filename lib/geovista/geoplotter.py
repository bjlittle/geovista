from typing import Any, Optional

import numpy as np
from pyproj import CRS, Transformer
import pyvista as pv
from pyvista.utilities import abstract_class
import pyvistaqt as pvqt
import vtk

from .common import GV_FIELD_CRS, to_xy0
from .core import add_texture_coords, cut_along_meridian
from .crs import WGS84, from_wkt, get_central_meridian, set_central_meridian
from .filters import cast_UnstructuredGrid_to_PolyData as cast
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

        radius = 1 if (zoffset := self.crs.is_projected) else 1 - (5e-3)
        kwargs["zoffset"] = zoffset
        mesh = pv.Sphere(radius=radius, theta_resolution=360, phi_resolution=180)

        # attach the pyproj crs serialized as ogc wkt
        wkt = np.array([WGS84.to_wkt()])
        mesh.field_data[GV_FIELD_CRS] = wkt

        if "show_edges" in kwargs:
            _ = kwargs.pop("show_edges")

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
        if isinstance(mesh, pv.UnstructuredGrid):
            mesh = cast(mesh)

        zoffset = kwargs.pop("zoffset") if "zoffset" in kwargs else False

        if isinstance(mesh, pv.PolyData):
            src_crs = from_wkt(mesh)
            tgt_crs = self.crs
            project = src_crs and src_crs != tgt_crs
            if project:
                meridian = get_central_meridian(tgt_crs) or 0

                if meridian:
                    mesh.rotate_z(-meridian, inplace=True)
                    tgt_crs = set_central_meridian(tgt_crs, 0)

                mesh = cut_along_meridian(mesh, antimeridian=True)
            if "texture" in kwargs:
                mesh = add_texture_coords(mesh, antimeridian=True)
            if project:
                ll = to_xy0(mesh, closed_interval=True)
                transformer = Transformer.from_crs(src_crs, tgt_crs, always_xy=True)
                xs, ys = transformer.transform(ll[:, 0], ll[:, 1], errcheck=True)
                mesh.points[:, 0] = xs
                mesh.points[:, 1] = ys
                if zoffset:
                    xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds
                    xdelta = abs(xmax - xmin)
                    ydelta = abs(ymax - ymin)
                    delta = max(xdelta, ydelta)
                    zoffset = -delta * 1e-3
                else:
                    zoffset = 0
                mesh.points[:, 2] = zoffset

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
