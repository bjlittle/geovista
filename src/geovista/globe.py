# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""The globe a scene is drawn on.

A globe holds the Earth's radius, the radius it is drawn at, and the
exaggeration of heights above and below sea level.

Notes
-----
.. versionadded:: 0.6.0

"""

from __future__ import annotations

import functools
import math
from numbers import Real
from typing import TYPE_CHECKING, Any, NoReturn, cast

import lazy_loader as lazy

from .common import (
    _GV_GLOBE_FIELDS,
    GV_FIELD_GLOBE_EXAGGERATION_ABOVE,
    GV_FIELD_GLOBE_EXAGGERATION_BELOW,
    GV_FIELD_GLOBE_RADIUS,
    GV_FIELD_GLOBE_RENDER_RADIUS,
    GV_FIELD_RADIUS,
    GV_POINT_HEIGHT,
    RADIUS,
    _retired,
    _to_cartesian,
)
from .crs import _ellipsoidal_height, projected
from .units import _Quantity, as_quantity, to_metres

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import ArrayLike, NDArray
    import pyvista as pv

    from .crs import CRSLike
    from .units import Quantity

# lazy import third-party dependencies
np = lazy.load("numpy")

__all__ = ["Globe"]

# the relative spread of radii within which a mesh's points lie on a sphere
# (scene spec §4.4). It admits a sphere of float32 points, whose radii vary by
# some 6e-8, and refuses heights of more than about 6 m at the Earth's radius
_SPREAD: float = 1e-6


def _finite_and_positive(keyword: str, value: float, given: object) -> float:
    """Return a value that is finite and positive.

    Parameters
    ----------
    keyword : str
        The keyword the value was given as, to name it in a message.
    value : float
        The value, as a float.
    given : object
        The value as it was given, to show it in a message.

    Returns
    -------
    float
        The value.

    Raises
    ------
    ValueError
        If the value is not finite, or not positive.

    """
    if not math.isfinite(value) or value <= 0:
        emsg = f"{keyword} must be finite and positive, got {given!r}."
        raise ValueError(emsg)
    return value


def _ratio(keyword: str, value: object) -> float:
    """Read a plain number, such as a render radius or a factor, as a float.

    Parameters
    ----------
    keyword : str
        The keyword the value was given as, to name it in a message.
    value : object
        The value.

    Returns
    -------
    float
        The value, finite and positive.

    Raises
    ------
    TypeError
        If the value is not a plain number. A bool is not one, and nor is a
        string, which would otherwise be read as the number it spells.

    """
    if isinstance(value, bool) or not isinstance(value, Real):
        emsg = f"{keyword} must be a plain number, got {value!r}."
        raise TypeError(emsg)
    return _finite_and_positive(keyword, float(value), value)


def _length(value: object) -> float:
    """Read a radius, a plain number in metres or a ``pint`` quantity, as metres.

    Parameters
    ----------
    value : object
        The radius.

    Returns
    -------
    float
        The radius in metres, finite and positive.

    Raises
    ------
    TypeError
        If the radius is neither a plain number nor a ``pint`` quantity, or is
        a quantity of more than one length.

    """
    emsg = (
        "radius must be one length, a plain number in metres or a pint "
        f"quantity, got {value!r}."
    )
    if isinstance(value, bool):
        raise TypeError(emsg)
    if isinstance(value, Real):
        metres = float(value)
    elif hasattr(value, "magnitude") and hasattr(value, "units"):
        converted = to_metres(cast("Quantity", value))
        if not isinstance(converted, float):
            raise TypeError(emsg)
        metres = converted
    else:
        raise TypeError(emsg)
    return _finite_and_positive("radius", metres, value)


def _recorded(mesh: pv.DataSet, name: str) -> float:
    """Read a field that records one finite number.

    Parameters
    ----------
    mesh : pyvista.DataSet
        The mesh.
    name : str
        The name of the field.

    Returns
    -------
    float
        The number.

    Raises
    ------
    ValueError
        If the field is not one finite number.

    """
    values = np.asarray(mesh.field_data[name])
    if (
        values.shape != (1,)
        or values.dtype.kind not in "fiu"
        or not np.isfinite(values[0])
    ):
        emsg = f"The mesh's {name!r} must record one finite number, got {values!r}."
        raise ValueError(emsg)
    return float(values[0])


class Globe:  # numpydoc ignore=PR01
    """The globe a scene is drawn on.

    A globe is immutable and hashable, and two globes are equal when their
    values are.

    Notes
    -----
    .. versionadded:: 0.6.0

    Examples
    --------
    >>> from geovista import Globe
    >>> globe = Globe(exaggeration=20, exaggeration_below=100)
    >>> print(globe.radius.to("km"))
    6378.137 kilometer
    >>> globe.exaggeration, globe.exaggeration_below
    (20.0, 100.0)

    """

    __slots__ = ("_exaggeration", "_exaggeration_below", "_radius", "_render_radius")

    _exaggeration: float
    _exaggeration_below: float
    _radius: float
    _render_radius: float

    def __init__(
        self,
        *,
        radius: float | Quantity = 6378137.0,
        render_radius: float = RADIUS,
        exaggeration: float = 1.0,
        exaggeration_below: float | None = None,
    ) -> None:
        """Build a globe, checking each value.

        Parameters
        ----------
        radius : float or pint.Quantity, default=6378137.0
            The Earth's radius, by default the WGS84 semi-major axis. A plain
            number is in metres, and a ``pint`` quantity, from any registry,
            carries its own units. For a magnitude with a CF unit string, pass
            ``geovista.units.to_metres(6371, "km")``.
        render_radius : float, default=RADIUS
            The radius the globe is drawn at, in the units of the scene.
        exaggeration : float, default=1.0
            The factor for heights above sea level, and for depths below it
            too unless `exaggeration_below` is given. A factor need not be
            whole, and one below 1 flattens heights.
        exaggeration_below : float, optional
            The factor for depths below sea level, by default the
            `exaggeration`. Land below sea level, such as the shore of the
            Dead Sea, takes this factor too.

        Raises
        ------
        TypeError
            If a value is of the wrong type, such as a string or a bool, or a
            render radius or a factor is a quantity.
        ValueError
            If a value is not finite, or not positive.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        if exaggeration_below is None:
            exaggeration_below = exaggeration
        values = {
            "_radius": _length(radius),
            "_render_radius": _ratio("render_radius", render_radius),
            "_exaggeration": _ratio("exaggeration", exaggeration),
            "_exaggeration_below": _ratio("exaggeration_below", exaggeration_below),
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)

    def _values(self) -> tuple[float, float, float, float]:
        """Return the four values of the globe.

        Returns
        -------
        tuple of float
            The radius in metres, the render radius and the two factors.

        """
        return (
            self._radius,
            self._render_radius,
            self._exaggeration,
            self._exaggeration_below,
        )

    def __setattr__(self, name: str, value: object) -> NoReturn:
        """Refuse to change the globe, which is immutable.

        Parameters
        ----------
        name : str
            The attribute.
        value : object
            The value.

        Raises
        ------
        AttributeError
            Always.

        """
        emsg = f"A Globe cannot be changed, so build a new one, not set {name!r}."
        raise AttributeError(emsg)

    def __delattr__(self, name: str) -> NoReturn:
        """Refuse to change the globe, which is immutable.

        Parameters
        ----------
        name : str
            The attribute.

        Raises
        ------
        AttributeError
            Always.

        """
        emsg = f"A Globe cannot be changed, so cannot delete {name!r}."
        raise AttributeError(emsg)

    def __eq__(self, other: object) -> bool:
        """Compare the four values of two globes, exactly.

        Parameters
        ----------
        other : object
            The other globe.

        Returns
        -------
        bool
            Whether the globes are equal.

        """
        if not isinstance(other, Globe):
            return NotImplemented
        return self._values() == other._values()

    def __hash__(self) -> int:
        """Hash the four values of the globe.

        Returns
        -------
        int
            The hash.

        """
        return hash(self._values())

    def __reduce__(self) -> tuple[Any, ...]:
        """Rebuild the globe, so that it can be copied and pickled.

        Returns
        -------
        tuple
            The call that rebuilds the globe, which names each of its values,
            and an empty tuple of arguments.

        """
        rebuild = functools.partial(
            Globe,
            radius=self._radius,
            render_radius=self._render_radius,
            exaggeration=self._exaggeration,
            exaggeration_below=self._exaggeration_below,
        )
        return (rebuild, ())

    def __repr__(self) -> str:
        """Return the call that builds the globe.

        Returns
        -------
        str
            The call, with the radius as a plain number in metres.

        """
        return (
            f"Globe(radius={self._radius!r}, render_radius={self._render_radius!r}, "
            f"exaggeration={self._exaggeration!r}, "
            f"exaggeration_below={self._exaggeration_below!r})"
        )

    @classmethod
    def from_mesh(cls, mesh: pv.DataSet) -> Globe | None:
        """Read the globe a mesh records, without changing the mesh.

        A mesh that records no globe is read at its ``gvRadius``, as written
        before the globe, and otherwise at the one radius its points lie at,
        if they lie at one and the mesh is neither projected nor lifted by the
        heights it carries.

        Parameters
        ----------
        mesh : pyvista.DataSet
            The mesh.

        Returns
        -------
        Globe or None
            The globe, or ``None`` when it cannot be read, as for a mesh warped
            by its heights.

        Raises
        ------
        ValueError
            If the mesh records part of a globe, or a value that is not one
            finite and positive number.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        field_data = mesh.field_data
        missing = [name for name in _GV_GLOBE_FIELDS if name not in field_data]

        if len(missing) < len(_GV_GLOBE_FIELDS):
            if missing:
                emsg = (
                    "The mesh records part of a globe, without "
                    f"{', '.join(repr(name) for name in missing)}."
                )
                raise ValueError(emsg)
            return cls(
                radius=_recorded(mesh, GV_FIELD_GLOBE_RADIUS),
                render_radius=_recorded(mesh, GV_FIELD_GLOBE_RENDER_RADIUS),
                exaggeration=_recorded(mesh, GV_FIELD_GLOBE_EXAGGERATION_ABOVE),
                exaggeration_below=_recorded(mesh, GV_FIELD_GLOBE_EXAGGERATION_BELOW),
            )

        if GV_FIELD_RADIUS in field_data:
            return cls(render_radius=_recorded(mesh, GV_FIELD_RADIUS))

        # a mesh with heights lies at them, so heights all equal would read as a
        # globe at the lifted radius, and the mesh be lifted twice
        # (scene spec §4.4 item 2, heights spec §4.3)
        if GV_POINT_HEIGHT in mesh.point_data or mesh.n_points == 0 or projected(mesh):
            return None

        radii = np.linalg.norm(np.asarray(mesh.points, dtype=np.float64), axis=1)
        if not np.all(np.isfinite(radii)):
            return None

        low, high = float(radii.min()), float(radii.max())
        if high <= 0 or high - low > _SPREAD * high:
            return None

        radius = float(radii.mean())
        if mesh.points.dtype == np.float32:
            # a mean of float32 points is not exactly their radius, as
            # pv.Sphere() averages 1 +/- 6e-10, so round it as they were
            radius = float(np.float32(radius))

        return cls(render_radius=radius)

    def to_mesh(self, mesh: pv.DataSet) -> None:
        """Record the globe on a mesh, in place.

        The globe is written as four float64 fields of one value each, and
        replaces any ``gvRadius``.

        Parameters
        ----------
        mesh : pyvista.DataSet
            The mesh.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        record = {
            GV_FIELD_GLOBE_RADIUS: self._radius,
            GV_FIELD_GLOBE_RENDER_RADIUS: self._render_radius,
            GV_FIELD_GLOBE_EXAGGERATION_ABOVE: self._exaggeration,
            GV_FIELD_GLOBE_EXAGGERATION_BELOW: self._exaggeration_below,
        }
        for name, value in record.items():
            mesh.field_data[name] = np.array([value], dtype=np.float64)
        if GV_FIELD_RADIUS in mesh.field_data:
            del mesh.field_data[GV_FIELD_RADIUS]

    @property
    def radius(self) -> Quantity:
        """The Earth's radius.

        Returns
        -------
        pint.Quantity
            The radius in metres, a quantity in ``pint``'s application
            registry, so that it adds to quantities of a user's own. The first
            read imports ``pint``.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        return as_quantity(self._radius)

    @property
    def render_radius(self) -> float:
        """The radius the globe is drawn at.

        Returns
        -------
        float
            The radius, in the units of the scene.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        return self._render_radius

    @property
    def exaggeration(self) -> float:
        """The factor for heights above sea level.

        Returns
        -------
        float
            The factor.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        return self._exaggeration

    @property
    def exaggeration_below(self) -> float:
        """The factor for depths below sea level.

        Returns
        -------
        float
            The factor.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        return self._exaggeration_below

    @property
    def scale(self) -> float:
        """The render radius over the radius.

        Returns
        -------
        float
            The scale of the drawing, in units of the scene per metre.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        return self._render_radius / self._radius


def _resolve(globe: object, /) -> Globe:
    """Resolve the globe a function is given.

    Parameters
    ----------
    globe : object
        The globe given, or ``None``.

    Returns
    -------
    Globe
        The globe given, or the default globe when given ``None``.

    Raises
    ------
    TypeError
        When given anything but a globe or ``None``, such as a number a caller
        would once have given as a ``radius``.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if globe is None:
        return Globe()

    if not isinstance(globe, Globe):
        emsg = (
            f"globe must be a geovista.Globe, got {globe!r}. Draw a sphere of "
            "radius r with Globe(render_radius=r)."
        )
        raise TypeError(emsg)

    return globe


