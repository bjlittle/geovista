# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Provide specialisation to support a geospatial aware plotter.

See :class:`pyvista.Plotter`.

Notes
-----
.. versionadded:: 0.1.0

"""

from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache
import os
from typing import TYPE_CHECKING, Any
from warnings import warn

import lazy_loader as lazy

from .bridge import Transform
from .common import (
    GV_FIELD_ZSCALE,
    GV_POINT_IDS,
    GV_REMESH_POINT_IDS,
    LRU_CACHE_SIZE,
    RADIUS,
    REMESH_SEAM,
    ZLEVEL_SCALE,
    ZTRANSFORM_FACTOR,
    distance,
    point_cloud,
    to_cartesian,
    to_lonlat,
    vtk_warnings_off,
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
from .geodesic import BBox
from .geometry import coastlines
from .gridlines import (
    GRATICULE_ZLEVEL,
    GraticuleGrid,
    create_meridians,
    create_parallels,
)
from .pantry.meshes import (
    LFRIC_RESOLUTION,
    REGULAR_RESOLUTION,
    lfric,
    regular_grid,
)
from .raster import wrap_texture
from .transform import transform_mesh, transform_point

if TYPE_CHECKING:
    from collections.abc import Callable

    from numpy.typing import ArrayLike
    import pyvista as pv

    from geovista.crs import CRSLike

# lazy import third-party dependencies
np = lazy.load("numpy")
pyproj = lazy.load("pyproj")
pv = lazy.load("pyvista")

__all__ = [
    "ADD_POINTS_STYLE",
    "BASE_ZLEVEL_SCALE",
    "COASTLINES_RTOL",
    "GRATICULE_LABEL_FONT_SIZE",
    "GRATICULE_SHOW_LABELS",
    "OPACITY_BLACKLIST",
    "GeoPlotter",
    "GeoPlotterBase",
]

ADD_POINTS_STYLE: tuple[str, str] = ("points", "points_gaussian")
"""The valid 'style' options for adding points."""

BASE_ZLEVEL_SCALE: float = 1.0e-3
"""Proportional multiplier for z-axis levels/offsets of base-layer mesh."""

COASTLINES_RTOL: float = 1.0e-8
"""Coastlines relative tolerance for longitudes close to 'wrap meridian'."""

GRATICULE_LABEL_FONT_SIZE: int = 9
"""The default font size for graticule labels."""

GRATICULE_SHOW_LABELS: bool = True
"""Whether to render graticule labels by default."""

OPACITY_BLACKLIST = [
    ("llvmpipe (LLVM 7.0, 256 bits)", "3.3 (Core Profile) Mesa 18.3.4"),
]
"""Known GPU renderer and version combinations that don't support opacity."""


