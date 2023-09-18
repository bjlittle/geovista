"""Provide specialisation to support a geospatial aware plotter.

See :class:`pyvista.Plotter`.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

from functools import lru_cache
from typing import Any
from warnings import warn

import numpy.typing as npt
from pyproj import CRS
import pyvista as pv
import pyvista.core.utilities.helpers as helpers

from .bridge import Transform
from .common import (
    GV_FIELD_ZSCALE,
    GV_REMESH_POINT_IDS,
    LRU_CACHE_SIZE,
    RADIUS,
    REMESH_SEAM,
    ZLEVEL_SCALE,
    ZTRANSFORM_FACTOR,
    distance,
    point_cloud,
    to_cartesian,
)
from .common import cast_UnstructuredGrid_to_PolyData as cast
from .core import add_texture_coords, resize, slice_mesh
from .crs import (
    WGS84,
    CRSLike,
    from_wkt,
    get_central_meridian,
    has_wkt,
    projected,
    set_central_meridian,
    to_wkt,
)
from .geometry import coastlines
from .gridlines import (
    GRATICULE_ZLEVEL,
    GraticuleGrid,
    create_meridians,
    create_parallels,
)
from .raster import wrap_texture
from .samples import LFRIC_RESOLUTION, REGULAR_RESOLUTION, lfric, regular_grid
from .transform import transform_mesh

__all__ = ["GeoPlotter"]

#: The valid 'style' options for adding points.
ADD_POINTS_STYLE: list[str, ...] = ["points", "points_gaussian"]

#: Proportional multiplier for z-axis levels/offsets of base-layer mesh.
BASE_ZLEVEL_SCALE: int = 1.0e-3

#: Coastlines relative tolerance for values close to longitudinal wrap base + period.
COASTLINES_RTOL: float = 1.0e-8

#: The default font size for graticule labels.
GRATICULE_LABEL_FONT_SIZE: int = 9

#: Whether to rendering graticule labels by default.
GRATICULE_SHOW_LABELS: bool = True

#: Known GPU renderer and version combinations that don't support opacity.
OPACITY_BLACKLIST = [
    ("llvmpipe (LLVM 7.0, 256 bits)", "3.3 (Core Profile) Mesa 18.3.4"),
]


@lru_cache(maxsize=LRU_CACHE_SIZE)
def _lfric_mesh(
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

    def __init__(self, *args: Any | None, **kwargs: Any | None) -> None:
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
        # status of gpu opacity support
        self._missing_opacity = False
        super().__init__(*args, **kwargs)

    def _add_graticule_labels(
        self,
        graticule: GraticuleGrid,
        radius: float | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        point_labels_args: dict[Any, Any] | None = None,
    ) -> None:
        """Render the labels for the given parallels/meridians.

        Parameters
        ----------
        graticule : GraticuleGrid
            The labels and associated lon/lat points for the graticule
            parallels/meridians.
        radius : float, optional
            The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        point_labels_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_point_labels`.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        if zlevel is None:
            zlevel = GRATICULE_ZLEVEL

        if point_labels_args is None:
            point_labels_args = {}

        lonlat = graticule.lonlat
        xyz = to_cartesian(
            lonlat[:, 0], lonlat[:, 1], radius=radius, zlevel=zlevel, zscale=zscale
        )

        mesh = pv.PolyData(xyz)

        if graticule.mask is not None:
            mask = graticule.mask * REMESH_SEAM
            mesh.point_data[GV_REMESH_POINT_IDS] = mask
            mesh.set_active_scalars(name=None)

        to_wkt(mesh, WGS84)
        # the point-cloud won't be sliced, however it's important that the
        # central-meridian rotation is performed here
        mesh = transform_mesh(mesh, self.crs, zlevel=zlevel, inplace=True)
        xyz = mesh.points

        if "show_points" in point_labels_args:
            _ = point_labels_args.pop("show_points")

        if "font_size" not in point_labels_args:
            point_labels_args["font_size"] = GRATICULE_LABEL_FONT_SIZE

        # labels over-plot points, therefore enforce non-rendering of points,
        # which is more efficient
        point_labels_args["show_points"] = False
        # opinionated over-ride to disable label visibility filter
        point_labels_args["always_visible"] = False

        self.add_point_labels(xyz, graticule.labels, **point_labels_args)

    def _warn_opacity(self) -> None:
        """Add textual warning for no opacity support to plotter scene.

        Convenience for adding a text warning to the render scene for known GPU
        configurations that don't support opacity.

        Notes
        -----
        .. versionadded:: 0.4.0

        """
        if not self._missing_opacity:
            info = pv.GPUInfo()
            renderer_version = info.renderer, info.version

            if renderer_version in OPACITY_BLACKLIST:
                self.add_text(
                    "Requires GPU opacity support",
                    position="lower_right",
                    font_size=7,
                    color="red",
                    shadow=True,
                )
                self._missing_opacity = True

    def add_base_layer(
        self, mesh: pv.PolyData | None = None, **kwargs: Any | None
    ) -> pv.Actor:
        """Generate a cubed-sphere base layer mesh and add to the plotter scene.

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
            The resolution of the cubed-sphere to generate as the base layer,
            which may be either ``c48``, ``c96`` or ``c192``. Defaults to
            :data:`geovista.samples.LFRIC_RESOLUTION`. Alternatively, generate a
            regular grid using a format of ``rN``, where ``N`` is the number of cells
            in latitude, and ``N * 1.5`` cells in longitude. When adding a base layer
            to a projection, the default is to use a regular grid with resolution
            :data:`REGULAR_RESOLUTION`.
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
        Actor
            The rendered actor added to the plotter scene.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        resolution = kwargs.pop("resolution") if "resolution" in kwargs else None

        if resolution is None:
            resolution = (
                REGULAR_RESOLUTION if self.crs.is_projected else LFRIC_RESOLUTION
            )
        else:
            resolution = str(resolution)

        if self.crs.is_projected:
            # pass through "zlevel" and "zscale" to the "add_mesh" method,
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
            if resolution.startswith("r"):
                mesh = regular_grid(resolution=resolution, radius=radius)
            else:
                mesh = _lfric_mesh(resolution=resolution, radius=radius)

        actor = self.add_mesh(mesh, **kwargs)

        return actor

    def add_coastlines(
        self,
        resolution: str | None = None,
        radius: float | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        rtol: float | None = None,
        atol: float | None = None,
        **kwargs: Any | None,
    ) -> pv.Actor:
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
        rtol : float, optional
            The relative tolerance for values close to longitudinal
            :func:`geovista.common.wrap` base + period.
        atol : float, optional
            The absolute tolerance for values close to longitudinal
            :func:`geovista.common.wrap` base + period.
        **kwargs : dict, optional
            See :meth:`pyvista.Plotter.add_mesh`.

        Returns
        -------
        Actor
            The rendered actor added to the plotter scene.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if self.crs.is_projected:
            # don't pass through "radius", as it's not applicable
            if rtol is None:
                rtol = COASTLINES_RTOL
            if zscale is None:
                zscale = ZLEVEL_SCALE
            if zlevel is None:
                zlevel = ZTRANSFORM_FACTOR
            # pass through kwargs to "add_mesh"
            kwargs.update({"zlevel": zlevel, "zscale": zscale})

        mesh = coastlines(
            resolution=resolution, radius=radius, zlevel=zlevel, zscale=zscale
        )

        if rtol is not None:
            kwargs["rtol"] = rtol

        if atol is not None:
            kwargs["atol"] = atol

        actor = self.add_mesh(mesh, **kwargs)

        return actor

    def add_graticule(
        self,
        lon_start: float | None = None,
        lon_stop: float | None = None,
        lon_step: float | None = None,
        lat_start: float | None = None,
        lat_step: float | None = None,
        lat_stop: float | None = None,
        poles_parallel: bool | None = None,
        poles_label: bool | None = None,
        show_labels: bool | None = None,
        radius: float | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        mesh_args: dict[Any, Any] | None = None,
        point_labels_args: dict[Any, Any] | None = None,
    ) -> None:
        """Generate a graticule and add to the plotter scene.

        This involves generating lines of constant latitude (parallels) and
        lines of constant longitude (meridians), which together form the graticule.

        Parameters
        ----------
        lon_start : float, optional
            The first line of longitude (degrees). The graticule will include this
            meridian. Defaults to :data:`geovista.gridlines.LONGITUDE_START`.
        lon_stop : float, optional
            The last line of longitude (degrees). The graticule will include this
            meridian when it is a multiple of `lon_step`. Also see
            ``closed_interval``. Defaults to :data:`geovista.gridlines.LONGITUDE_STOP`.
        lon_step : float, optional
            The delta (degrees) between neighbouring meridians. Defaults to
            :data:`geovista.gridlines.LONGITUDE_STEP`.
        lat_start : float, optional
            The first line of latitude (degrees). The graticule will include this
            parallel. Also see `poles_parallel`. Defaults to
            :data:`geovista.gridlines.LATITUDE_START`.
        lat_stop : float, optional
            The last line of latitude (degrees). The graticule will include this
            parallel when it is a multiple of `lat_step`. Defaults to
            :data:`geovista.gridlines.LATITUDE_STOP`.
        lat_step : float, optional
            The delta (degrees) between neighbouring parallels. Defaults to
            :data:`geovista.gridlines.LATITUDE_STEP`.
        poles_parallel : bool, optional
            Whether to create a line of latitude at the north/south poles. Defaults to
            :data:`geovista.gridlines.LATITUDE_POLES_PARALLEL`.
        poles_label : bool, optional
            Whether to create a single north/south pole label. Only applies when
            ``poles_parallel=False``. Defaults to
            :data:`geovista.gridlines.LATITUDE_POLES_LABEL`.
        show_labels : bool, optional
            Whether to render the labels of the parallels and meridians. Defaults to
            :data:`GRATICULE_SHOW_LABELS`.
        radius : float, optional
            The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        mesh_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_mesh`.
        point_labels_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_point_labels`.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        self.add_meridians(
            start=lon_start,
            stop=lon_stop,
            step=lon_step,
            lat_step=lat_step,
            show_labels=show_labels,
            radius=radius,
            zlevel=zlevel,
            zscale=zscale,
            mesh_args=mesh_args,
            point_labels_args=point_labels_args,
        )
        self.add_parallels(
            start=lat_start,
            stop=lat_stop,
            step=lat_step,
            lon_step=lon_step,
            poles_parallel=poles_parallel,
            poles_label=poles_label,
            show_labels=show_labels,
            radius=radius,
            zlevel=zlevel,
            zscale=zscale,
            mesh_args=mesh_args,
            point_labels_args=point_labels_args,
        )

    def add_mesh(self, mesh: Any, **kwargs: Any | None) -> pv.Actor:
        """Add the `mesh` to the plotter scene.

        See :meth:`pyvista.Plotter.add_mesh`.

        Parameters
        ----------
        mesh : PolyData
            The mesh to add to the plotter.
        rtol : float, optional
            The relative tolerance for values close to longitudinal
            :func:`geovista.common.wrap` base + period.
        atol : float, optional
            The absolute tolerance for values close to longitudinal
            :func:`geovista.common.wrap` base + period.
        radius : float, optional
            The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
        zlevel : int or ArrayLike, default=0
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius`/vertical by a proportional amount e.g.,
            ``radius * zlevel * zscale``. If `zlevel` is not a scalar, then its shape
            must match or broadcast with the shape of the ``mesh.points``.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        **kwargs : dict, optional
            See :meth:`pyvista.Plotter.add_mesh`.

        Returns
        -------
        Actor
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

            if src_crs is None:
                wmsg = "Found no coordinate reference system (CRS) attached to mesh."
                warn(wmsg, stacklevel=2)

            tgt_crs = self.crs
            transform_required = src_crs and src_crs != tgt_crs
            central_meridian = get_central_meridian(tgt_crs) or 0

            if transform_required and not cloud:
                if central_meridian:
                    mesh.rotate_z(-central_meridian, inplace=True)
                    tgt_crs = set_central_meridian(tgt_crs, 0)

                # the sliced_mesh is guaranteed to be a new instance,
                # even if not bisected
                sliced_mesh = slice_mesh(mesh, rtol=rtol, atol=atol)

                if central_meridian:
                    # undo rotation of original mesh
                    mesh.rotate_z(central_meridian, inplace=True)

                mesh = sliced_mesh

            if "texture" in kwargs and kwargs["texture"] is not None:
                mesh = add_texture_coords(mesh, antimeridian=True)
                texture = wrap_texture(
                    kwargs["texture"], central_meridian=central_meridian
                )
                kwargs["texture"] = texture

            if transform_required:
                mesh = transform_mesh(
                    mesh,
                    tgt_crs,
                    slice_connectivity=False,
                    rtol=rtol,
                    atol=atol,
                    zlevel=zlevel,
                    zscale=zscale,
                    inplace=not cloud,
                )
                to_wkt(mesh, self.crs)
            else:
                if not projected(mesh) and zlevel:
                    if not cloud:
                        radius = distance(mesh)

                    mesh = resize(mesh, radius=radius, zlevel=zlevel, zscale=zscale)

        def _check(option: str) -> bool:
            return option in kwargs and kwargs[option] is not None

        if not self._missing_opacity and (_check("opacity") or _check("nan_opacity")):
            self._warn_opacity()

        return super().add_mesh(mesh, **kwargs)

    def add_meridian(
        self,
        lon: float,
        lat_step: float | None = None,
        n_samples: int | None = None,
        show_labels: bool | None = None,
        radius: float | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        mesh_args: dict[Any, Any] | None = None,
        point_labels_args: dict[Any, Any] | None = None,
    ) -> None:
        """Generate a line of constant longitude and add to the plotter scene.

        Parameters
        ----------
        lon : float
            The constant line of longitude (degrees) to generate.
        lat_step : float, optional
            The delta (degrees) between neighbouring parallels. Defaults to
            :data:`geovista.gridlines.LATITUDE_STEP`.
        n_samples : int, optional
            The number of points in a single line of longitude. Defaults to
            :data:`geovista.gridlines.LONGITUDE_N_SAMPLES`.
        show_labels : bool, optional
            Whether to render the meridian label. Defaults to
            :data:`GRATICULE_SHOW_LABELS`.
        radius : float, optional
            The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        mesh_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_mesh`.
        point_labels_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_point_labels`.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        self.add_meridians(
            start=lon,
            stop=lon,
            lat_step=lat_step,
            n_samples=n_samples,
            show_labels=show_labels,
            radius=radius,
            zlevel=zlevel,
            zscale=zscale,
            mesh_args=mesh_args,
            point_labels_args=point_labels_args,
        )

    def add_meridians(
        self,
        start: float | None = None,
        stop: float | None = None,
        step: float | None = None,
        lat_step: float | None = None,
        n_samples: int | None = None,
        show_labels: bool | None = None,
        radius: float | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        mesh_args: dict[Any, Any] | None = None,
        point_labels_args: dict[Any, Any] | None = None,
    ) -> None:
        """Generate lines of constant longitude and add to the plotter scene.

        Parameters
        ----------
        start : float, optional
            The first line of longitude (degrees). The graticule will include this
            meridian. Defaults to :data:`geovista.gridlines.LONGITUDE_START`.
        stop : float, optional
            The last line of longitude (degrees). The graticule will include this
            meridian when it is a multiple of `step`. Also see ``closed_interval``.
            Defaults to :data:`geovista.gridlines.LONGITUDE_STOP`.
        step : float, optional
            The delta (degrees) between neighbouring meridians. Defaults to
            :data:`geovista.gridlines.LONGITUDE_STEP`.
        lat_step : float, optional
            The delta (degrees) between neighbouring parallels. Defaults to
            :data:`geovista.gridlines.LATITUDE_STEP`.
        n_samples : int, optional
            The number of points in a single line of longitude. Defaults to
            :data:`geovista.gridlines.LONGITUDE_N_SAMPLES`.
        show_labels : bool, optional
            Whether to render the labels of the meridians. Defaults to
            :data:`GRATICULE_SHOW_LABELS`.
        radius : float, optional
            The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        mesh_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_mesh`.
        point_labels_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_point_labels`.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        if show_labels is None:
            show_labels = GRATICULE_SHOW_LABELS

        if zlevel is None:
            zlevel = ZTRANSFORM_FACTOR if self.crs.is_projected else GRATICULE_ZLEVEL

        if mesh_args is None:
            mesh_args = {}

        if point_labels_args is None:
            point_labels_args = {}

        closed_interval = self.crs.is_projected
        central_meridian = get_central_meridian(self.crs)

        meridians = create_meridians(
            start=start,
            stop=stop,
            step=step,
            lat_step=lat_step,
            n_samples=n_samples,
            closed_interval=closed_interval,
            central_meridian=central_meridian,
            radius=radius,
            zlevel=zlevel,
            zscale=zscale,
        )

        if radius is not None:
            mesh_args["radius"] = radius

        if zlevel is not None:
            mesh_args["zlevel"] = zlevel

        if zscale is not None:
            mesh_args["zscale"] = zscale

        for mesh in meridians.blocks:
            self.add_mesh(mesh, **mesh_args)

        if show_labels:
            self._add_graticule_labels(
                meridians,
                radius=radius,
                zlevel=zlevel,
                zscale=zscale,
                point_labels_args=point_labels_args,
            )

    def add_parallel(
        self,
        lat: float,
        lon_step: float | None = None,
        n_samples: int | None = None,
        poles_parallel: bool | None = None,
        show_labels: bool | None = None,
        radius: float | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        mesh_args: dict[Any, Any] | None = None,
        point_labels_args: dict[Any, Any] | None = None,
    ) -> None:
        """Generate a line of constant latitude and add to the plotter scene.

        Parameters
        ----------
        lat : float
            The constant line of latitude (degrees) to generate.
        lon_step : float, optional
            The delta (degrees) between neighbouring meridians. Defaults to
            :data:`geovista.gridlines.LONGITUDE_STEP`.
        n_samples : int, optional
            The number of points in a single line of latitude. Defaults to
            :data:`geovista.gridlines.LATITUDE_N_SAMPLES`.
        poles_parallel : bool, optional
            Whether to create a line of latitude at the north/south poles. Defaults to
            :data:`geovista.gridlines.LATITUDE_POLES_PARALLEL`.
        show_labels : bool, optional
            Whether to render the parallel label. Defaults to
            :data:`GRATICULE_SHOW_LABELS`.
        radius : float, optional
            The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        mesh_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_mesh`.
        point_labels_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_point_labels`.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        self.add_parallels(
            start=lat,
            stop=lat,
            lon_step=lon_step,
            n_samples=n_samples,
            poles_parallel=poles_parallel,
            show_labels=show_labels,
            radius=radius,
            zlevel=zlevel,
            zscale=zscale,
            mesh_args=mesh_args,
            point_labels_args=point_labels_args,
        )

    def add_parallels(
        self,
        start: float | None = None,
        stop: float | None = None,
        step: float | None = None,
        lon_step: float | None = None,
        n_samples: int | None = None,
        poles_parallel: bool | None = None,
        poles_label: bool | None = None,
        show_labels: bool | None = None,
        radius: float | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        mesh_args: dict[Any, Any] | None = None,
        point_labels_args: dict[Any, Any] | None = None,
    ) -> None:
        """Generate lines of constant latitude and add to the plotter scene.

        Parameters
        ----------
        start : float, optional
            The first line of latitude (degrees). The graticule will include this
            parallel. Also see `poles_parallel`. Defaults to
            :data:`geovista.gridlines.LATITUDE_START`.
        stop : float, optional
            The last line of latitude (degrees). The graticule will include this
            parallel when it is a multiple of `step`. Also see `poles_parallel`.
            Defaults to :data:`geovista.gridlines.LATITUDE_STOP`.
        step : float, optional
            The delta (degrees) between neighbouring parallels. Defaults to
            :data:`geovista.gridlines.LATITUDE_STEP`.
        lon_step : float, optional
            The delta (degrees) between neighbouring meridians. Defaults to
            :data:`geovista.gridlines.LONGITUDE_STEP`.
        n_samples : int, optional
            The number of points in a single line of latitude. Defaults to
            :data:`geovista.gridlines.LATITUDE_N_SAMPLES`.
        poles_parallel : bool, optional
            Whether to create a line of latitude at the north/south poles. Defaults to
            :data:`geovista.gridlines.LATITUDE_POLES_PARALLEL`.
        poles_label : bool, optional
            Whether to create a single north/south pole label. Only applies when
            ``poles_parallel=False``. Defaults to
            :data:`geovista.gridlines.LATITUDE_POLES_LABEL`.
        show_labels : bool, optional
            Whether to render the labels of the parallels. Defaults to
            :data:`GRATICULE_SHOW_LABELS`.
        radius : float, optional
            The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        mesh_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_mesh`.
        point_labels_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_point_labels`.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        if show_labels is None:
            show_labels = GRATICULE_SHOW_LABELS

        if zlevel is None:
            zlevel = ZTRANSFORM_FACTOR if self.crs.is_projected else GRATICULE_ZLEVEL

        if mesh_args is None:
            mesh_args = {}

        if point_labels_args is None:
            point_labels_args = {}

        # TODO: fix behaviour of longitudes at poles
        poles_parallel = False

        parallels = create_parallels(
            start=start,
            stop=stop,
            step=step,
            lon_step=lon_step,
            n_samples=n_samples,
            poles_parallel=poles_parallel,
            poles_label=poles_label,
            radius=radius,
            zlevel=zlevel,
            zscale=zscale,
        )

        if radius is not None:
            mesh_args["radius"] = radius

        if zlevel is not None:
            mesh_args["zlevel"] = zlevel

        if zscale is not None:
            mesh_args["zscale"] = zscale

        for mesh in parallels.blocks:
            self.add_mesh(mesh, **mesh_args)

        if show_labels:
            self._add_graticule_labels(
                parallels,
                radius=radius,
                zlevel=zlevel,
                zscale=zscale,
                point_labels_args=point_labels_args,
            )

    def add_points(
        self,
        points: npt.ArrayLike | pv.PolyData | None = None,
        xs: npt.ArrayLike | None = None,
        ys: npt.ArrayLike | None = None,
        scalars: str | npt.ArrayLike | None = None,
        crs: CRSLike | None = None,
        radius: float | None = None,
        style: str | None = None,
        zlevel: int | npt.ArrayLike | None = None,
        zscale: float | None = None,
        **kwargs: Any | None,
    ) -> pv.Actor:
        """Add points to the plotter scene.

        See :meth:`pyvista.Plotter.add_mesh`.

        Parameters
        ----------
        points : ArrayLike or PolyData, optional
            Array of xyz points, in canonical `crs` units, or the points of the mesh
            to be rendered.
        xs : ArrayLike, optional
            A 1-D, 2-D or 3-D array of point-cloud x-values, in canonical `crs` units.
            Must have the same shape as the `ys`.
        ys : ys : ArrayLike
            A 1-D, 2-D or 3-D array of point-cloud y-values, in canonical `crs` units.
            Must have the same shape as the `xs`.
        scalars : str or ArrayLike, optional
            Values used to color the points. Either, the string name of an array that is
            present on the `points` mesh or an array equal to the number of points.
            Alternatively, an array of values equal to the number of points to be
            rendered. If both `color` and `scalars` are ``None``, then the active
            scalars on the `points` mesh are used.
        crs : CRSLike, optional
            The Coordinate Reference System of the provided `points`, or `xs` and `ys`.
            May be anything accepted by :meth:`pyproj.CRS.from_user_input`. Defaults
            to ``EPSG:4326`` i.e., ``WGS 84``.
        radius : float, optional
            The radius of the mesh point-cloud. Defaults to
            :data:`geovista.common.RADIUS`.
        style : str, optional
            Visualization style of the points to be rendered. Maybe either ``points``
            or ``points_gaussian``. The ``points_gaussian`` option maybe controlled
            with the ``emissive`` and ``render_points_as_spheres`` options.
        zlevel : int or ArrayLike, default=0
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
            If `zlevel` is not a scalar, then its shape must match or broadcast
            with the shape of the `xs` and `ys`.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        **kwargs : dict, optional
            See :meth:`pyvista.Plotter.add_mesh`.

        Returns
        -------
        Actor
            The rendered actor added to the plotter scene.

        Notes
        -----
        .. versionadded:: 0.4.0

        """
        if crs is not None:
            # sanity check the source crs
            crs = CRS.from_user_input(crs)

        if style is None:
            style = "points"

        if style not in ADD_POINTS_STYLE:
            options = "or ".join(f"{option!r}" for option in ADD_POINTS_STYLE)
            emsg = (
                f"Invalid 'style' for 'add_points', expected {options}, "
                f"got {style!r}."
            )
            raise ValueError(emsg)

        if points is None and xs is None and ys is None:
            emsg = (
                "Require either 'points' or both 'xs' and 'ys' to be specified, "
                "got neither."
            )
            raise ValueError(emsg)

        if points is not None and xs is not None and ys is not None:
            emsg = (
                "Require either 'points' or both 'xs' and 'ys' to be specified, "
                "got both 'points', and 'xs' and 'ys'."
            )
            raise ValueError(emsg)

        if points is not None:
            if xs is not None or ys is not None:
                emsg = (
                    "Require either 'points' or both 'xs' and 'ys' to be specified, "
                    "got both 'points', and 'xs' or 'ys'."
                )
                raise ValueError(emsg)

            if not helpers.is_pyvista_dataset(points):
                points = helpers.wrap(points)

            mesh = points

            if crs is not None:
                if has_wkt(mesh):
                    other = from_wkt(mesh)
                    if other != crs:
                        emsg = (
                            "The CRS serialized as WKT on the 'points' mesh does not "
                            "match the provided 'crs'."
                        )
                        raise ValueError(emsg)
                else:
                    # serialize the provided CRS on the points mesh as wkt
                    to_wkt(mesh, crs)
            elif not has_wkt(mesh):
                # assume CRS is WGS84
                to_wkt(mesh, WGS84)
        else:
            if xs is None or ys is None:
                emsg = (
                    "Require either 'points', or both 'xs' and 'ys' to be specified, "
                    "got only 'xs' or 'ys'."
                )
                raise ValueError(emsg)

            if isinstance(scalars, str):
                wmsg = (
                    f"Ignoring the 'scalars' string name '{scalars}', as no 'points' "
                    "mesh was provided."
                )
                warn(wmsg, stacklevel=2)

            mesh = Transform.from_points(
                xs=xs,
                ys=ys,
                crs=crs,
                radius=radius,
                zlevel=zlevel,
                zscale=zscale,
            )

        # defensive kwarg pop
        if "texture" in kwargs:
            _ = kwargs.pop("texture")

        return self.add_mesh(mesh, style=style, scalars=scalars, **kwargs)


class GeoPlotter(GeoPlotterBase, pv.Plotter):
    """A geospatial aware plotter.

    See :class:`geovista.geoplotter.GeoPlotterBase` and
    :class:`pyvista.Plotter`.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