def _records(mesh: pv.DataSet, globe: Globe, /) -> bool:
    """Determine whether a mesh records exactly a globe, and no retired field.

    A mesh read at a globe it does not record, by its ``gvRadius`` or by
    measuring its points, does not record it.

    Parameters
    ----------
    mesh : pyvista.DataSet
        The mesh.
    globe : Globe
        The globe.

    Returns
    -------
    bool
        Whether the mesh records the globe in its four fields, and nothing a
        cleaning would change.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    field_data = mesh.field_data

    if _retired(mesh) or not all(name in field_data for name in _GV_GLOBE_FIELDS):
        return False

    return Globe.from_mesh(mesh) == globe


def _written(mesh: pv.DataSet, /) -> bool:
    """Determine whether a mesh records a globe, rather than lying at one.

    A mesh records its globe in its four fields, or in the ``gvRadius`` written
    before the globe. Any other mesh is read at the one radius its points lie
    at, which a sphere drawn above or below a globe shares with that globe.

    Parameters
    ----------
    mesh : pyvista.DataSet
        The mesh.

    Returns
    -------
    bool
        Whether the mesh has any of the four fields, or a ``gvRadius``.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    field_data = mesh.field_data

    return GV_FIELD_RADIUS in field_data or any(
        name in field_data for name in _GV_GLOBE_FIELDS
    )


