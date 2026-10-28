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
    RADIUS,
)
from .crs import projected
from .units import as_quantity, to_metres

if TYPE_CHECKING:
    import numpy as np
    import pyvista as pv

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
        if they lie at one and the mesh is not projected.

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

        if mesh.n_points == 0 or projected(mesh):
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
