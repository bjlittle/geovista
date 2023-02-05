"""
This module provides behaviour specialisation to support a geospatial aware
:class:`pyvista.Plotter`.

Notes
-----
.. versionadded:: 0.1.0

"""
# pylint: disable=no-member
from functools import lru_cache
from typing import Any, Optional, Union
from warnings import warn

from pyproj import CRS, Transformer
import pyvista as pv
import pyvistaqt as pvqt
import vtk

from .common import RADIUS, ZLEVEL_FACTOR, to_xy0
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
    Retrieve the LFRic unstructured cubed-sphere from the geovista cache.

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
        mesh = resize(mesh, radius=radius)

    mesh.set_active_scalars(name=None)

    return mesh


class GeoPlotterBase:
    """
    Base class with common behaviour for a geospatial aware :class:`pyvista.Plotter`.

    Notes
    -----
    .. versionadded:: 0.1.0

    """

    def __init__(self, *args: Optional[Any], **kwargs: Optional[Any]):
        """

        Parameters
        ----------
        crs : str or CRS, optional
            The target CRS to render the geo-located meshes added to the
            plotter.
        kwargs : any, optional
            See :class:`pyvista.Plotter`.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
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
        Generate a cube-sphere base layer mesh and add to the plotter scene.

        Optionally, a `mesh` may be provided, which better fits the
        geometry of the surface mesh.

        Parameters
        ----------
        mesh : PolyData, optional
            Use the provided mesh as the base layer.
        radius : float, optional
            The radius of the spherical mesh to generate as the base layer.
        resolution : str, default="c96"
            The resolution of the cube-sphere to generate as the base layer,
            which may be either ``c48``, ``c96`` or ``c192``.
        zfactor : float, optional
            The magnitude factor for z-axis levels (`zlevel`). Defaults to
            :data:`geovista.common.ZLEVEL_FACTOR`.
        zlevel : float, optional
            The z-axis level. Used in combination with the `zfactor` to offset
            the base layer from the surface by the proportional amount of
            ``zlevel * zfactor``.
        kwargs : any, optional
            See :meth:`pyvista.Plotter.add_mesh`.

        Returns
        -------
        vtkActor
            The rendered actor added to the plotter scene.

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
        Generate coastlines and add to the plotter scene.

        Parameters
        ----------
        resolution : str, default="10m"
            The resolution of the Natural Earth coastlines.
        kwargs : any, optional
            See :meth:`pyvista.Plotter.add_mesh`.

        Returns
        -------
        vtkActor
            The rendered actor added to the plotter scene.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        mesh = get_coastlines(resolution=resolution)
        return self.add_mesh(mesh, **kwargs)

    def add_mesh(self, mesh: Any, **kwargs: Optional[Any]):
        """
        Add the mesh to the plotter scene.

        Parameters
        ----------
        mesh : PolyData
            The mesh to add to the plotter.
        atol : float, optional
            The absolute tolerance for values close to longitudinal
            :func:`geovista.common.wrap` base + period.
        radius : float, optional
            The radius of the spherical mesh. Used to confirm the radius of
            the spherical mesh when projecting to the target CRS. Otherwise,
            the radius will be calculated.
        rtol : float, optional
            The relative tolerance for values close to longitudinal
            :func:`geovista.common.wrap base + period.
        zfactor : float, optional
            The magnitude factor for z-axis levels (`zlevel`). Defaults to
            :data:`geovista.common.ZLEVEL_FACTOR`.
        zlevel : float, optional
            The z-axis level. Used in combination with the `zfactor` to offset
            the projected surface by the proportional amount of
            ``zlevel * zfactor``.
        kwargs : any, optional
            See :meth:`pyvista.Plotter.add_mesh`.

        Returns
        -------
        vtkActor
            The rendered actor added to the plotter scene.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if isinstance(mesh, pv.UnstructuredGrid):
            mesh = cast(mesh)

        if isinstance(mesh, pv.PolyData):
            atol = float(kwargs.pop("atol")) if "atol" in kwargs else None
            radius = float(kwargs.pop("radius")) if "radius" in kwargs else None
            rtol = float(kwargs.pop("rtol")) if "rtol" in kwargs else None
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
                    cut_mesh = cut_along_meridian(
                        mesh, antimeridian=True, rtol=rtol, atol=atol
                    )
                    # undo rotation
                    mesh.rotate_z(meridian, inplace=True)
                    mesh = cut_mesh
                except ValueError:
                    pass

            if "texture" in kwargs and kwargs["texture"] is not None:
                mesh = add_texture_coords(mesh, antimeridian=True)
                texture = wrap_texture(kwargs["texture"], central_meridian=meridian)
                kwargs["texture"] = texture

            if project:
                lonlat = to_xy0(
                    mesh, radius=radius, closed_interval=True, rtol=rtol, atol=atol
                )
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

    # def add_point_labels(
    #     self,
    #     points: Any,
    #     labels: Any,
    #     **kwargs: Optional[Any],
    # ) -> vtk.vtkActor2D:
    #     """
    #     TODO
    #
    #     Parameters
    #     ----------
    #     points :
    #     labels :
    #     kwargs : any, optional
    #         See :meth:`pyvista.Plotter.add_point_labels`.
    #
    #     Returns
    #     -------
    #     vtkActor2D
    #         The rendered actor added to the plotter scene.
    #
    #     Notes
    #     -----
    #     .. versionadded:: 0.1.0
    #
    #     """
    #     if isinstance(points, pv.PolyData):
    #         crs = from_wkt(points)
    #
    #         if crs is not None and crs != WGS84:
    #             lonlat = to_xy0(points)
    #             transformer = Transformer.from_crs(crs, self.crs, always_xy=True)
    #             xs, ys = transformer.transform(
    #                 lonlat[:, 0], lonlat[:, 1], errcheck=True
    #             )
    #             result = pv.PolyData()
    #             result.copy_structure(points)
    #             result.points[:, 0] = xs
    #             result.points[:, 1] = ys
    #             result.points[:, 2] = 0
    #             points = result
    #
    #     return super().add_point_labels(points, labels, **kwargs)
    #
    # def add_points(
    #     self,
    #     points: Optional[Any] = None,
    #     xs: Optional[ArrayLike] = None,
    #     ys: Optional[ArrayLike] = None,
    #     crs: Optional[CRSLike] = None,
    #     radius: Optional[float] = None,
    #     zfactor: Optional[float] = None,
    #     zlevel: Optional[int] = None,
    #     **kwargs: Optional[Any],
    # ) -> vtk.vtkActor:
    #     """
    #
    #
    #     """
    #     kwargs["style"] = "points"
    #
    #     if "texture" in kwargs:
    #         _ = kwargs.pop("texture")
    #
    #     if points is not None:
    #         if crs is not None:
    #             warn("Ignoring 'crs' as cartesian xyz 'points' have been provided.")
    #             crs = None
    #
    #     if crs is not None:
    #         if xs is None or ys is None:
    #             emsg = "Given a 'crs', both 'xs' and 'ys' require to be provided."
    #             raise ValueError(emsg)
    #
    #         xs = np.asanyarray(xs)
    #         ys = np.asanyarray(ys)
    #
    #         if xs.shape != ys.shape:
    #             emsg = (
    #                 "Require 'xs' and 'ys' with the same shape, got "
    #                 f"{xs.shape=} and {ys.shape}."
    #             )
    #             raise ValueError(emsg)
    #
    #         crs = CRS.from_user_input(crs)
    #
    #         if crs != WGS84:
    #             transformer = Transformer.from_crs(crs, WGS84, always_xy=True)
    #             xs, ys = transformer.transform(xs, ys, errcheck=True)
    #
    #         radius = RADIUS if radius is None else abs(radius)
    #
    #         if zfactor is None:
    #             zfactor = ZLEVEL_FACTOR
    #
    #         if zlevel is None:
    #             zlevel = 0
    #
    #         radius += radius * zlevel * zfactor
    #
    #         xyz = to_xyz(xs, ys, radius=radius)
    #         points = pv.PolyData(xyz)
    #         # attach the pyproj crs serialized as ogc wkt
    #         wkt = np.array([WGS84.to_wkt()])
    #         points.field_data[GV_FIELD_CRS] = wkt
    #         kwargs["radius"] = radius
    #         kwargs["zfactor"] = zfactor
    #         kwargs["zlevel"] = zlevel
    #
    #     return self.add_mesh(points, **kwargs)


class GeoBackgroundPlotter(GeoPlotterBase, pvqt.BackgroundPlotter):
    """
    See :class:`geovista.geoplotter.GeoPlotterBase` and
    :class:`pyvistaqt.BackgroundPlotter`.

    """


class GeoMultiPlotter(GeoPlotterBase, pvqt.MultiPlotter):
    """
    See :class:`geovista.geoplotter.GeoPlotterBase` and
    :class:`pyvistaqt.MultiPlotter`.

    """


class GeoPlotter(GeoPlotterBase, pv.Plotter):
    """
    See :class:`geovista.geoplotter.GeoPlotterBase` and
    :class:`pyvista.Plotter`.

    """
