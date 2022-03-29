from functools import lru_cache
from typing import Any, Optional
from warnings import warn

from pyproj import CRS, Transformer
import pyvista as pv
import pyvistaqt as pvqt
import vtk

from .common import ZLEVEL_FACTOR, to_xy0, to_xyz
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
        lonlat = to_xy0(mesh)
        xyz = to_xyz(lonlat[:, 0], lonlat[:, 1], radius=radius)
        mesh.points = xyz

    mesh.active_scalars_name = None

    return mesh


class GeoPlotterBase:
    def __init__(self, *args, **kwargs):
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
        resolution = kwargs.pop("resolution") if "resolution" in kwargs else None
        logger.debug(
            "resolution=%s, is_projected=%s", resolution, self.crs.is_projected
        )

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
            logger.debug("radius=%s", radius)
        else:
            original = abs(float(kwargs.pop("radius"))) if "radius" in kwargs else 1.0
            zfactor = (
                float(kwargs.pop("zfactor")) if "zfactor" in kwargs else ZLEVEL_FACTOR
            )
            zlevel = int(kwargs.pop("zlevel")) if "zlevel" in kwargs else -1
            radius = original + original * zlevel * zfactor
            logger.debug(
                "radius=%f(%s), zfactor=%f, zlevel=%s",
                radius,
                original,
                zfactor,
                zlevel,
            )

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

        zfactor = float(kwargs.pop("zfactor")) if "zfactor" in kwargs else ZLEVEL_FACTOR
        zlevel = int(kwargs.pop("zlevel")) if "zlevel" in kwargs else 0
        logger.debug(
            "zfactor=%f, zlevel=%d, is_projected=%s",
            zfactor,
            zlevel,
            self.crs.is_projected,
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
                lonlat = to_xy0(mesh, closed_interval=True)
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
                    logger.debug(
                        "delta=%f, zfactor=%f, zlevel=%d", delta, zfactor, zlevel
                    )
                logger.debug("zoffset=%f", zoffset)
                mesh.points[:, 2] = zoffset

        return super().add_mesh(mesh, **kwargs)


class GeoBackgroundPlotter(GeoPlotterBase, pvqt.BackgroundPlotter):
    pass


class GeoMultiPlotter(GeoPlotterBase, pvqt.MultiPlotter):
    pass


class GeoPlotter(GeoPlotterBase, pv.Plotter):
    pass
