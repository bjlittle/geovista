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
import typing
from typing import TYPE_CHECKING, Any
from warnings import warn

import lazy_loader as lazy

import geovista.config as gvc

from .bridge import Transform
from .common import (
    GV_FIELD_ZSCALE,
    GV_POINT_IDS,
    GV_POINT_ZLEVEL,
    GV_REMESH_POINT_IDS,
    LRU_CACHE_SIZE,
    REMESH_SEAM,
    ZLEVEL_SCALE,
    ZTRANSFORM_FACTOR,
    _current,
    _missing_positions,
    _refuse_missing_poi,
    _to_cartesian,
    from_cartesian,
    point_cloud,
    to_cartesian,
    to_lonlat,
    vtk_warnings_off,
)
from .common import cast_UnstructuredGrid_to_PolyData as cast
from .core import add_texture_coords, resize
from .crs import (
    WGS84,
    CRSLike,
    from_wkt,
    get_central_meridian,
    has_wkt,
    planar,
    projected,
    to_wkt,
)
from .geodesic import BBox
from .geometry import coastlines
from .globe import (
    Globe,
    _carried_heights,
    _for_points,
    _heights,
    _on_globe,
    _record_heights,
    _refuse_zlevel,
    _resolve,
    _written,
)
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
from .themes import resolve_theme_name
from .transform import (
    _apply_datum,
    _carry_levels,
    _coordinates,
    _heights_z,
    _point_levels,
    _slice_seam,
    transform_mesh,
    transform_point,
)
from .units import _Quantity

if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy as np
    from numpy.typing import ArrayLike
    import pyproj
    import pyvista as pv
    from pyvista.plotting.themes import Theme

    from geovista.crs import CRSLike
    from geovista.units import Quantity

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
    globe: Globe | None = None,
) -> pv.PolyData:
    """Retrieve the LFRic unstructured cubed-sphere from the geovista cache.

    Parameters
    ----------
    resolution : str, optional
        The resolution of the LFRic unstructured cubed-sphere. Defaults to
        :data:`geovista.pantry.meshes.LFRIC_RESOLUTION`.
    globe : :class:`~geovista.globe.Globe`, optional
        The globe the mesh is drawn on, which it records. Defaults to
        ``Globe()``.

    Returns
    -------
    PolyData
        The LFRic spherical mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    mesh = lfric(resolution=resolution)

    # a fresh mesh, so it is resized in place
    mesh = resize(mesh, globe=_resolve(globe), inplace=True)

    mesh.set_active_scalars(name=None)

    return mesh


def _cut_scalars(scalars: ArrayLike, kept: np.ndarray) -> np.ndarray:
    """Keep the scalars of the points kept, of one value or one row for each point.

    A point cloud drops a missing point, with its entry in every array given for
    each point (positions spec §4.5).

    Parameters
    ----------
    scalars : ArrayLike
        The scalars: one value, or one row such as a colour, for each point given.
    kept : ndarray of bool
        ``True`` for each point given that is kept, in C order.

    Returns
    -------
    ndarray
        The scalars of the points kept, each row keeping its shape.

    Raises
    ------
    ValueError
        If `scalars` are not one value or one row for each point given, which
        would be refused were no point missing.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    values = np.asanyarray(scalars)

    if values.ndim > 1 and len(values) == kept.size:
        # one row for each point, such as a colour, or a column of values that
        # pyvista colours by magnitude, so each row keeps its shape
        rows: np.ndarray = values[kept]
        return rows

    if values.size == kept.size:
        result: np.ndarray = values.ravel()[kept]
        return result

    # refused before the points are cut, or they would pair with the points kept
    emsg = (
        "Require scalars with one value, or one row, for each of the "
        f"{kept.size:,d} points given, got shape {values.shape}."
    )
    raise ValueError(emsg)


def _place_by_heights(mesh: pv.DataSet, globe: Globe, /) -> None:
    """Place the points of a mesh at their heights on a globe, in place.

    On the sphere each point keeps its direction, and lies at a radius of
    ``s (R + V(h))``. On a map each point keeps its ``x`` and ``y``, and lies at
    ``z = V(h)`` in the units of the CRS (heights spec §4.3). The mesh records
    the globe.

    Parameters
    ----------
    mesh : pyvista.DataSet
        The mesh, which carries heights.
    globe : Globe
        The globe to place its points on.

    Raises
    ------
    ValueError
        If the mesh lies flat with no CRS, as its heights cannot be placed.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    heights = _carried_heights(mesh)

    if heights is None:
        # nothing to place by
        return

    if projected(mesh):
        crs = from_wkt(mesh)
        if crs is None:
            # heights recorded but never placed would disagree with the points
            emsg = (
                "Heights place each point, but the mesh lies flat with no "
                "coordinate reference system (CRS), so geovista cannot tell "
                "where its points are. Attach a CRS with geovista.crs.to_wkt."
            )
            raise ValueError(emsg)
        points = np.array(mesh.points)
        points[:, 2] = _heights_z(globe, heights, crs)
        mesh.points = points
    else:
        # from_cartesian reads only the points, which every dataset has
        lonlat = from_cartesian(typing.cast("pv.PolyData", mesh))
        mesh.points = _on_globe(globe, lonlat[:, 0], lonlat[:, 1], heights)

    globe.to_mesh(mesh)


def _carries_levels(mesh: pv.DataSet, /) -> bool:
    """Determine whether the points of a point cloud carry z-levels other than 0.

    On the sphere a cloud keeps its levels in the radius of each point, so a
    point off the render radius of the globe it records carries a level, to
    the precision its points are stored in. On a map it keeps them in
    ``gvZLevel``, read to the rounding of its points over the magnitude of its
    zscale. A zscale of 0 lifts no point, so such a cloud carries no level.

    Parameters
    ----------
    mesh : pyvista.DataSet
        The mesh.

    Returns
    -------
    bool
        Whether the mesh is a point cloud whose points carry z-levels other
        than 0.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if not isinstance(mesh, pv.PolyData) or not point_cloud(mesh):
        return False

    if projected(mesh):
        if GV_POINT_ZLEVEL not in mesh.point_data:
            return False
        zscale = abs(
            float(mesh.field_data[GV_FIELD_ZSCALE][0])
            if GV_FIELD_ZSCALE in mesh.field_data
            else ZLEVEL_SCALE
        )
        if zscale == 0:
            # a zscale of 0 lifts no point, whatever its level
            return False
        # the levels were read from the radius of each point, so carry the
        # rounding of the points, which keep their precision on a map, over
        # the zscale
        atol = 16 * np.finfo(np.asarray(mesh.points).dtype).eps / zscale
        levels = np.asarray(mesh.point_data[GV_POINT_ZLEVEL], dtype=np.float64)
        return not np.allclose(levels, 0.0, rtol=0, atol=atol)

    globe = Globe.from_mesh(mesh)

    if GV_FIELD_ZSCALE not in mesh.field_data or globe is None:
        return False

    points = np.asarray(mesh.points)
    rtol = 16 * np.finfo(points.dtype).eps
    return not np.allclose(
        np.linalg.norm(points.astype(np.float64), axis=1),
        globe.render_radius,
        rtol=rtol,
        atol=0,
    )


