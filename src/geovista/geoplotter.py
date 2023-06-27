"""Provide specialisation to support a geospatial aware plotter.

See :class:`pyvista.Plotter`.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Union
from warnings import warn

from pyproj import CRS, Transformer
import pyvista as pv
import vtk

from .common import (
    GV_FIELD_ZSCALE,
    LRU_CACHE_SIZE,
    RADIUS,
    ZLEVEL_SCALE,
    distance,
    from_cartesian,
    point_cloud,
)
from .common import cast_UnstructuredGrid_to_PolyData as cast
from .core import add_texture_coords, cut_along_meridian, resize
from .crs import WGS84, from_wkt, get_central_meridian, set_central_meridian
from .geometry import coastlines
from .raster import wrap_texture
from .samples import lfric

__all__ = ["GeoPlotter"]

# type aliases
CRSLike = Union[int, str, dict, CRS]

#: Proportional multiplier for z-axis levels/offsets of base-layer mesh.
BASE_ZLEVEL_SCALE: int = 1.0e-3


@lru_cache(maxsize=LRU_CACHE_SIZE)
def _get_lfric(
    resolution: str | None = None,
    radius: float | None = None,
) -> pv.PolyData:
    """Retrieve the LFRic unstructured cubed-sphere from the geovista cache.

    Parameters
    ----------
    resolution : str, optional
        The resolution of the LFRic unstructured cubed-sphere. Defaults to
        :data:`geovista.samples.LFRIC_RESOLUTION`.
    radius : float, optional
        The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.

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
    """Base class with common behaviour for a geospatial aware plotter.

    See :class:`pyvista.Plotter`.

    Notes
    -----
    .. versionadded:: 0.1.0

    """

    def __init__(self, *args: Any | None, **kwargs: Any | None):
        """Create geospatial aware plotter.

        Parameters
        ----------
        crs : str or CRS, optional
            The target CRS to render geolocated meshes added to the plotter.
        **kwargs : dict, optional
            See :class:`pyvista.Plotter` for further details.

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
                warn(wmsg, stacklevel=2)
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
        self, mesh: pv.PolyData | None = None, **kwargs: Any | None
    ) -> vtk.vtkActor:
        """Generate a cube-sphere base layer mesh and add to the plotter scene.

        Optionally, a `mesh` may be provided, which better fits the
        geometry of the surface mesh.

        Parameters
        ----------
        mesh : PolyData, optional
            Use the provided mesh as the base layer.
        radius : float, optional
            The radius of the spherical mesh to generate as the base layer. Defaults
            to :data:`geovista.common.RADIUS`.
        resolution : str, optional
            The resolution of the cube-sphere to generate as the base layer,
            which may be either ``c48``, ``c96`` or ``c192``. Defaults to
            :data:`geovista.samples.LFRIC_RESOLUTION`.
        zlevel : int, default=-1
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        **kwargs : dict, optional
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
            # pass-through "zlevel" and "zscale" to the "add_mesh" method,
            # but remove "radius", as it's not applicable to planar projections
            if "radius" in kwargs:
                _ = kwargs.pop("radius")
            # opt to the default radius for the base layer mesh
            radius = None
            if "zscale" not in kwargs:
                kwargs["zscale"] = BASE_ZLEVEL_SCALE
            if "zlevel" not in kwargs:
                kwargs["zlevel"] = -1
        else:
            radius = abs(float(kwargs.pop("radius"))) if "radius" in kwargs else RADIUS
            zscale = (
                float(kwargs.pop("zscale")) if "zscale" in kwargs else BASE_ZLEVEL_SCALE
            )
            zlevel = int(kwargs.pop("zlevel")) if "zlevel" in kwargs else -1
            radius += radius * zlevel * zscale

        if mesh is not None:
            if radius is not None:
                mesh = resize(mesh, radius=radius)
        else:
            mesh = _get_lfric(resolution=resolution, radius=radius)

        actor = self.add_mesh(mesh, **kwargs)

        return actor

    def add_coastlines(
        self,
        resolution: str | None = None,
        radius: float | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        **kwargs: Any | None,
    ) -> vtk.vtkActor:
        """Generate coastlines and add to the plotter scene.

        Parameters
        ----------
        resolution : str, optional
            The resolution of the Natural Earth coastlines, which may be either
            ``110m``, ``50m``, or ``10m``. Defaults to
            :data:`geovista.common.COASTLINES_RESOLUTION`.
        radius : float, optional
            The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
        zlevel : int, default=1
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        **kwargs : dict, optional
            See :meth:`pyvista.Plotter.add_mesh`.

        Returns
        -------
        vtkActor
            The rendered actor added to the plotter scene.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        mesh = coastlines(
            resolution=resolution, radius=radius, zlevel=zlevel, zscale=zscale
        )
        return self.add_mesh(mesh, **kwargs)

    def add_mesh(self, mesh: Any, **kwargs: Any | None):
        """Add the mesh to the plotter scene.

        See :meth:`pyvista.Plotter.add_mesh`.

        Parameters
        ----------
        mesh : PolyData
            The mesh to add to the plotter.
        atol : float, optional
            The absolute tolerance for values close to longitudinal
            :func:`geovista.common.wrap` base + period.
        rtol : float, optional
            The relative tolerance for values close to longitudinal
            :func:`geovista.common.wrap` base + period.
        zlevel : int, default=0
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        **kwargs : dict, optional
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
            tgt_crs = self.crs
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
                cut_mesh = cut_along_meridian(
                    mesh, antimeridian=True, rtol=rtol, atol=atol
                )
                if meridian:
                    # undo rotation
                    mesh.rotate_z(meridian, inplace=True)
                mesh = cut_mesh

            if "texture" in kwargs and kwargs["texture"] is not None:
                mesh = add_texture_coords(mesh, antimeridian=True)
                texture = wrap_texture(kwargs["texture"], central_meridian=meridian)
                kwargs["texture"] = texture

            if project:
                lonlat = from_cartesian(
                    mesh, closed_interval=True, rtol=rtol, atol=atol
                )
                transformer = Transformer.from_crs(src_crs, tgt_crs, always_xy=True)
                xs, ys = transformer.transform(
                    lonlat[:, 0], lonlat[:, 1], errcheck=True
                )
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

        return super().add_mesh(mesh, **kwargs)


class GeoPlotter(GeoPlotterBase, pv.Plotter):
    """A geospatial aware plotter.

    See :class:`geovista.geoplotter.GeoPlotterBase` and
    :class:`pyvista.Plotter`.

    """