def _heights(
    height: object,
    depth: object,
    vertical_units: str | None,
    /,
    *,
    crs: CRSLike | None = None,
) -> float | NDArray[np.float64] | None:
    """Read the heights a function is given, in metres above mean sea level.

    Parameters
    ----------
    height : object
        The heights given, or ``None``: a number or an array in metres, or in
        the unit `vertical_units` names, or a ``pint`` quantity of length.
    depth : object
        The depths given, or ``None``, positive downward, in the same forms.
    vertical_units : str, optional
        A CF unit string for a `height` or `depth` given as plain numbers.
    crs : CRSLike, optional
        The CRS of the points the heights are given for.

    Returns
    -------
    float or ndarray or None
        The heights in metres, NaN where one is masked or missing, or ``None``
        when neither a height nor a depth is given.

    Raises
    ------
    ValueError
        If both a height and a depth are given, `vertical_units` is given with
        neither or with a quantity, a height is infinite or not a length, or
        heights are given with a CRS whose height is above the ellipsoid.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if height is not None and depth is not None:
        emsg = "Give a height or a depth, not both, got both 'height' and 'depth'."
        raise ValueError(emsg)

    keyword, value = ("height", height) if depth is None else ("depth", depth)

    if value is None:
        if vertical_units is not None:
            emsg = (
                f"vertical_units={vertical_units!r} names the unit of a height or "
                "a depth, but neither was given."
            )
            raise ValueError(emsg)
        return None

    if vertical_units is not None and isinstance(value, _Quantity):
        emsg = (
            f"The {keyword} given is a quantity, with a unit of its own, so "
            f"takes no vertical_units, got vertical_units={vertical_units!r}."
        )
        raise ValueError(emsg)

    # a value that carries its units as an attribute, as an xarray DataArray or
    # a netCDF4 variable does, is refused here, naming the keyword these take
    own = None if isinstance(value, _Quantity) else getattr(value, "units", None)
    if own is not None:
        emsg = (
            f"The {keyword} given carries its own units, {own!r}, which geovista "
            "does not read from it. Pass its values, with their units as "
            f"vertical_units={own!r}."
        )
        raise ValueError(emsg)

    if crs is not None and _ellipsoidal_height(crs):
        emsg = (
            "Heights are above mean sea level, but the CRS "
            f"{getattr(crs, 'name', crs)!r} has an 'Ellipsoidal height' axis. "
            "Give a CRS whose height is gravity-related, such as 'EPSG:9705', or "
            "a horizontal one, such as 'EPSG:4326'."
        )
        raise ValueError(emsg)

    # a value that is not a length, or not numbers, is refused by to_metres
    metres = to_metres(cast("ArrayLike | Quantity", value), vertical_units)
    values = np.asarray(metres)
    infinite = np.isinf(values)

    if np.any(infinite):
        if values.ndim:
            index = int(np.flatnonzero(infinite)[0])
            emsg = (
                f"A {keyword} cannot be infinite, got {values.flat[index]} at "
                f"index {index}."
            )
        else:
            emsg = f"A {keyword} cannot be infinite, got {float(values)}."
        raise ValueError(emsg)

    return -metres if depth is not None else metres


def _for_points(
    heights: float | NDArray[np.float64], n_points: int, n_cells: int, /
) -> NDArray[np.float64]:
    """Return one height for each point of a mesh.

    Parameters
    ----------
    heights : float or ndarray
        The heights, in metres: one for the whole mesh, or one for each point.
    n_points : int
        The number of points of the mesh.
    n_cells : int
        The number of cells of the mesh, or of faces given to build it.

    Returns
    -------
    ndarray
        A new float64 array of one height for each point, in C order.

    Raises
    ------
    ValueError
        If the heights are one for each cell, or fit neither the points nor
        the whole mesh.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    values: NDArray[np.float64] = np.array(heights, dtype=np.float64).ravel()

    if values.size == 1:
        return np.full(n_points, values[0], dtype=np.float64)

    if values.size == n_points:
        return values

    if values.size == n_cells:
        emsg = (
            "Heights are given one for each point, got one for each of the "
            f"{n_cells:,} cells, which geovista does not draw yet (issue #2728)."
        )
        raise ValueError(emsg)

    emsg = (
        f"Require one height for each of the {n_points:,} points, or one for the "
        f"whole mesh, got {values.size:,}."
    )
    raise ValueError(emsg)


