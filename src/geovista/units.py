# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Read lengths and angles, and convert them to metres and degrees.

A length or an angle crosses the API boundary in one of three forms: a plain
number, in metres or degrees; a ``pint`` quantity, from any registry; or a
magnitude with a CF unit string, which ``pint-cf`` reads. Each is converted
once, here, so everything else works on plain floats and NumPy arrays.

A length goes back out through the API as a ``pint`` quantity in ``pint``'s
application registry, from :func:`as_quantity`, so that a user can add it to
quantities of their own.

Only this module imports ``pint``, and only when a quantity or a unit string
arrives or leaves, so a plain number never pays for it.

Notes
-----
.. versionadded:: 0.6.0

"""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING, Any, Protocol, cast, overload, runtime_checkable
import warnings

import lazy_loader as lazy

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import ArrayLike, NDArray
    import pint

# lazy import third-party dependencies. pint is bound here, unloaded, so that
# the Quantity alias resolves at runtime
np = lazy.load("numpy")
pint = lazy.load("pint")

__all__ = ["Quantity", "as_quantity", "to_degrees", "to_metres"]

type Quantity = pint.Quantity
"""Type alias for a ``pint`` quantity, which only this module may import."""

#: The decimal places of a degree an angle converted from another unit snaps to.
_GRID = 9

#: The furthest, in degrees, a converted angle snaps, well above the noise of a
#: conversion and well below any angle that means something on the globe.
_SNAP = 1e-11


@runtime_checkable
class _Quantity(Protocol):
    """A quantity from any ``pint`` registry, read by its attributes alone."""

    magnitude: Any
    units: Any


@cache
def _registry() -> pint.UnitRegistry:
    """Build the registry of ``pint-cf`` once, since each takes 60 ms.

    Returns
    -------
    pint.UnitRegistry
        The registry that reads every unit string.

    """
    import pint_cf  # noqa: PLC0415

    return pint_cf.cf_unitregistry()


def _magnitude(value: object) -> NDArray[np.float64]:
    """Return a value as float64, with each masked element NaN.

    Parameters
    ----------
    value : object
        A number or an array, perhaps masked.

    Returns
    -------
    ndarray
        The value as float64, never its fill value where it is masked.

    """
    result: NDArray[np.float64] = np.ma.filled(
        np.ma.asarray(value, dtype=np.float64), np.nan
    )
    return result


def _quantity(value: object, units: str | None) -> tuple[pint.Quantity, str] | None:
    """Read a value with units as a quantity in the registry of ``pint-cf``.

    Parameters
    ----------
    value : object
        A number, an array or a ``pint`` quantity from any registry.
    units : str, optional
        A CF unit string, for a value that is not a quantity.

    Returns
    -------
    tuple of (pint.Quantity, str) or None
        The quantity, and its unit as it was given, to name it in a message.
        ``None`` for a value with no units, without importing ``pint``.

    Raises
    ------
    ValueError
        If a quantity is given units as well, a value carries units of its
        own as an attribute, or a unit cannot be read.

    """
    is_quantity = isinstance(value, _Quantity)

    # a value that carries its units as an attribute, as an xarray DataArray
    # or a netCDF4 variable does, would otherwise be read as metres or degrees
    own = None if is_quantity else getattr(value, "units", None)

    if own is not None:
        emsg = (
            f"{type(value).__name__} carries its own units, '{own}', which "
            "geovista does not read from it. Pass its values, with their "
            "units as 'units'."
        )
        raise ValueError(emsg)

    if not is_quantity and units is None:
        return None

    if is_quantity and units is not None:
        emsg = "Give the units on the quantity or as 'units', not both."
        raise ValueError(emsg)

    from lark.exceptions import LarkError  # noqa: PLC0415
    from pint.errors import PintError  # noqa: PLC0415

    if isinstance(value, _Quantity):
        # pint's plain long form, "D", since a short form can read differently
        # in another registry, as "nmi", a nautical mile, reads as a nano mile.
        # str() follows the registry's display format, which may be short
        label = format(value.units, "D")
        magnitude = _magnitude(value.magnitude)
    else:
        label = str(units)
        magnitude = _magnitude(value)

    registry = _registry()

    try:
        # pint-cf warns of the COARDS placeholders, such as "level", which are
        # dimensionless, so are refused below with a message of their own
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            unit = registry.Unit(label)
    except (ArithmeticError, LarkError, PintError, ValueError) as err:
        # pint-cf raises ZeroDivisionError for a unit such as "m/0"
        emsg = f"{label!r} is not a unit geovista can read."
        raise ValueError(emsg) from err

    return registry.Quantity(magnitude, unit), label


def _result(values: NDArray[np.float64]) -> float | NDArray[np.float64]:
    """Return a 0-d array as a Python float, and any other array as it is.

    Parameters
    ----------
    values : ndarray
        The converted values.

    Returns
    -------
    float or ndarray
        A float for a 0-d array, else the array.

    """
    return float(values) if values.ndim == 0 else values


@overload
def to_degrees(
    value: float,
    units: str | None = None,
) -> float: ...  # numpydoc ignore=GL08


@overload
def to_degrees(
    value: ArrayLike | Quantity, units: str | None = None
) -> float | NDArray[np.float64]: ...  # numpydoc ignore=GL08


def to_degrees(
    value: ArrayLike | Quantity, units: str | None = None
) -> float | NDArray[np.float64]:
    """Read an angle, and convert it to degrees.

    Parameters
    ----------
    value : float, ArrayLike or pint.Quantity
        The angle. A plain number or array is in degrees, unless `units` names
        another unit. A ``pint`` quantity, from any registry, carries its
        own units. A masked element becomes NaN.
    units : str, optional
        A CF unit string for a plain `value`, such as ``"degrees_north"`` or
        ``"radian"``, read by ``pint-cf``.

    Returns
    -------
    float or ndarray
        The angle in degrees, a float for a scalar, else a float64 array.

    Raises
    ------
    ValueError
        If the units are not angular, cannot be read, or are given both on a
        quantity and as `units`, or if `value` carries units of its own as an
        attribute, as an xarray DataArray does. ``pint`` counts an angle as
        dimensionless, so a dimensionless unit is refused, rather than read as
        radians.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    parsed = _quantity(value, units)

    if parsed is None:
        return _result(_magnitude(value))

    quantity, label = parsed
    registry = _registry()
    _, base = registry.get_base_units(quantity.units)

    # an angle is a unit whose base is the radian, since pint would otherwise
    # read a dimensionless "1", "percent" or "m/m" as radians without a word
    if base == registry.Unit("radian"):
        degrees: NDArray[np.float64] = quantity.to("degree").magnitude
        return _result(degrees)

    if quantity.dimensionless:
        emsg = (
            f"{label!r} is dimensionless, and an angle needs an angular unit, "
            "such as 'degree' or 'radian'."
        )
        raise ValueError(emsg)

    emsg = f"{label!r} is not an angle, so cannot be read in degrees."
    raise ValueError(emsg)