@lru_cache(maxsize=LRU_CACHE_SIZE)
def _lfric_mesh(
    *,
    resolution: str | None = None,
    radius: float | None = None,
) -> pv.PolyData:
    """Retrieve the LFRic unstructured cubed-sphere from the geovista cache.

    Parameters
    ----------
    resolution : str, optional
        The resolution of the LFRic unstructured cubed-sphere. Defaults to
        :data:`geovista.pantry.meshes.LFRIC_RESOLUTION`.
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


class GeoPlotterBase:  # numpydoc ignore=PR01
    """Base class with common behaviour for a geospatial aware plotter.

    See :class:`pyvista.Plotter`.

    Notes
    -----
    .. versionadded:: 0.1.0

    """

    def __init__(
        self,
        *args: Any | None,
        crs: CRSLike | None = None,
        manifold: BBox | None = None,
        **kwargs: Any | None,
    ) -> None:
        """Create geospatial aware plotter.

        Parameters
        ----------
        *args : tuple, optional
            See :class:`pyvista.Plotter` for further details.
        crs : CRSLike, optional
            The target CRS to render geolocated meshes added to the plotter.
            May be anything accepted by :meth:`pyproj.crs.CRS.from_user_input`.
            Defaults to ``EPSG:4326`` i.e., ``WGS 84``.
        manifold : BBox, optional
            Apply the `manifold` to each mesh added to the plotter so that only
            the region enclosed by the `manifold` is rendered.
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
                    f"geovista {klass} received an unexpected argument. "
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

        self.crs = pyproj.CRS.from_user_input(crs) if crs is not None else WGS84
        """The Coordinate Reference System (CRS) for the plotter."""

        # the manifold defining the AOI (area of interest) for geometries
        # added to the plotter i.e., sample extraction within its boundary
        self.manifold = manifold

        # status of gpu opacity support
        self._missing_opacity = False
        # cartesian (xyz) center of last mesh added to the plotter
        self._poi: list[float] | None = None
        super().__init__(*args, **kwargs)

    @property
    def manifold(self) -> BBox | None:
        """The manifold boundary applied to meshes added to the plotter.

        Returns
        -------
        BBox or None
            The plotter manifold.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        return self._manifold

    @manifold.setter
    def manifold(self, value: Any) -> None:
        """Set the manifold boundary applied to meshes added to the plotter.

        Parameters
        ----------
        value : BBox, optional
            The manifold boundary to apply to meshes added to the plotter.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        if value is not None and not isinstance(value, BBox):
            emsg = f"'manifold' must be a 'BBox' instance, got '{type(value)}'."
            raise TypeError(emsg)
        self._manifold = value

    def _add_graticule_labels(
        self,
        graticule: GraticuleGrid,
        /,
        *,
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
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`.
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

        labels = graticule.labels
        lonlat = graticule.lonlat

        xyz = to_cartesian(
            lonlat[:, 0], lonlat[:, 1], radius=radius, zlevel=zlevel, zscale=zscale
        )
        mesh = pv.PolyData(xyz)
        to_wkt(mesh, WGS84)

        if graticule.mask is not None:
            mask = graticule.mask * REMESH_SEAM
            mesh.point_data[GV_REMESH_POINT_IDS] = mask
            mesh.set_active_scalars(name=None)

        if self._manifold:
            mesh[GV_POINT_IDS] = np.arange(mesh.n_points)
            mesh.set_active_scalars(name=None)
            mesh = self._manifold(mesh)
            idxs = mesh[GV_POINT_IDS]
            labels = np.array(labels)[idxs]

        if mesh.n_points:
            # the point-cloud won't be sliced, however it's important that the
            # central-meridian rotation is performed here
            mesh = transform_mesh(mesh, tgt_crs=self.crs, zlevel=zlevel, inplace=True)

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

            self.add_point_labels: Callable[..., None]
            self.add_point_labels(xyz, labels, **point_labels_args)

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
                self.add_text: Callable[..., None]
                self.add_text(
                    "Requires GPU opacity support",
                    position="lower_right",
                    font_size=7,
                    color="red",
                    shadow=True,
                )
                self._missing_opacity = True

    def add_base_layer(
        self,
        *,
        mesh: pv.PolyData | None = None,
        resolution: str | None = None,
        radius: float | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        rtol: float | None = None,
        atol: float | None = None,
        **kwargs: Any | None,
    ) -> pv.Actor:
        """Generate a cubed-sphere base layer mesh and add to the plotter scene.

        Optionally, a `mesh` may be provided (e.g. if one is available that
        better fits the geometry of the surface mesh).

        Parameters
        ----------
        mesh : PolyData, optional
            Use the provided mesh as the base layer.
        resolution : str, optional
            The resolution of the cubed-sphere to generate as the base layer,
            which may be either ``c48``, ``c96`` or ``c192``. Defaults to
            :data:`geovista.pantry.meshes.LFRIC_RESOLUTION`. Alternatively, generate a
            regular grid using a format of ``rN``, where ``N`` is the number of cells
            in latitude, and ``N * 1.5`` cells in longitude. When adding a base layer
            to a projection, the default is to use a regular grid with resolution
            :data:`geovista.pantry.meshes.REGULAR_RESOLUTION`.
        radius : float, optional
            The radius of the spherical mesh to generate as the base layer. Defaults
            to :data:`geovista.common.RADIUS`.
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
            Defaults to ``-1``.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`BASE_ZLEVEL_SCALE`.
        rtol : float, optional
            The relative tolerance for longitudes close to the 'wrap meridian' -
            see :func:`geovista.common.wrap` for more.
        atol : float, optional
            The absolute tolerance for longitudes close to the 'wrap meridian' -
            see :func:`geovista.common.wrap` for more.
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
        if resolution is None:
            resolution = (
                REGULAR_RESOLUTION if self.crs.is_projected else LFRIC_RESOLUTION
            )
        else:
            resolution = str(resolution)

        if self.crs.is_projected:
            # pass through "zlevel" and "zscale" to the "add_mesh" method,
            # but ignore "radius", as it's not applicable to planar projections
            radius = None
            kwargs["zlevel"] = -1 if zlevel is None else zlevel
            kwargs["zscale"] = BASE_ZLEVEL_SCALE if zscale is None else zscale
        else:
            if radius is None:
                radius = RADIUS
            if zlevel is None:
                zlevel = -1
            if zscale is None:
                zscale = BASE_ZLEVEL_SCALE
            radius += radius * zlevel * zscale

        if mesh is not None:
            if radius is not None:
                mesh = resize(mesh, radius=radius)
        elif resolution.startswith("r"):
            mesh = regular_grid(resolution=resolution, radius=radius)
        else:
            mesh = _lfric_mesh(resolution=resolution, radius=radius)

        return self.add_mesh(mesh, rtol=rtol, atol=atol, **kwargs)

    def add_coastlines(
        self,
        *,
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
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
            Defaults to :data:`geovista.common.ZTRANSFORM_FACTOR`.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        rtol : float, optional
            The relative tolerance for longitudes close to the 'wrap meridian' -
            see :func:`geovista.common.wrap` for more.
        atol : float, optional
            The absolute tolerance for longitudes close to the 'wrap meridian' -
            see :func:`geovista.common.wrap` for more.
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
            # ignore "radius", as it's not applicable to planar projections
            radius = None

            if rtol is None:
                rtol = COASTLINES_RTOL
            if zscale is None:
                zscale = ZLEVEL_SCALE
            if zlevel is None:
                zlevel = ZTRANSFORM_FACTOR

            # pass through kwargs to "add_mesh" method
            kwargs.update({"zlevel": zlevel, "zscale": zscale})

        mesh = coastlines(
            resolution=resolution, radius=radius, zlevel=zlevel, zscale=zscale
        )

        return self.add_mesh(mesh, rtol=rtol, atol=atol, **kwargs)

    def add_graticule(  # noqa: PLR0913
        self,
        *,
        lon_start: float | None = None,
        lon_stop: float | None = None,
        lon_step: float | None = None,
        lat_start: float | None = None,
        lat_stop: float | None = None,
        lat_step: float | None = None,
        n_samples: int | tuple[int | None, int | None] | None = None,
        factor: float | None = None,
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
            ``closed_interval`` in :func:`~geovista.gridlines.create_meridians`.
            Defaults to :data:`geovista.gridlines.LONGITUDE_STOP`.
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
        n_samples : int | tuple[int | None, int | None], optional
            The number of points in a single line of longitude and latitude.
            If a single integer is provided, both meridians and parallels will
            use that value. If a tuple of two integers is provided, the first
            value will be used for meridians and the second for parallels. A value
            of ``None`` will use the defaults provided by
            :data:`geovista.gridlines.LONGITUDE_N_SAMPLES` and
            :data:`geovista.gridlines.LATITUDE_N_SAMPLES`.
        factor : float, optional
            The factor to scale the number of sample points in a single graticule line
            (meridians and parallels). E.g. a ``factor=2`` will double the number of
            sample points. Defaults to 1.
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
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`.
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
        if not isinstance(n_samples, Iterable):
            num_samples = (n_samples, n_samples)
        else:
            num_samples = n_samples

        self.add_meridians(
            start=lon_start,
            stop=lon_stop,
            step=lon_step,
            lat_step=lat_step,
            n_samples=num_samples[0],
            factor=factor,
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
            n_samples=num_samples[1],
            factor=factor,
            poles_parallel=poles_parallel,
            poles_label=poles_label,
            show_labels=show_labels,
            radius=radius,
            zlevel=zlevel,
            zscale=zscale,
            mesh_args=mesh_args,
            point_labels_args=point_labels_args,
        )

    def add_mesh(
        self,
        mesh: Any,
        /,
        *,
        radius: float | None = None,
        zlevel: int | ArrayLike | None = None,
        zscale: float | None = None,
        rtol: float | None = None,
        atol: float | None = None,
        **kwargs: Any | None,
    ) -> pv.Actor:
        """Add the `mesh` to the plotter scene.

        See :meth:`pyvista.Plotter.add_mesh`.

        Parameters
        ----------
        mesh : PolyData
            The mesh to add to the plotter.
        radius : float, optional
            The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
        zlevel : int or ArrayLike, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius`/vertical by a proportional amount e.g.,
            ``radius * zlevel * zscale``. If `zlevel` is not a scalar, then its shape
            must match or broadcast with the shape of the ``mesh.points``.
            Defaults to ``0``.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        rtol : float, optional
            The relative tolerance for longitudes close to the 'wrap meridian' -
            see :func:`geovista.common.wrap` for more.
        atol : float, optional
            The absolute tolerance for longitudes close to the 'wrap meridian' -
            see :func:`geovista.common.wrap` for more.
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
        # assume this is a sane default
        if os.environ.get("GEOVISTA_VTK_WARNINGS", "false").lower() == "false":
            vtk_warnings_off()

        if isinstance(mesh, pv.UnstructuredGrid):
            mesh = cast(mesh)

        if isinstance(mesh, pv.PolyData):
            if zlevel is None:
                zlevel = 0

            if zscale is None:
                zscale = ZLEVEL_SCALE

            cloud = point_cloud(mesh)

            if cloud and GV_FIELD_ZSCALE in mesh.field_data:
                zscale = mesh[GV_FIELD_ZSCALE][0]

            src_crs = from_wkt(mesh)

            if src_crs is None and hasattr(mesh, "is_empty") and not mesh.is_empty:
                wmsg = (
                    "geovista found no coordinate reference system (CRS) attached "
                    "to mesh."
                )
                warn(wmsg, stacklevel=2)

            tgt_crs = self.crs
            transform_required = src_crs and src_crs != tgt_crs
            central_meridian = get_central_meridian(tgt_crs) or 0

            if transform_required and not cloud and not src_crs.is_projected:
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
            elif not projected(mesh) and zlevel:
                if not cloud:
                    radius = distance(mesh)

                mesh = resize(mesh, radius=radius, zlevel=zlevel, zscale=zscale)

        def _check(option: str) -> bool:
            """Determine whether the keyword argument is present and not ``None``.

            Parameters
            ----------
            option : str
                Keyword argument to check.

            Returns
            -------
            bool
                Whether the keyword argument is present and not ``None``.

            Notes
            -----
            .. versionadded:: 0.1.0

            """
            return option in kwargs and kwargs[option] is not None

        if not self._missing_opacity and (_check("opacity") or _check("nan_opacity")):
            self._warn_opacity()

        if hasattr(mesh, "center"):
            # POI cartesian xyz
            self._poi = mesh.center

        # Extend the geovista theme for scalar bar options.
        scalar_bar_args = (
            {
                "outline": True,
                "background_color": self.background_color,  # type: ignore[attr-defined]
                "fill": True,
            }
            if pv.global_theme.name == "geovista"
            else {}
        )

        # Always honour any requested scalar bar options.
        if "scalar_bar_args" in kwargs:
            scalar_bar_args.update(kwargs["scalar_bar_args"])  # type: ignore[arg-type]

        if scalar_bar_args:
            kwargs["scalar_bar_args"] = scalar_bar_args

        # reduced rendered mesh to only points enclosed by the manifold
        if self._manifold:
            mesh = self._manifold(mesh)

        # explicitly don't add an empty mesh, regardless of
        # theme allow_empty_mesh option
        if hasattr(mesh, "is_empty") and mesh.is_empty:
            result = None
        else:
            result = super().add_mesh(mesh, **kwargs)  # type: ignore[misc]

        return result

    def add_meridian(
        self,
        lon: float,
        /,
        *,
        lat_step: float | None = None,
        n_samples: int | None = None,
        factor: float | None = None,
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
            The delta (degrees) between neighbouring parallels. Sets the
            frequency of the labels. Defaults to
            :data:`geovista.gridlines.LATITUDE_STEP`.
        n_samples : int, optional
            The number of points in a single line of longitude. Defaults to
            :data:`geovista.gridlines.LONGITUDE_N_SAMPLES`.
        factor : float, optional
            The factor to scale the number of sample points in a single line of
            longitude. E.g. a ``factor=2`` will double the number of sample points.
            Defaults to 1.
        show_labels : bool, optional
            Whether to render the meridian label. Defaults to
            :data:`GRATICULE_SHOW_LABELS`.
        radius : float, optional
            The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`.
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
            factor=factor,
            show_labels=show_labels,
            radius=radius,
            zlevel=zlevel,
            zscale=zscale,
            mesh_args=mesh_args,
            point_labels_args=point_labels_args,
        )

    def add_meridians(
        self,
        *,
        start: float | None = None,
        stop: float | None = None,
        step: float | None = None,
        lat_step: float | None = None,
        n_samples: int | None = None,
        factor: float | None = None,
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
            meridian when it is a multiple of `step`. Also see
            ``closed_interval`` in :func:`~geovista.gridlines.create_meridians`.
            Defaults to :data:`geovista.gridlines.LONGITUDE_STOP`.
        step : float, optional
            The delta (degrees) between neighbouring meridians. Defaults to
            :data:`geovista.gridlines.LONGITUDE_STEP`.
        lat_step : float, optional
            The delta (degrees) between neighbouring parallels. Sets the
            frequency of the labels. Defaults to
            :data:`geovista.gridlines.LATITUDE_STEP`.
        n_samples : int, optional
            The number of points in a single line of longitude. Defaults to
            :data:`geovista.gridlines.LONGITUDE_N_SAMPLES`.
        factor : float, optional
            The factor to scale the number of sample points in a single line of
            longitude. E.g. a ``factor=2`` will double the number of sample points.
            Defaults to 1.
        show_labels : bool, optional
            Whether to render the labels of the meridians. Defaults to
            :data:`GRATICULE_SHOW_LABELS`.
        radius : float, optional
            The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`.
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
        from . import GEOVISTA_IMAGE_TESTING  # noqa: PLC0415

        if show_labels is None:
            show_labels = False if GEOVISTA_IMAGE_TESTING else GRATICULE_SHOW_LABELS

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
            factor=factor,
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
        /,
        *,
        lon_step: float | None = None,
        n_samples: int | None = None,
        factor: float | None = None,
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
            The delta (degrees) between neighbouring meridians. Sets the
            frequency of the labels. Defaults to
            :data:`geovista.gridlines.LONGITUDE_STEP`.
        n_samples : int, optional
            The number of points in a single line of latitude. Defaults to
            :data:`geovista.gridlines.LATITUDE_N_SAMPLES`.
        factor : float, optional
            The factor to scale the number of sample points in a single line of
            latitude. E.g. a ``factor=2`` will double the number of sample points.
            Defaults to 1.
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
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`.
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
            factor=factor,
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
        *,
        start: float | None = None,
        stop: float | None = None,
        step: float | None = None,
        lon_step: float | None = None,
        n_samples: int | None = None,
        factor: float | None = None,
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
            The delta (degrees) between neighbouring meridians. Sets the
            frequency of the labels. Defaults to
            :data:`geovista.gridlines.LONGITUDE_STEP`.
        n_samples : int, optional
            The number of points in a single line of latitude. Defaults to
            :data:`geovista.gridlines.LATITUDE_N_SAMPLES`.
        factor : float, optional
            The factor to scale the number of sample points in a single line of
            latitude. E.g. a ``factor=2`` will double the number of sample points.
            Defaults to 1.
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
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`.
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
        from . import GEOVISTA_IMAGE_TESTING  # noqa: PLC0415

        if show_labels is None:
            show_labels = False if GEOVISTA_IMAGE_TESTING else GRATICULE_SHOW_LABELS

        if zlevel is None:
            zlevel = ZTRANSFORM_FACTOR if self.crs.is_projected else GRATICULE_ZLEVEL

        if mesh_args is None:
            mesh_args = {}

        if point_labels_args is None:
            point_labels_args = {}

        # TODO @bjlittle: Fix behaviour of longitudes at poles.
        poles_parallel = False

        parallels = create_parallels(
            start=start,
            stop=stop,
            step=step,
            lon_step=lon_step,
            n_samples=n_samples,
            factor=factor,
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
        points: ArrayLike | pv.PolyData | None = None,
        *,
        xs: ArrayLike | None = None,
        ys: ArrayLike | None = None,
        scalars: str | ArrayLike | None = None,
        crs: CRSLike | None = None,
        radius: float | None = None,
        style: str | None = None,
        zlevel: int | ArrayLike | None = None,
        zscale: float | None = None,
        **kwargs: Any | None,
    ) -> pv.Actor:
        """Add points to the plotter scene.

        See :meth:`pyvista.Plotter.add_points`.

        Parameters
        ----------
        points : ArrayLike or PolyData, optional
            Array of xyz points, or the points of the mesh to be rendered.
            Passed to :meth:`pyvista.core.utilities.helpers.wrap` without any
            cartographic transformation, i.e. ``0 0 0`` is centre of the globe
            (the plot origin), ``0 0 1`` is the north pole.
        xs : ArrayLike, optional
            A 1D, 2D or 3D array of point-cloud x-values, in canonical `crs` units.
            Must have the same shape as the `ys`.
        ys : ArrayLike
            A 1D, 2D or 3D array of point-cloud y-values, in canonical `crs` units.
            Must have the same shape as the `xs`.
        scalars : str or ArrayLike, optional
            Values used to color the points. Either, the string name of an array that is
            present on the `points` mesh or an array equal to the number of points.
            If both `color` (see `kwargs`) and `scalars` are ``None``, then the active
            scalars on the `points` mesh are used.
        crs : CRSLike, optional
            The Coordinate Reference System of the provided `points`, or `xs` and `ys`.
            May be anything accepted by :meth:`pyproj.crs.CRS.from_user_input`. Defaults
            to ``EPSG:4326`` i.e., ``WGS 84``.
        radius : float, optional
            The radius of the mesh point-cloud. Defaults to
            :data:`geovista.common.RADIUS`.
        style : str, optional
            Visualization style of the points to be rendered. May be either ``points``
            or ``points_gaussian``. The ``points_gaussian`` option may be controlled
            with the ``emissive`` and ``render_points_as_spheres`` options in
            `kwargs`.
        zlevel : int or ArrayLike, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
            If `zlevel` is not a scalar, then its shape must match or broadcast
            with the shape of the `xs` and `ys`. Defaults to ``0``.
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
            crs = pyproj.CRS.from_user_input(crs)

        if style is None:
            style = "points"

        if style not in ADD_POINTS_STYLE:
            options = "or ".join(f"{option!r}" for option in ADD_POINTS_STYLE)
            emsg = (
                f"Invalid 'style' for 'add_points', expected {options}, got {style!r}."
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

            if not pv.core.utilities.helpers.is_pyvista_dataset(points):
                points = pv.core.utilities.helpers.wrap(points)

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
                    f"geovista ignoring the 'scalars' string name '{scalars}', as no "
                    "'points' mesh was provided."
                )
                warn(wmsg, stacklevel=2)

            mesh = Transform.from_points(
                xs,
                ys,
                crs=crs,
                radius=radius,
                zlevel=zlevel,
                zscale=zscale,
            )

        # defensive kwarg pop
        if "texture" in kwargs:
            _ = kwargs.pop("texture")

        return self.add_mesh(mesh, style=style, scalars=scalars, **kwargs)

    def view_poi(
        self,
        x: float | None = None,
        y: float | None = None,
        *,
        crs: CRSLike | None = None,
    ) -> None:
        """Center the camera at a point-of-interest (POI).

        If no POI is provided, then the center of the previous mesh added to the scene
        is used, if available.

        Note that the camera will be positioned at the POI to view **all** the actors
        added to the scene so far; order is important. The point at which
        :meth:`~geovista.geoplotter.GeoPlotterBase.view_poi` is called relative to the
        other actors influences the final rendered scene.

        Parameters
        ----------
        x : float, optional
            The spatial x-value point, in canonical `crs` units, of the POI.
            Defaults to ``0`` if unspecified and `y` has been provided,
            otherwise ``None``.
        y : float, optional
            The spatial y-value point, in canonical `crs` units, of the POI.
            Defaults to ``0`` if unspecified and `x` has been provided,
            otherwise ``None``.
        crs : CRSLike, optional
            The Coordinate Reference System of the POI. May be anything accepted by
            :meth:`pyproj.crs.CRS.from_user_input`. Defaults to ``EPSG:4326`` i.e.,
            ``WGS 84``.

        Notes
        -----
        .. versionadded:: 0.5.0

        Examples
        --------
        First, create an RGB mesh of the Bahamas from a GeoTIFF.

        >>> import geovista
        >>> from geovista.pantry import fetch_raster
        >>> fname = fetch_raster("bahamas_rgb.tif")
        >>> bahamas = geovista.Transform.from_tiff(
        ...     fname, rgb=True, sieve=True, extract=True
        ... )

        Now add the ``bahamas`` mesh to a ``plotter`` **before** adding a texture mapped
        base layer. Note that the camera is centered over the ``bahamas`` mesh, which
        is the primary focus of the scene.

        >>> p = geovista.GeoPlotter()
        >>> _ = p.add_mesh(bahamas, rgb=True)
        >>> p.view_poi()
        >>> _ = p.add_base_layer(texture=geovista.natural_earth_1())
        >>> p.show()

        In comparison, add a texture mapped base layer to a ``plotter`` **before** the
        ``bahamas`` mesh. The camera is still centered over the ``bahamas`` in the
        rendered scene, however the base layer is now fully visible.

        >>> p = geovista.GeoPlotter()
        >>> _ = p.add_base_layer(texture=geovista.natural_earth_1())
        >>> _ = p.add_mesh(bahamas, rgb=True)
        >>> p.view_poi()
        >>> p.show()

        """
        self.camera: pv.Plotter.camera
        camera = self.camera

        if crs is None:
            crs = WGS84

        use_mesh_poi = x is None and y is None

        if not use_mesh_poi:
            # at the very least x or y has been provided
            # default any unset to 0, which allows the API to support the
            # convenience "view_poi(x=30)" instead of "view_poi(x=30, y=0)"
            if x is None:
                x = 0
            if y is None:
                y = 0

        if use_mesh_poi:
            if self._poi is None:
                # this is a no-op
                wmsg = "No point-of-interest (POI) is available or has been provided."
                warn(wmsg, stacklevel=2)
                return

            if self.crs.is_geographic:
                # convert cartesian xyz to lon/lat
                x, y = to_lonlat(self._poi)
                crs = WGS84
            else:
                x, y, _ = self._poi
                crs = self.crs

        # Assertion to appease MyPy.
        assert x is not None
        assert y is not None
        if crs != self.crs:
            x, y, _ = transform_point(src_crs=crs, tgt_crs=self.crs, x=x, y=y)

        if self.crs.is_geographic:
            camera.focal_point = (0, 0, 0)
            # convert POI lon/lat to cartesian xyz
            xyz = to_cartesian(x, y)[0]
            # calculate the unit vector
            u_hat = xyz / np.linalg.norm(xyz)
            # set the new camera position at the same magnitude from the focal point
            camera.position = u_hat * np.linalg.norm(camera.position)
            self.reset_camera: Callable[..., None]
            self.reset_camera(render=False)
            clip = camera.clipping_range
            # defensive: extend far clip range to ensure no accidental
            # back culling of any potential forth-coming actors that
            # may be added to the scene
            camera.clipping_range = (clip[0], clip[1] * 2)
        else:
            position = np.array(camera.position)
            focal_point = np.array(camera.focal_point)
            magnitude = np.linalg.norm(focal_point - position)
            camera.up = (0, 1, 0)
            camera.focal_point = (x, y, 0)
            camera.position = (x, y, magnitude)


class GeoPlotter(GeoPlotterBase, pv.Plotter):
    """A geospatial aware plotter.

    See :class:`geovista.geoplotter.GeoPlotterBase` and
    :class:`pyvista.Plotter`.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