def _refuse_zlevel(zlevel: object, /) -> None:
    """Refuse a z-level other than 0, given with heights.

    Parameters
    ----------
    zlevel : object
        The z-level given, which is none when it is ``None``, 0 or all zeros.

    Raises
    ------
    ValueError
        If the z-level is other than 0.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if zlevel is not None and np.any(np.asarray(zlevel) != 0):
        emsg = (
            "A height and a z-level are never given together, since heights "
            f"place each point, got zlevel={zlevel!r}."
        )
        raise ValueError(emsg)


def _record_heights(mesh: pv.DataSet, heights: ArrayLike, /) -> None:
    """Record the heights of a mesh's points, in place.

    The heights are set apart from the active scalars, which they never
    become, so that ``threshold`` and ``add_mesh`` go on reading the data.

    Parameters
    ----------
    mesh : pyvista.DataSet
        The mesh.
    heights : ArrayLike
        One height for each point, in metres, NaN where one is missing.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    mesh.point_data.set_array(np.asarray(heights, dtype=np.float64), GV_POINT_HEIGHT)


def _carried_heights(mesh: pv.DataSet, /) -> NDArray[np.float64] | None:
    """Return the heights a mesh carries.

    Parameters
    ----------
    mesh : pyvista.DataSet
        The mesh.

    Returns
    -------
    ndarray or None
        The heights of its points, as float64, or ``None`` for a mesh without
        them.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if GV_POINT_HEIGHT not in mesh.point_data:
        return None

    heights: NDArray[np.float64] = np.asarray(
        mesh.point_data[GV_POINT_HEIGHT], dtype=np.float64
    )
    return heights


def _mapped(globe: Globe, heights: ArrayLike, /) -> NDArray[np.float64]:
    """Map heights through the vertical mapping of a globe.

    Parameters
    ----------
    globe : Globe
        The globe.
    heights : ArrayLike
        The heights, in metres.

    Returns
    -------
    ndarray
        The exaggerated heights, in metres: each above sea level by the
        `exaggeration`, each below it by the `exaggeration_below`, and each
        missing one as 0.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    values = np.asarray(heights, dtype=np.float64)
    mapped = np.where(
        values >= 0,
        globe.exaggeration * values,
        globe.exaggeration_below * values,
    )
    result: NDArray[np.float64] = np.where(np.isnan(values), 0.0, mapped)
    return result