@overload
def to_metres(
    value: float, units: str | None = None
) -> float: ...  # numpydoc ignore=GL08


@overload
def to_metres(
    value: ArrayLike | Quantity, units: str | None = None
) -> float | NDArray[np.float64]: ...  # numpydoc ignore=GL08


def to_metres(
    value: ArrayLike | Quantity, units: str | None = None
) -> float | NDArray[np.float64]:
    """Read a length, and convert it to metres.

    Parameters
    ----------
    value : float, ArrayLike or pint.Quantity
        The length. A plain number or array is in metres, unless `units` names
        another unit. A ``pint`` quantity, from any registry, carries its
        own units. A masked element becomes NaN.
    units : str, optional
        A CF unit string for a plain `value`, such as ``"km"`` or ``"ft"``,
        read by ``pint-cf``.

    Returns
    -------
    float or ndarray
        The length in metres, a float for a scalar, else a float64 array.

    Raises
    ------
    ValueError
        If the units are not a length, cannot be read, or are given both on a
        quantity and as `units`, or if `value` carries units of its own as an
        attribute, as an xarray DataArray does.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    parsed = _quantity(value, units)

    if parsed is None:
        return _result(_magnitude(value))

    quantity, label = parsed

    if quantity.dimensionality != _registry().Unit("meter").dimensionality:
        emsg = f"{label!r} is not a length, so cannot be read in metres."
        raise ValueError(emsg)

    metres: NDArray[np.float64] = quantity.to("meter").magnitude

    return _result(metres)


def as_quantity(metres: float) -> Quantity:
    """Return a length in metres as a quantity in ``pint``'s application registry.

    The application registry is the one ``pint`` provides for sharing
    quantities between packages. It is read at each call, so a registry set
    with ``pint.set_application_registry`` is honoured.

    Parameters
    ----------
    metres : float
        The length, in metres.

    Returns
    -------
    pint.Quantity
        The length in metres, with a float magnitude.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    import pint  # noqa: PLC0415

    # the object pint.set_application_registry swaps the registry inside
    quantity: pint.Quantity = pint.application_registry.Quantity(float(metres), "m")
    return quantity


def _masked(
    values: float | NDArray[np.float64], quantity: Quantity
) -> float | NDArray[np.float64]:
    """Give converted values the mask of the magnitude of their quantity.

    A conversion leaves a masked element as NaN, and a masked point has no
    position, so its mask is given back.

    Parameters
    ----------
    values : float or ndarray
        The converted values.
    quantity : pint.Quantity
        The quantity they were converted from.

    Returns
    -------
    float or ndarray
        The values, masked where the magnitude of `quantity` is.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    mask = np.ma.getmask(quantity.magnitude)
    return values if mask is np.ma.nomask else np.ma.masked_array(values, mask=mask)


def _read_angle(
    name: str, value: Quantity, *, radians: bool
) -> float | NDArray[np.float64]:
    """Read a quantity that is an angle, naming its argument if it is not one.

    A value within :data:`_SNAP` degrees of a number of :data:`_GRID` decimal
    places is taken as that number, so that a whole number of degrees given in
    radians reads as that number. The conversion leaves 30 degrees in radians as
    29.999999999999996 degrees, which would draw an extra line of a graticule, or
    label one a degree down. The snap moves a position by a micrometre at most.

    Parameters
    ----------
    name : str
        The name of the argument `value` was given as.
    value : pint.Quantity
        The angle.
    radians : bool
        Whether to read it in radians, rather than in degrees.

    Returns
    -------
    float or ndarray
        The angle, masked where the magnitude of `value` is.

    Raises
    ------
    ValueError
        If `value` is not an angle, or its units cannot be read.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    try:
        degrees = to_degrees(value)
    except ValueError as err:
        emsg = f"Cannot read {name!r} as an angle: {err}"
        raise ValueError(emsg) from err

    snapped = np.round(degrees, _GRID)
    degrees = np.where(np.abs(degrees - snapped) <= _SNAP, snapped, degrees)
    result: NDArray[np.float64] = np.radians(degrees) if radians else degrees
    return _masked(float(result) if result.ndim == 0 else result, value)


