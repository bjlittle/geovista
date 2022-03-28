from functools import lru_cache
from typing import Any, Optional

from pyproj import CRS, Transformer
import pyvista as pv
import pyvistaqt as pvqt
import vtk

from .common import to_xy0, to_xyz
from .core import add_texture_coords, cut_along_meridian
from .crs import WGS84, from_wkt, get_central_meridian, set_central_meridian
from .filters import cast_UnstructuredGrid_to_PolyData as cast
from .geometry import COASTLINE_RESOLUTION, get_coastlines
from .log import get_logger
from .raster import wrap_texture

__all__ = ["GeoBackgroundPlotter", "GeoMultiPlotter", "GeoPlotter", "logger"]

# configure the logger
logger = get_logger(__name__)


@lru_cache
def _get_lfric(
    resolution: Optional[str] = None,
    radius: Optional[float] = None,
) -> pv.PolyData:
    """
    Retrieve the LFRic unstructured cubed-sphere from the GeoVista cache.

    Parameters
    ----------
    resolution : str, default="c192"
        The resolution of the LFRic unstructured cubed-sphere.
    radius : float, default=1.0
        The radius of the sphere. Defaults to an S2 unit sphere.

    Returns
    -------
    PolyData
        The LFRic spherical mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    from .cache import lfric

    mesh = lfric(resolution=resolution)

    if radius:
        ll = to_xy0(mesh)
        xyz = to_xyz(ll[:, 0], ll[:, 1], radius=radius)
        mesh.points = xyz

    mesh.active_scalars_name = None

    return mesh


class GeoPlotterBase:
    def __init__(self, *args, **kwargs):
        if "crs" in kwargs:
            crs = kwargs.pop("crs")
            crs = CRS.from_user_input(crs)
        else:
            crs = WGS84
        self.crs = crs
        super().__init__(*args, **kwargs)

    def add_base_layer(self, **kwargs: Optional[Any]) -> vtk.vtkActor:
        """
        TODO

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
        offset_base_layer = self.crs.is_projected
        kwargs["offset_base_layer"] = offset_base_layer

        if "radius" in kwargs:
            radius = kwargs.pop("radius")
        else:
            # TODO: remove the magic numbers
            radius = None if offset_base_layer else 1.0 - (1e-3)

        resolution = kwargs.pop("resolution") if "resolution" in kwargs else None
        logger.debug(f"{radius=}")
        mesh = _get_lfric(resolution=resolution, radius=radius)
        actor = self.add_mesh(mesh, **kwargs)

        return actor

    def add_coastlines(
        self, resolution: Optional[str] = COASTLINE_RESOLUTION, **kwargs: Optional[Any]
    ) -> vtk.vtkActor:
        """
        TODO

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

        offset_base_layer = (
            kwargs.pop("offset_base_layer") if "offset_base_layer" in kwargs else False
        )

        if isinstance(mesh, pv.PolyData):
            src_crs = from_wkt(mesh)
            tgt_crs = self.crs
            project = src_crs and src_crs != tgt_crs
            meridian = get_central_meridian(tgt_crs) or 0
            if project:
                if meridian:
                    mesh.rotate_z(-meridian, inplace=True)
                    tgt_crs = set_central_meridian(tgt_crs, 0)

                mesh = cut_along_meridian(mesh, antimeridian=True)
            if "texture" in kwargs:
                mesh = add_texture_coords(mesh, antimeridian=True)
                texture = wrap_texture(kwargs["texture"], central_meridian=meridian)
                kwargs["texture"] = texture
            if project:
                ll = to_xy0(mesh, closed_interval=True)
                transformer = Transformer.from_crs(src_crs, tgt_crs, always_xy=True)
                xs, ys = transformer.transform(ll[:, 0], ll[:, 1], errcheck=True)
                mesh.points[:, 0] = xs
                mesh.points[:, 1] = ys
                zoffset = 0
                if offset_base_layer:
                    xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds
                    xdelta = abs(xmax - xmin)
                    ydelta = abs(ymax - ymin)
                    delta = max(xdelta, ydelta)
                    # TODO: remove the magic number
                    zoffset = -delta * 1e-3
                mesh.points[:, 2] = zoffset

        return super().add_mesh(mesh, **kwargs)


class GeoBackgroundPlotter(GeoPlotterBase, pvqt.BackgroundPlotter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class GeoMultiPlotter(GeoPlotterBase, pvqt.MultiPlotter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class GeoPlotter(GeoPlotterBase, pv.Plotter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