def _subtended(globe: Globe, heights: ArrayLike, /) -> NDArray[np.float64]:
    """Return the angle each mapped height subtends at the globe's radius.

    Parameters
    ----------
    globe : Globe
        The globe.
    heights : ArrayLike
        The heights, in metres.

    Returns
    -------
    ndarray
        The angles, in radians, of each height mapped by :func:`_mapped`.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    # the radius in metres, read without the quantity, which would import pint
    radius = globe.render_radius / globe.scale
    result: NDArray[np.float64] = _mapped(globe, heights) / radius
    return result


def _on_globe(
    globe: Globe, lons: ArrayLike, lats: ArrayLike, heights: ArrayLike, /
) -> NDArray[np.float64]:
    """Place points at their heights on a globe.

    Each point lies at a radius of ``s (R + V(h))``, heights spec §4.3.

    Parameters
    ----------
    globe : Globe
        The globe.
    lons : ArrayLike
        The longitudes, in degrees, read flattened.
    lats : ArrayLike
        The latitudes, in degrees, read flattened.
    heights : ArrayLike
        One height for each point, in metres, read flattened.

    Returns
    -------
    ndarray
        The ``(N, 3)`` cartesian points.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    points: NDArray[np.float64] = _to_cartesian(
        np.ravel(lons),
        np.ravel(lats),
        radius=globe.render_radius,
        zlevel=_subtended(globe, np.ravel(heights)),
        zscale=1.0,
    )
    return points
