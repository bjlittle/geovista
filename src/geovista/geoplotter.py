"""
Provide behaviour specialisation of :class:`pyvista.plotting.plotting.Plotter`.

"""
# pylint: disable=no-member

from functools import lru_cache
from typing import Any, Optional, Union
from warnings import warn

import numpy as np
from numpy.typing import ArrayLike
from pyproj import CRS, Transformer
import pyvista as pv
import pyvistaqt as pvqt
import vtk

from .common import GV_FIELD_CRS, RADIUS, ZLEVEL_FACTOR, to_xy0, to_xyz
from .core import add_texture_coords, cut_along_meridian, resize
from .crs import WGS84, from_wkt, get_central_meridian, set_central_meridian
from .filters import cast_UnstructuredGrid_to_PolyData as cast
from .geometry import COASTLINE_RESOLUTION, get_coastlines
from .raster import wrap_texture
from .samples import lfric

__all__ = ["GeoBackgroundPlotter", "GeoMultiPlotter", "GeoPlotter"]

# type aliases
CRSLike = Union[int, str, dict, CRS]


@lru_cache
def _get_lfric(
    resolution: Optional[str] = None,
    radius: Optional[float] = None,
) -> pv.PolyData:
    """
    Retrieve the LFRic unstructured cubed-sphere from the GeoVista cache.

    Parameters
    ----------
    resolution : str, default="c96"
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
    mesh = lfric(resolution=resolution)

    if radius:
        lonlat = to_xy0(mesh)
        xyz = to_xyz(lonlat[:, 0], lonlat[:, 1], radius=radius)
        mesh.points = xyz

    mesh.active_scalars_name = None

    return mesh


class GeoPlotterBase:
    def __init__(self, *args: Optional[Any], **kwargs: Optional[Any]):
        if args:
            klass = f"'{self.__class__.__name__}'"
            if len(args) == 1 and ("crs" not in kwargs or kwargs["crs"] is None):
                wmsg = (
                    f"{klass} received an unexpected argument. "
                    "Assuming 'crs' keyword argument instead..."
                )
                warn(wmsg)
                kwargs["crs"] = args[0]
                args = ()
            else:
                plural = "s" if len(args) > 1 else ""
                pre = ",".join([f"'{arg}'" for arg in args[:-1]])
                bad = f"{pre} and '{args[-1]}'" if pre else f"'{args[0]}'"
                emsg = (
                    f"{klass} received {len(args)} unexpected argument{plural}, {bad}."
                )
                raise ValueError(emsg)

        if "crs" in kwargs:
            crs = kwargs.pop("crs")
            crs = CRS.from_user_input(crs) if crs is not None else WGS84
        else:
            crs = WGS84
        self.crs = crs
        super().__init__(*args, **kwargs)

    def add_base_layer(
        self, mesh: Optional[pv.PolyData] = None, **kwargs: Optional[Any]
    ) -> vtk.vtkActor:
        """
        TODO

        Parameters
        ----------
        mesh
        kwargs : Any, optional

        Returns
        -------
        vtkActor

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        resolution = kwargs.pop("resolution") if "resolution" in kwargs else None

        if self.crs.is_projected:
            # pass-thru "zfactor" and "zlevel" to the "add_mesh" method,
            # but remove "radius", as it's not applicable to planar projections
            if "radius" in kwargs:
                _ = kwargs.pop("radius")
            # opt to the default radius for the base layer mesh
            radius = None
            if "zfactor" not in kwargs:
                kwargs["zfactor"] = ZLEVEL_FACTOR
            if "zlevel" not in kwargs:
                kwargs["zlevel"] = -1
        else:
            original = (
                abs(float(kwargs.pop("radius"))) if "radius" in kwargs else RADIUS
            )
            zfactor = (
                float(kwargs.pop("zfactor")) if "zfactor" in kwargs else ZLEVEL_FACTOR
            )
            zlevel = int(kwargs.pop("zlevel")) if "zlevel" in kwargs else -1
            radius = original + original * zlevel * zfactor

        if mesh is not None:
            if radius is not None:
                mesh = resize(mesh, radius=radius)
        else:
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

    def add_mesh(self, mesh: Any, **kwargs: Optional[Any]):
        if isinstance(mesh, pv.UnstructuredGrid):
            mesh = cast(mesh)

        if isinstance(mesh, pv.PolyData):
            radius = float(kwargs.pop("radius")) if "radius" in kwargs else None
            zfactor = (
                float(kwargs.pop("zfactor")) if "zfactor" in kwargs else ZLEVEL_FACTOR
            )
            zlevel = int(kwargs.pop("zlevel")) if "zlevel" in kwargs else 0

            src_crs = from_wkt(mesh)
            tgt_crs = self.crs
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

            if "texture" in kwargs and kwargs["texture"] is not None:
                mesh = add_texture_coords(mesh, antimeridian=True)
                texture = wrap_texture(kwargs["texture"], central_meridian=meridian)
                kwargs["texture"] = texture

            if project:
                lonlat = to_xy0(mesh, radius=radius, closed_interval=True)
                transformer = Transformer.from_crs(src_crs, tgt_crs, always_xy=True)
                xs, ys = transformer.transform(
                    lonlat[:, 0], lonlat[:, 1], errcheck=True
                )
                mesh.points[:, 0] = xs
                mesh.points[:, 1] = ys
                zoffset = 0
                if zlevel:
                    xmin, xmax, ymin, ymax, _, _ = mesh.bounds
                    xdelta, ydelta = abs(xmax - xmin), abs(ymax - ymin)
                    delta = max(xdelta, ydelta)
                    zoffset = zlevel * zfactor * delta
                mesh.points[:, 2] = zoffset

        return super().add_mesh(mesh, **kwargs)

    def add_point_labels(
        self,
        points: Any,
        labels: Any,
        **kwargs: Optional[Any],
    ) -> vtk.vtkActor2D:
        if isinstance(points, pv.PolyData):
            crs = from_wkt(points)

            if crs is not None and crs != WGS84:
                lonlat = to_xy0(points)
                transformer = Transformer.from_crs(crs, self.crs, always_xy=True)
                xs, ys = transformer.transform(
                    lonlat[:, 0], lonlat[:, 1], errcheck=True
                )
                result = pv.PolyData()
                result.copy_structure(points)
                result.points[:, 0] = xs
                result.points[:, 1] = ys
                result.points[:, 2] = 0
                points = result

        return super().add_point_labels(points, labels, **kwargs)

    def add_points(
        self,
        points: Optional[Any] = None,
        xs: Optional[ArrayLike] = None,
        ys: Optional[ArrayLike] = None,
        crs: Optional[CRSLike] = None,
        radius: Optional[float] = None,
        zfactor: Optional[float] = None,
        zlevel: Optional[int] = None,
        **kwargs: Optional[Any],
    ) -> vtk.vtkActor:
        kwargs["style"] = "points"

        if "texture" in kwargs:
            _ = kwargs.pop("texture")

        if points is not None:
            if crs is not None:
                warn("Ignoring 'crs' as cartesian xyz 'points' have been provided.")
                crs = None

        if crs is not None:
            if xs is None or ys is None:
                emsg = "Given a 'crs', both 'xs' and 'ys' require to be provided."
                raise ValueError(emsg)

            xs = np.asanyarray(xs)
            ys = np.asanyarray(ys)

            if xs.shape != ys.shape:
                emsg = (
                    "Require 'xs' and 'ys' with the same shape, got "
                    f"{xs.shape=} and {ys.shape}."
                )
                raise ValueError(emsg)

            crs = CRS.from_user_input(crs)

            if crs != WGS84:
                transformer = Transformer.from_crs(crs, WGS84, always_xy=True)
                xs, ys = transformer.transform(xs, ys, errcheck=True)

            radius = RADIUS if radius is None else abs(radius)

            if zfactor is None:
                zfactor = ZLEVEL_FACTOR

            if zlevel is None:
                zlevel = 0

            radius += radius * zlevel * zfactor

            xyz = to_xyz(xs, ys, radius=radius)
            points = pv.PolyData(xyz)
            # attach the pyproj crs serialized as ogc wkt
            wkt = np.array([WGS84.to_wkt()])
            points.field_data[GV_FIELD_CRS] = wkt
            kwargs["radius"] = radius
            kwargs["zfactor"] = zfactor
            kwargs["zlevel"] = zlevel

        return self.add_mesh(points, **kwargs)


class GeoBackgroundPlotter(GeoPlotterBase, pvqt.BackgroundPlotter):
    pass


class GeoMultiPlotter(GeoPlotterBase, pvqt.MultiPlotter):
    pass


class GeoPlotter(GeoPlotterBase, pv.Plotter):
    pass