@overload
def _angle(
    name: str, value: None, *, radians: bool = ...
) -> None: ...  # numpydoc ignore=GL08


@overload
def _angle(
    name: str, value: float | Quantity, *, radians: bool = ...
) -> float: ...  # numpydoc ignore=GL08


def _angle(
    name: str, value: float | Quantity | None, *, radians: bool = False
) -> float | None:
    """Read an argument that is one angle, given as a number or a quantity.

    Parameters
    ----------
    name : str
        The name of the argument, to name it in a message.
    value : float or pint.Quantity, optional
        The angle. A plain number, or ``None``, is returned as it is given.
    radians : bool, default=False
        Whether to read a quantity in radians, rather than in degrees.

    Returns
    -------
    float, optional
        The angle.

    Raises
    ------
    ValueError
        If a quantity is not an angle, or its units cannot be read.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    # pint's quantity holds its magnitude and units as properties, which the
    # protocol does not, so a test of it narrows no type
    quantity = isinstance(value, _Quantity)
    if not quantity:
        return cast("float | None", value)
    return float(_read_angle(name, cast("Quantity", value), radians=radians))


def _angle_array(
    name: str, value: ArrayLike | Quantity, *, radians: bool = False
) -> ArrayLike:
    """Read an argument that is an array of angles, given plain or as a quantity.

    Parameters
    ----------
    name : str
        The name of the argument, to name it in a message.
    value : ArrayLike or pint.Quantity
        The angles. Plain numbers are returned as they are given.
    radians : bool, default=False
        Whether to read a quantity in radians, rather than in degrees.

    Returns
    -------
    ArrayLike
        The angles, masked where the magnitude of a quantity is.

    Raises
    ------
    ValueError
        If a quantity is not an angle, or its units cannot be read.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    quantity = isinstance(value, _Quantity)
    if not quantity:
        return cast("ArrayLike", value)
    return _read_angle(name, cast("Quantity", value), radians=radians)


def _both(x_name: str, x: object, y_name: str, y: object) -> bool:
    """Decide whether the coordinates of a position are given as quantities.

    Both or neither may be, as a plain number beside a quantity is more likely a
    mistake than a number in the documented unit (crs spec §8 item 13).

    Parameters
    ----------
    x_name : str
        The name of the argument `x` was given as.
    x : object
        The x-values, or longitudes.
    y_name : str
        The name of the argument `y` was given as.
    y : object
        The y-values, or latitudes.

    Returns
    -------
    bool
        Whether both are quantities.

    Raises
    ------
    ValueError
        If only one of them is a quantity.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    x_quantity, y_quantity = isinstance(x, _Quantity), isinstance(y, _Quantity)

    if x_quantity != y_quantity:
        alone = x_name if x_quantity else y_name
        emsg = (
            f"Give {x_name!r} and {y_name!r} both as pint quantities, or neither, "
            f"got {alone!r} alone."
        )
        raise ValueError(emsg)

    return x_quantity


def _lonlats(
    lons: ArrayLike | Quantity,
    lats: ArrayLike | Quantity,
    *,
    lon_name: str = "lons",
    lat_name: str = "lats",
    radians: bool = False,
) -> tuple[ArrayLike, ArrayLike]:
    """Read the longitudes and latitudes of points, given plain or as quantities.

    Parameters
    ----------
    lons : ArrayLike or pint.Quantity
        The longitudes.
    lats : ArrayLike or pint.Quantity
        The latitudes.
    lon_name : str, default="lons"
        The name of the argument `lons` was given as.
    lat_name : str, default="lats"
        The name of the argument `lats` was given as.
    radians : bool, default=False
        Whether to read quantities in radians, rather than in degrees.

    Returns
    -------
    tuple of ArrayLike
        The longitudes and the latitudes.

    Raises
    ------
    ValueError
        If only one of them is a quantity, or either is not an angle.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if not _both(lon_name, lons, lat_name, lats):
        return cast("ArrayLike", lons), cast("ArrayLike", lats)

    return (
        _angle_array(lon_name, lons, radians=radians),
        _angle_array(lat_name, lats, radians=radians),
    )