if TYPE_CHECKING:
    # mypy needs to know the mixin is combined with a plotter, which is true of
    # every class that uses it
    _PlotterBase = pv.BasePlotter
else:
    _PlotterBase = object


class GeoPlotterBase(_PlotterBase):  # numpydoc ignore=PR01
    """Base class with common behaviour for a geospatial aware plotter.

    See :class:`pyvista.Plotter`.

    Notes
    -----
    .. versionadded:: 0.1.0

    """

    def __init__(
        self,
        *args: Any,
        crs: CRSLike | None = None,
        globe: Globe | None = None,
        manifold: BBox | None = None,
        theme: Theme | str | None = None,
        **kwargs: Any,
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
        globe : :class:`~geovista.globe.Globe`, optional
            The globe of the scene, which every layer added takes its geometry
            from. Defaults to ``Globe()``.
        manifold : BBox, optional
            Apply the `manifold` to each mesh added to the plotter so that only
            the region enclosed by the `manifold` is rendered.
        theme : Theme or str, optional
            Plot specific theme.
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

        if isinstance(theme, str):
            theme = resolve_theme_name(theme)

        if theme is not None:
            kwargs["theme"] = theme

        # status of gpu opacity support
        self._missing_opacity = False
        # cartesian (xyz) center of last mesh added to the plotter
        self._poi: list[float] | None = None
        super().__init__(*args, **kwargs)

        # the globe of the scene, read through the "globe" property. It is resolved
        # once the plotter is whole, as pyvista cannot delete one only partly made
        self._globe = _resolve(globe)

    @property
    def globe(self) -> Globe:
        """The globe of the scene, which every layer added takes its geometry from.

        It cannot be set, since the layers already added are drawn at it.

        Returns
        -------
        :class:`~geovista.globe.Globe`
            The globe of the scene.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        return self._globe

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
        zlevel: int | None = None,
        zscale: float | None = None,
        point_labels_args: dict[Any, Any] | None = None,
        name: str | None = None,
    ) -> None:
        """Render the labels for the given parallels/meridians.

        Parameters
        ----------
        graticule : GraticuleGrid
            The labels and associated lon/lat points for the graticule
            parallels/meridians.
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            render radius of the scene's globe by a proportional amount i.e.,
            ``render_radius * zlevel * zscale``.
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        point_labels_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_point_labels`.
        name : str, optional
            The name for the added labels/actor so that they can be easily updated.
            If an actor of this name already exists in the plotter scene, it
            will be replaced by the new actor. Note that the provided `name` will be
            appended with ``-labels`` to form the name of the added labels/actor.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        if zlevel is None:
            zlevel = GRATICULE_ZLEVEL

        if point_labels_args is None:
            point_labels_args = {}

        labels = graticule.labels
        lonlat = np.asanyarray(graticule.lonlat)

        xyz = _to_cartesian(
            lonlat[:, 0],
            lonlat[:, 1],
            radius=self.globe.render_radius,
            zlevel=zlevel,
            zscale=zscale,
        )
        mesh = pv.PolyData(xyz)
        to_wkt(mesh, WGS84)

        if graticule.mask is not None:
            mask = np.asanyarray(graticule.mask) * REMESH_SEAM
            mesh.point_data[GV_REMESH_POINT_IDS] = mask
            mesh.set_active_scalars(name=None)

        if self._manifold:
            mesh[GV_POINT_IDS] = np.arange(mesh.n_points)
            mesh.set_active_scalars(name=None)
            mesh = self._manifold(mesh)
            idxs = mesh[GV_POINT_IDS]
            labels = np.array(labels)[idxs].tolist()

        if mesh.n_points:
            # the point-cloud won't be sliced, however it's important that the
            # central-meridian rotation is performed here
            mesh = transform_mesh(
                mesh,
                tgt_crs=self.crs,
                globe=self.globe,
                zlevel=zlevel,
                zscale=zscale,
                inplace=True,
            )

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

            self.add_point_labels(xyz, labels, name=name, **point_labels_args)

    def _warn_opacity(self) -> None:
        """Add textual warning for no opacity support to plotter scene.

        Convenience for adding a text warning to the render scene for known GPU
        configurations that don't support opacity.

        Notes
        -----
        .. versionadded:: 0.4.0

        """
        if not self._missing_opacity:
            # typing spec §8 -- pyvista 0.49 leaves GPUInfo.__init__ unannotated
            gpu_info: Callable[[], pv.GPUInfo] = pv.GPUInfo
            info = gpu_info()
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
        self,
        *,
        mesh: pv.PolyData | None = None,
        resolution: str | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        rtol: float | None = None,
        atol: float | None = None,
        **kwargs: Any,
    ) -> pv.Actor | None:
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
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            render radius of the scene's globe by a proportional amount i.e.,
            ``render_radius * zlevel * zscale``.
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
        Actor or None
            The rendered actor added to the plotter scene, or ``None`` when the
            mesh is empty and nothing is added.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if resolution is None:
            resolution = REGULAR_RESOLUTION if planar(self.crs) else LFRIC_RESOLUTION
        else:
            resolution = str(resolution)

        zlevel = -1 if zlevel is None else zlevel
        zscale = BASE_ZLEVEL_SCALE if zscale is None else zscale

        if mesh is None:
            mesh = (
                regular_grid(resolution=resolution, globe=self.globe)
                if resolution.startswith("r")
                else _lfric_mesh(resolution=resolution, globe=self.globe)
            )

        if planar(self.crs):
            # pass through "zlevel" and "zscale" to the "add_mesh" method
            kwargs["zlevel"] = zlevel
            kwargs["zscale"] = zscale
        else:
            # lowered beneath the scene's globe, which it records
            mesh = resize(mesh, globe=self.globe, zlevel=zlevel, zscale=zscale)

        return self.add_mesh(mesh, rtol=rtol, atol=atol, **kwargs)

    def add_coastlines(
        self,
        *,
        resolution: str | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        rtol: float | None = None,
        atol: float | None = None,
        **kwargs: Any,
    ) -> pv.Actor | None:
        """Generate coastlines and add to the plotter scene.

        Parameters
        ----------
        resolution : str, optional
            The resolution of the Natural Earth coastlines, which may be either
            ``110m``, ``50m``, or ``10m``. Defaults to
            :data:`geovista.common.COASTLINES_RESOLUTION`.
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            render radius of the scene's globe by a proportional amount i.e.,
            ``render_radius * zlevel * zscale``.
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
        Actor or None
            The rendered actor added to the plotter scene, or ``None`` when the
            mesh is empty and nothing is added.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if planar(self.crs):
            if rtol is None:
                rtol = COASTLINES_RTOL
            if zscale is None:
                zscale = ZLEVEL_SCALE
            if zlevel is None:
                zlevel = ZTRANSFORM_FACTOR

            # pass through kwargs to "add_mesh" method
            kwargs.update({"zlevel": zlevel, "zscale": zscale})

        mesh = coastlines(
            resolution=resolution, globe=self.globe, zlevel=zlevel, zscale=zscale
        )

        return self.add_mesh(mesh, rtol=rtol, atol=atol, **kwargs)

    def add_graticule(  # noqa: PLR0913
        self,
        *,
        lon_start: float | Quantity | None = None,
        lon_stop: float | Quantity | None = None,
        lon_step: float | Quantity | None = None,
        lat_start: float | Quantity | None = None,
        lat_stop: float | Quantity | None = None,
        lat_step: float | Quantity | None = None,
        n_samples: int | tuple[int | None, int | None] | None = None,
        factor: float | None = None,
        poles_parallel: bool | None = None,
        poles_label: bool | None = None,
        show_labels: bool | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        mesh_args: dict[Any, Any] | None = None,
        point_labels_args: dict[Any, Any] | None = None,
        name: str | None = None,
    ) -> None:
        """Generate a graticule and add to the plotter scene.

        This involves generating lines of constant latitude (parallels) and
        lines of constant longitude (meridians), which together form the graticule.

        Parameters
        ----------
        lon_start : float or pint.Quantity, optional
            The first line of longitude (degrees). The graticule will include this
            meridian. Defaults to :data:`geovista.gridlines.LONGITUDE_START`.
            A ``pint`` quantity, from any registry, is read in degrees.
        lon_stop : float or pint.Quantity, optional
            The last line of longitude (degrees). The graticule will include this
            meridian when it is a multiple of `lon_step`. Also see
            ``closed_interval`` in :func:`~geovista.gridlines.create_meridians`.
            Defaults to :data:`geovista.gridlines.LONGITUDE_STOP`.
            A ``pint`` quantity, from any registry, is read in degrees.
        lon_step : float or pint.Quantity, optional
            The delta (degrees) between neighbouring meridians. Defaults to
            :data:`geovista.gridlines.LONGITUDE_STEP`.
            A ``pint`` quantity, from any registry, is read in degrees.
        lat_start : float or pint.Quantity, optional
            The first line of latitude (degrees). The graticule will include this
            parallel. Also see `poles_parallel`. Defaults to
            :data:`geovista.gridlines.LATITUDE_START`.
            A ``pint`` quantity, from any registry, is read in degrees.
        lat_stop : float or pint.Quantity, optional
            The last line of latitude (degrees). The graticule will include this
            parallel when it is a multiple of `lat_step`. Defaults to
            :data:`geovista.gridlines.LATITUDE_STOP`.
            A ``pint`` quantity, from any registry, is read in degrees.
        lat_step : float or pint.Quantity, optional
            The delta (degrees) between neighbouring parallels. Defaults to
            :data:`geovista.gridlines.LATITUDE_STEP`.
            A ``pint`` quantity, from any registry, is read in degrees.
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
            (meridians and parallels) e.g. a ``factor=2`` will double the number of
            sample points. Defaults to ``1``.
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
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            render radius of the scene's globe by a proportional amount i.e.,
            ``render_radius * zlevel * zscale``.
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        mesh_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_mesh`.
        point_labels_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_point_labels`.
        name : str, optional
            The name for the added graticule actors so that they can be easily updated.
            If actors of this name already exist in the plotter scene, they
            will be replaced by the new actors. Note that the provided `name` will be
            prepended with ``meridian-`` or ``parallel-`` to form the names of the
            graticule actors.

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
            zlevel=zlevel,
            zscale=zscale,
            mesh_args=mesh_args,
            point_labels_args=point_labels_args,
            name=name,
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
            zlevel=zlevel,
            zscale=zscale,
            mesh_args=mesh_args,
            point_labels_args=point_labels_args,
            name=name,
        )

    def add_mesh(  # type: ignore[override]  # typing spec §3.5
        self,
        mesh: Any,
        /,
        *,
        height: ArrayLike | Quantity | None = None,
        depth: ArrayLike | Quantity | None = None,
        vertical_units: str | None = None,
        zlevel: int | ArrayLike | None = None,
        zscale: float | None = None,
        rtol: float | None = None,
        atol: float | None = None,
        **kwargs: Any,
    ) -> pv.Actor | None:
        """Add the `mesh` to the plotter scene.

        See :meth:`pyvista.Plotter.add_mesh`.

        Parameters
        ----------
        mesh : PolyData
            The mesh to add to the plotter.
        height : ArrayLike or pint.Quantity, optional
            The height of each point, or one for the whole mesh, above mean sea
            level: in metres, in the unit `vertical_units` names, or a ``pint``
            quantity of length from any registry. A masked or NaN height is
            missing, and its point is drawn at sea level. The heights are written
            to a copy, which is placed by them at the scene's globe and drawn, so
            the `mesh` given is unchanged. Heights given for a `mesh` that already
            carries them are refused.
        depth : ArrayLike or pint.Quantity, optional
            The depth of each point, or one for the whole mesh, positive
            downward, in the same forms as a `height`. Give a `height` or a
            `depth`, not both.
        vertical_units : str, optional
            The CF unit of a `height` or `depth` given as plain numbers.
            Defaults to metres.
        zlevel : int or ArrayLike, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            render radius of the scene's globe/vertical by a proportional amount
            e.g., ``render_radius * zlevel * zscale``. If `zlevel` is not a scalar,
            then it must broadcast to the shape ``(mesh.n_points,)``. Defaults to
            ``0``.
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
        Actor or None
            The rendered actor added to the plotter scene, or ``None`` when the
            mesh is empty and nothing is added.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        info = (
            mesh.active_scalars_info if hasattr(mesh, "active_scalars_info") else None
        )
        # the mesh given, which drawing never changes
        given = mesh

        # assume this is a sane default
        if os.environ.get("GEOVISTA_VTK_WARNINGS", "false").lower() == "false":
            vtk_warnings_off()

        if isinstance(mesh, pv.UnstructuredGrid):
            mesh = cast(mesh)

        heights = _heights(
            height,
            depth,
            vertical_units,
            crs=from_wkt(mesh) if isinstance(mesh, pv.DataSet) else None,
        )

        if heights is not None or (
            isinstance(mesh, pv.DataSet) and _carried_heights(mesh) is not None
        ):
            # a height and a z-level are never given together (heights spec §4.4)
            _refuse_zlevel(zlevel)

        if heights is not None:
            keyword = "height" if depth is None else "depth"
            mesh = self._with_heights(mesh, heights, keyword)

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
            transform_required = src_crs is not None and src_crs != tgt_crs
            src_planar = src_crs is not None and planar(src_crs)
            central_meridian = get_central_meridian(tgt_crs) or 0

            resize_required = (
                not transform_required
                and not projected(mesh)
                and bool(np.ndim(zlevel) or np.any(zlevel))
            )

            if transform_required and not cloud and not src_planar:
                # the seam is cut here, before any texture coordinates are added,
                # and a per-point zlevel is carried through the cut to the points
                # it adds, which is what transform_mesh is then given. The datum
                # operation is taken where each point is, before the cut, see
                # issue #2714
                mesh = _apply_datum(mesh, tgt_crs)
                level = _point_levels(mesh, zlevel)
                mesh, tgt_crs, zlevel = _slice_seam(
                    mesh, tgt_crs, level=level, rtol=rtol, atol=atol
                )

            if "texture" in kwargs and kwargs["texture"] is not None:
                if resize_required and not cloud:
                    # the seam cut adds points along the chords of the cells it
                    # crosses, inside the sphere, so a per-point zlevel is carried
                    # to them, and the resize below lifts them with the rest
                    level = np.asanyarray(zlevel)
                    if level.size == 1:
                        level = level.reshape(())
                    else:
                        level = _point_levels(mesh, level, action="resize")
                    mesh, zlevel = _carry_levels(
                        mesh,
                        level,
                        lambda mesh: add_texture_coords(mesh, antimeridian=True),
                    )
                else:
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
                    globe=self.globe,
                    # in place only on a mesh made here, never on the one given
                    inplace=not cloud and mesh is not given,
                )
                to_wkt(mesh, self.crs)
            elif resize_required:
                # a z-level lifts the mesh from the scene's globe
                mesh = resize(mesh, globe=self.globe, zlevel=zlevel, zscale=zscale)
            else:
                mesh = self._at_scene_globe(mesh)
        elif isinstance(mesh, pv.DataSet):
            mesh = self._at_scene_globe(mesh)

        if isinstance(mesh, pv.DataSet):
            # the mesh drawn carries only current fields
            mesh = _current(mesh, given)

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
                "background_color": self.background_color,
                "fill": True,
            }
            if self.theme.name.startswith("geovista")
            else {}
        )

        # Always honour any requested scalar bar options.
        if "scalar_bar_args" in kwargs:
            scalar_bar_args.update(kwargs["scalar_bar_args"])

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
            if info is not None:
                mesh.set_active_scalars(
                    info.name, preference=info.association.name.lower()
                )

            result = super().add_mesh(mesh, **kwargs)

        return result

    def _with_heights(
        self, mesh: Any, heights: float | np.ndarray, keyword: str, /
    ) -> pv.DataSet:
        """Return a copy of the mesh with its heights, placed at the scene's globe.

        Parameters
        ----------
        mesh : Any
            The mesh given to the scene.
        heights : float or ndarray
            The heights given, in metres, NaN where one is missing.
        keyword : str
            The keyword the heights were given by, ``height`` or ``depth``.

        Returns
        -------
        pyvista.DataSet
            A copy of the mesh, which records the heights and the scene's globe,
            with its points placed by them.

        Raises
        ------
        TypeError
            If the mesh is not a dataset.
        ValueError
            If the mesh carries heights of its own, lies flat with no CRS, is a
            point cloud whose points carry z-levels other than 0, or the heights
            fit neither its points nor the whole mesh.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        if not isinstance(mesh, pv.DataSet):
            emsg = (
                f"Heights are given for the points of a mesh, got {keyword!r} "
                f"with a {type(mesh).__name__}."
            )
            raise TypeError(emsg)

        # heights are given once (heights spec §2 decision 5)
        if _carried_heights(mesh) is not None:
            emsg = (
                "The mesh given carries heights of its own, and heights are "
                f"given once, got {keyword!r}."
            )
            raise ValueError(emsg)

        if _carries_levels(mesh):
            emsg = (
                "A height and a z-level are never given together, and the point "
                "cloud given carries z-levels other than 0."
            )
            raise ValueError(emsg)

        if projected(mesh) and from_wkt(mesh) is None:
            emsg = (
                f"Heights place each point, but the mesh given with {keyword!r} "
                "lies flat with no coordinate reference system (CRS), so "
                "geovista cannot tell where its points are. Attach a CRS with "
                "geovista.crs.to_wkt."
            )
            raise ValueError(emsg)

        values = _for_points(heights, mesh.n_points, mesh.n_cells)

        # the heights are written to the mesh drawn, never to the mesh given
        drawn: pv.DataSet = mesh.copy()
        _record_heights(drawn, values)

        # a point cloud with heights carries no z-level (heights spec §4.3)
        if GV_FIELD_ZSCALE in drawn.field_data:
            del drawn.field_data[GV_FIELD_ZSCALE]
        if GV_POINT_ZLEVEL in drawn.point_data:
            del drawn.point_data[GV_POINT_ZLEVEL]

        # positions are built from heights when a mesh is added, before any seam
        # is cut or the mesh is transformed (heights spec §2 decision 7)
        _place_by_heights(drawn, self.globe)

        return drawn

    def _at_scene_globe(self, mesh: pv.DataSet) -> pv.DataSet:
        """Return the mesh as drawn at the globe of the scene.

        A mesh that records another globe, in its four fields or a ``gvRadius``,
        is drawn as a copy that records the scene's. A mesh with heights is built
        from them at the scene's globe, on the globe and on a map. Any other has
        its points scaled by the ratio of the two render radii on the globe, and
        unmoved on a map. A mesh that records the scene's globe, or records none,
        is drawn where its points are, even when they lie at one radius.

        Parameters
        ----------
        mesh : pyvista.DataSet
            The mesh to draw.

        Returns
        -------
        pyvista.DataSet
            The mesh to draw.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        if not _written(mesh):
            # a globe read from points at one radius may be a shell above or
            # below the globe, so the mesh is drawn where it is
            return mesh

        recorded = Globe.from_mesh(mesh)

        if recorded is None or recorded == self.globe:
            return mesh

        mesh = mesh.copy()

        if _carried_heights(mesh) is not None:
            # a mesh with heights is built from them at the scene's globe, on
            # the globe and on a map (heights spec §4.3)
            _place_by_heights(mesh, self.globe)
        elif not projected(mesh):
            mesh.points = mesh.points * (
                self.globe.render_radius / recorded.render_radius
            )

        self.globe.to_mesh(mesh)

        return mesh

    def add_meridian(
        self,
        lon: float | Quantity,
        /,
        *,
        lat_step: float | Quantity | None = None,
        n_samples: int | None = None,
        factor: float | None = None,
        show_labels: bool | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        mesh_args: dict[Any, Any] | None = None,
        point_labels_args: dict[Any, Any] | None = None,
        name: str | None = None,
    ) -> None:
        """Generate a line of constant longitude and add to the plotter scene.

        Parameters
        ----------
        lon : float or pint.Quantity
            The constant line of longitude (degrees) to generate.
            A ``pint`` quantity, from any registry, is read in degrees.
        lat_step : float or pint.Quantity, optional
            The delta (degrees) between neighbouring parallels. Sets the
            frequency of the labels. Defaults to
            :data:`geovista.gridlines.LATITUDE_STEP`.
            A ``pint`` quantity, from any registry, is read in degrees.
        n_samples : int, optional
            The number of points in a single line of longitude. Defaults to
            :data:`geovista.gridlines.LONGITUDE_N_SAMPLES`.
        factor : float, optional
            The factor to scale the number of sample points in a single line of
            longitude e.g., a ``factor=2`` will double the number of sample points.
            Defaults to ``1``.
        show_labels : bool, optional
            Whether to render the meridian label. Defaults to
            :data:`GRATICULE_SHOW_LABELS`.
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            render radius of the scene's globe by a proportional amount i.e.,
            ``render_radius * zlevel * zscale``.
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        mesh_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_mesh`.
        point_labels_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_point_labels`.
        name : str, optional
            The name for the added meridian/actors so that it can be easily updated.
            If an actor of this name already exists in the plotter scene, it
            will be replaced by the new actor. Note that the provided `name` will be
            prepended with ``meridian-`` along with the longitude to form the name
            of the added meridian/actors.

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
            zlevel=zlevel,
            zscale=zscale,
            mesh_args=mesh_args,
            point_labels_args=point_labels_args,
            name=name,
        )

    def add_meridians(
        self,
        *,
        start: float | Quantity | None = None,
        stop: float | Quantity | None = None,
        step: float | Quantity | None = None,
        lat_step: float | Quantity | None = None,
        n_samples: int | None = None,
        factor: float | None = None,
        show_labels: bool | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        mesh_args: dict[Any, Any] | None = None,
        point_labels_args: dict[Any, Any] | None = None,
        name: str | None = None,
    ) -> None:
        """Generate lines of constant longitude and add to the plotter scene.

        Parameters
        ----------
        start : float or pint.Quantity, optional
            The first line of longitude (degrees). The graticule will include this
            meridian. Defaults to :data:`geovista.gridlines.LONGITUDE_START`.
            A ``pint`` quantity, from any registry, is read in degrees.
        stop : float or pint.Quantity, optional
            The last line of longitude (degrees). The graticule will include this
            meridian when it is a multiple of `step`. Also see
            ``closed_interval`` in :func:`~geovista.gridlines.create_meridians`.
            Defaults to :data:`geovista.gridlines.LONGITUDE_STOP`.
            A ``pint`` quantity, from any registry, is read in degrees.
        step : float or pint.Quantity, optional
            The delta (degrees) between neighbouring meridians. Defaults to
            :data:`geovista.gridlines.LONGITUDE_STEP`.
            A ``pint`` quantity, from any registry, is read in degrees.
        lat_step : float or pint.Quantity, optional
            The delta (degrees) between neighbouring parallels. Sets the
            frequency of the labels. Defaults to
            :data:`geovista.gridlines.LATITUDE_STEP`.
            A ``pint`` quantity, from any registry, is read in degrees.
        n_samples : int, optional
            The number of points in a single line of longitude. Defaults to
            :data:`geovista.gridlines.LONGITUDE_N_SAMPLES`.
        factor : float, optional
            The factor to scale the number of sample points in a single line of
            longitude e.g., a ``factor=2`` will double the number of sample points.
            Defaults to ``1``.
        show_labels : bool, optional
            Whether to render the labels of the meridians. Defaults to
            :data:`GRATICULE_SHOW_LABELS`.
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            render radius of the scene's globe by a proportional amount i.e.,
            ``render_radius * zlevel * zscale``.
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        mesh_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_mesh`.
        point_labels_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_point_labels`.
        name : str, optional
            The name for the added meridians/actors so that it can be easily updated.
            If an actor of this name already exists in the plotter scene, it
            will be replaced by the new actor. Note that the provided `name` will be
            prepended with ``meridian-`` along with the longitude to form the name of
            the added meridians/actors.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        if show_labels is None:
            show_labels = False if gvc.GEOVISTA_IMAGE_TESTING else GRATICULE_SHOW_LABELS

        if zlevel is None:
            zlevel = ZTRANSFORM_FACTOR if planar(self.crs) else GRATICULE_ZLEVEL

        if mesh_args is None:
            mesh_args = {}

        if point_labels_args is None:
            point_labels_args = {}

        closed_interval = planar(self.crs)
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
            globe=self.globe,
            zlevel=zlevel,
            zscale=zscale,
        )

        if zlevel is not None:
            mesh_args["zlevel"] = zlevel

        if zscale is not None:
            mesh_args["zscale"] = zscale

        labels = (
            label.replace("°", "")
            for label in meridians.labels[: len(meridians.blocks)]
        )
        mesh_names = []

        for label, mesh in zip(labels, meridians.blocks, strict=True):
            address = f"{type(mesh).__name__}({mesh.GetAddressAsString('')})"
            postfix = f"{address}" if name is None else f"{name}-{address}"
            mesh_name = f"meridian-{label}-{postfix}"
            mesh_names.append(mesh_name)
            self.add_mesh(mesh, name=mesh_name, **mesh_args)

        if show_labels:
            if len(mesh_names) == 1:
                (labels_name,) = mesh_names
            else:
                labels_name = "meridian" if name is None else f"meridian-{name}"

            # note that pyvista will automatically append "-labels" to the actor name
            self._add_graticule_labels(
                meridians,
                zlevel=zlevel,
                zscale=zscale,
                point_labels_args=point_labels_args,
                name=labels_name,
            )

    def add_parallel(
        self,
        lat: float | Quantity,
        /,
        *,
        lon_step: float | Quantity | None = None,
        n_samples: int | None = None,
        factor: float | None = None,
        poles_parallel: bool | None = None,
        show_labels: bool | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        mesh_args: dict[Any, Any] | None = None,
        point_labels_args: dict[Any, Any] | None = None,
        name: str | None = None,
    ) -> None:
        """Generate a line of constant latitude and add to the plotter scene.

        Parameters
        ----------
        lat : float or pint.Quantity
            The constant line of latitude (degrees) to generate.
            A ``pint`` quantity, from any registry, is read in degrees.
        lon_step : float or pint.Quantity, optional
            The delta (degrees) between neighbouring meridians. Sets the
            frequency of the labels. Defaults to
            :data:`geovista.gridlines.LONGITUDE_STEP`.
            A ``pint`` quantity, from any registry, is read in degrees.
        n_samples : int, optional
            The number of points in a single line of latitude. Defaults to
            :data:`geovista.gridlines.LATITUDE_N_SAMPLES`.
        factor : float, optional
            The factor to scale the number of sample points in a single line of
            latitude e.g., a ``factor=2`` will double the number of sample points.
            Defaults to ``1``.
        poles_parallel : bool, optional
            Whether to create a line of latitude at the north/south poles. Defaults to
            :data:`geovista.gridlines.LATITUDE_POLES_PARALLEL`.
        show_labels : bool, optional
            Whether to render the parallel label. Defaults to
            :data:`GRATICULE_SHOW_LABELS`.
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            render radius of the scene's globe by a proportional amount i.e.,
            ``render_radius * zlevel * zscale``.
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        mesh_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_mesh`.
        point_labels_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_point_labels`.
        name : str, optional
            The name for the added parallel/actor so that it can be easily updated.
            If an actor of this name already exists in the plotter scene, it
            will be replaced by the new actor. Note that the provided `name` will be
            prepended with ``parallel-`` along with the latitude to form the name of
            the added parallel/actor.

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
            zlevel=zlevel,
            zscale=zscale,
            mesh_args=mesh_args,
            point_labels_args=point_labels_args,
            name=name,
        )

    def add_parallels(
        self,
        *,
        start: float | Quantity | None = None,
        stop: float | Quantity | None = None,
        step: float | Quantity | None = None,
        lon_step: float | Quantity | None = None,
        n_samples: int | None = None,
        factor: float | None = None,
        poles_parallel: bool | None = None,
        poles_label: bool | None = None,
        show_labels: bool | None = None,
        zlevel: int | None = None,
        zscale: float | None = None,
        mesh_args: dict[Any, Any] | None = None,
        point_labels_args: dict[Any, Any] | None = None,
        name: str | None = None,
    ) -> None:
        """Generate lines of constant latitude and add to the plotter scene.

        Parameters
        ----------
        start : float or pint.Quantity, optional
            The first line of latitude (degrees). The graticule will include this
            parallel. Also see `poles_parallel`. Defaults to
            :data:`geovista.gridlines.LATITUDE_START`.
            A ``pint`` quantity, from any registry, is read in degrees.
        stop : float or pint.Quantity, optional
            The last line of latitude (degrees). The graticule will include this
            parallel when it is a multiple of `step`. Also see `poles_parallel`.
            Defaults to :data:`geovista.gridlines.LATITUDE_STOP`.
            A ``pint`` quantity, from any registry, is read in degrees.
        step : float or pint.Quantity, optional
            The delta (degrees) between neighbouring parallels. Defaults to
            :data:`geovista.gridlines.LATITUDE_STEP`.
            A ``pint`` quantity, from any registry, is read in degrees.
        lon_step : float or pint.Quantity, optional
            The delta (degrees) between neighbouring meridians. Sets the
            frequency of the labels. Defaults to
            :data:`geovista.gridlines.LONGITUDE_STEP`.
            A ``pint`` quantity, from any registry, is read in degrees.
        n_samples : int, optional
            The number of points in a single line of latitude. Defaults to
            :data:`geovista.gridlines.LATITUDE_N_SAMPLES`.
        factor : float, optional
            The factor to scale the number of sample points in a single line of
            latitude e.g., a ``factor=2`` will double the number of sample points.
            Defaults to ``1``.
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
        zlevel : int, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            render radius of the scene's globe by a proportional amount i.e.,
            ``render_radius * zlevel * zscale``.
            Defaults to :data:`geovista.gridlines.GRATICULE_ZLEVEL`.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        mesh_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_mesh`.
        point_labels_args : dict, optional
            Arguments to pass through to :meth:`pyvista.Plotter.add_point_labels`.
        name : str, optional
            The name for the added parallels/actors so that it can be easily updated.
            If an actor of this name already exists in the plotter scene, it
            will be replaced by the new actor. Note that the provided `name` will be
            prepended with ``-parallel`` along with the latitude to form the name of
            the added parallels/actors.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        if show_labels is None:
            show_labels = False if gvc.GEOVISTA_IMAGE_TESTING else GRATICULE_SHOW_LABELS

        if zlevel is None:
            zlevel = ZTRANSFORM_FACTOR if planar(self.crs) else GRATICULE_ZLEVEL

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
            globe=self.globe,
            zlevel=zlevel,
            zscale=zscale,
        )

        if zlevel is not None:
            mesh_args["zlevel"] = zlevel

        if zscale is not None:
            mesh_args["zscale"] = zscale

        labels = (
            label.replace("°", "")
            for label in parallels.labels[: len(parallels.blocks)]
        )
        mesh_names = []

        for label, mesh in zip(labels, parallels.blocks, strict=True):
            address = f"{type(mesh).__name__}({mesh.GetAddressAsString('')})"
            postfix = f"{address}" if name is None else f"{name}-{address}"
            mesh_name = f"parallel-{label}-{postfix}"
            mesh_names.append(mesh_name)
            self.add_mesh(mesh, name=mesh_name, **mesh_args)

        if show_labels:
            if len(mesh_names) == 1:
                (labels_name,) = mesh_names
            else:
                labels_name = "parallel" if name is None else f"parallel-{name}"

            # note that pyvista will automatically append "-labels" to the actor name
            self._add_graticule_labels(
                parallels,
                zlevel=zlevel,
                zscale=zscale,
                point_labels_args=point_labels_args,
                name=labels_name,
            )

    def add_points(  # type: ignore[override]  # typing spec §3.5
        self,
        points: ArrayLike | pv.PolyData | None = None,
        *,
        xs: ArrayLike | Quantity | None = None,
        ys: ArrayLike | Quantity | None = None,
        scalars: str | ArrayLike | None = None,
        crs: CRSLike | None = None,
        style: str | None = None,
        height: ArrayLike | Quantity | None = None,
        depth: ArrayLike | Quantity | None = None,
        vertical_units: str | None = None,
        zlevel: int | ArrayLike | None = None,
        zscale: float | None = None,
        **kwargs: Any,
    ) -> pv.Actor | None:
        """Add points to the plotter scene.

        See :meth:`pyvista.Plotter.add_points`.

        Parameters
        ----------
        points : ArrayLike or PolyData, optional
            Array of xyz points, or the points of the mesh to be rendered.
            Passed to :func:`pyvista.wrap` without any
            cartographic transformation, i.e. ``0 0 0`` is centre of the globe
            (the plot origin), ``0 0 1`` is the north pole.
        xs : ArrayLike or pint.Quantity, optional
            A 1D, 2D or 3D array of point-cloud x-values, in canonical `crs` units.
            Must have the same shape as the `ys`. A ``pint`` quantity, from any
            registry, carries its own units, and is read in those of the `crs`.
            Give `ys` as a quantity too.
        ys : ArrayLike or pint.Quantity, optional
            A 1D, 2D or 3D array of point-cloud y-values, in canonical `crs` units.
            Must have the same shape as the `xs`. A ``pint`` quantity, from any
            registry, carries its own units, and is read in those of the `crs`.
            Give `xs` as a quantity too.
        scalars : str or ArrayLike, optional
            Values used to color the points. Either, the string name of an array that is
            present on the `points` mesh or an array equal to the number of points.
            If both `color` (see `kwargs`) and `scalars` are ``None``, then the active
            scalars on the `points` mesh are used. An array given with `xs` and `ys`
            loses the entry of each missing point, which
            :meth:`~geovista.bridge.Transform.from_points` drops.
        crs : CRSLike, optional
            The Coordinate Reference System of the provided `points`, or `xs` and `ys`.
            May be anything accepted by :meth:`pyproj.crs.CRS.from_user_input`. Defaults
            to ``EPSG:4326`` i.e., ``WGS 84``.
        style : str, optional
            Visualization style of the points to be rendered. May be either ``points``
            or ``points_gaussian``. The ``points_gaussian`` option may be controlled
            with the ``emissive`` and ``render_points_as_spheres`` options in
            `kwargs`.
        height : ArrayLike or pint.Quantity, optional
            The height of each point, or one for every point, above mean sea
            level: in metres, in the unit `vertical_units` names, or a ``pint``
            quantity of length from any registry. The points are placed by them
            at the scene's globe. A missing point given with `xs` and `ys` is
            dropped with its height. Heights given for a `points` mesh that
            already carries them are refused.
        depth : ArrayLike or pint.Quantity, optional
            The depth of each point, or one for every point, positive downward,
            in the same forms as a `height`. Give a `height` or a `depth`, not
            both.
        vertical_units : str, optional
            The CF unit of a `height` or `depth` given as plain numbers.
            Defaults to metres.
        zlevel : int or ArrayLike, optional
            The z-axis level. Used in combination with the `zscale` to offset the
            render radius of the scene's globe by a proportional amount i.e.,
            ``render_radius * zlevel * zscale``.
            If `zlevel` is not a scalar, then its shape must match or broadcast
            with the shape of the `xs` and `ys`. Defaults to ``0``.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.
        **kwargs : dict, optional
            See :meth:`pyvista.Plotter.add_mesh`.

        Returns
        -------
        Actor or None
            The rendered actor added to the plotter scene, or ``None`` when the
            mesh is empty and nothing is added.

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

        # the heights given, passed on only when given
        heights: dict[str, Any] = {
            name: value
            for name, value in (
                ("height", height),
                ("depth", depth),
                ("vertical_units", vertical_units),
            )
            if value is not None
        }

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
                points = pv.wrap(points)

            mesh = points

            if "height" in heights or "depth" in heights:
                # a points mesh is given no z-level, so one given with heights
                # is refused rather than dropped (heights spec §4.4)
                _refuse_zlevel(zlevel)

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

            if scalars is not None and np.ndim(scalars) > 0:
                # the scalars of a missing point go with it, as from_points drops
                # it and warns (positions spec §4.5), its points paired in order
                px, py = map(np.ravel, _coordinates(xs, ys, crs))
                if px.size == py.size:
                    missing = _missing_positions(px, py, x_name="xs", y_name="ys")
                    if np.any(missing):
                        scalars = _cut_scalars(scalars, ~missing)

            # the points are built at their heights, and a missing point is
            # dropped with its height (positions spec §4.5)
            mesh = Transform.from_points(
                xs,
                ys,
                crs=crs,
                globe=self.globe,
                zlevel=zlevel,
                zscale=zscale,
                **heights,
            )
            heights = {}

        # defensive kwarg pop
        if "texture" in kwargs:
            _ = kwargs.pop("texture")

        return self.add_mesh(mesh, style=style, scalars=scalars, **heights, **kwargs)

    def view_poi(
        self,
        x: float | Quantity | None = None,
        y: float | Quantity | None = None,
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
        x : float or pint.Quantity, optional
            The spatial x-value point, in canonical `crs` units, of the POI.
            Defaults to ``0`` if unspecified and `y` has been provided,
            otherwise ``None``.
            A ``pint`` quantity, from any registry, carries its own units, and is read
            in those of the `crs`. Give `y` as a quantity too, unless it is left out.
        y : float or pint.Quantity, optional
            The spatial y-value point, in canonical `crs` units, of the POI.
            Defaults to ``0`` if unspecified and `x` has been provided,
            otherwise ``None``.
            A ``pint`` quantity, from any registry, carries its own units, and is read
            in those of the `crs`. Give `x` as a quantity too, unless it is left out.
        crs : CRSLike, optional
            The Coordinate Reference System of the POI. May be anything accepted by
            :meth:`pyproj.crs.CRS.from_user_input`. Defaults to ``EPSG:4326`` i.e.,
            ``WGS 84``.

        Raises
        ------
        ValueError
            If `x` or `y` is masked, NaN or infinite, as such a POI has no position.

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
        camera = self.camera

        if crs is None:
            crs = WGS84

        use_mesh_poi = x is None and y is None

        if not use_mesh_poi:
            # at the very least x or y has been provided
            # default any unset to 0, which allows the API to support the
            # convenience "view_poi(x=30)" instead of "view_poi(x=30, y=0)"
            if x is None or y is None:
                # in the units of the other, if it has any, as 0 is 0 in any unit,
                # and present, so a refusal never names the coordinate left out;
                # pint's quantity holds its units as a property, which the
                # protocol does not, so its test would narrow no type
                given: Any = y if x is None else x
                zero: float | Quantity = (
                    given.units * 0 if isinstance(given, _Quantity) else 0
                )
                if x is None:
                    x = zero
                if y is None:
                    y = zero
            px, py = _coordinates(x, y, crs, x_name="x", y_name="y")
            # a missing point-of-interest has no view (positions spec §4.3)
            _refuse_missing_poi(px, py, x_name="x", y_name="y")
            x, y = float(np.asarray(px)), float(np.asarray(py))

        if use_mesh_poi:
            if self._poi is None:
                # this is a no-op
                wmsg = "No point-of-interest (POI) is available or has been provided."
                warn(wmsg, stacklevel=2)
                return

            if not planar(self.crs):
                # convert cartesian xyz to lon/lat, on the scene's globe
                x, y = to_lonlat(self._poi, globe=self.globe)
                crs = WGS84
            else:
                x, y, _ = self._poi
                crs = self.crs

        # Assertion to appease MyPy.
        assert x is not None
        assert y is not None
        if crs != self.crs:
            x, y, _ = transform_point(src_crs=crs, tgt_crs=self.crs, x=x, y=y)

        if not planar(self.crs):
            camera.focal_point = (0, 0, 0)
            # convert POI lon/lat to cartesian xyz
            xyz = to_cartesian(x, y)[0]
            # calculate the unit vector
            u_hat = xyz / np.linalg.norm(xyz)
            # set the new camera position at the same magnitude from the focal point
            camera.position = u_hat * np.linalg.norm(camera.position)
            # typing spec §8 -- pyvista 0.49's _Wrapped drops the descriptor protocol
            reset_camera: Callable[..., None] = self.reset_camera
            reset_camera(render=False)
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
