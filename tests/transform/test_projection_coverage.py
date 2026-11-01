# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Record which projections take a global mesh cleanly, see crs spec §6.

Every projection method PROJ offers, and every projection class of ``cartopy``,
projects a global 5° mesh through :func:`geovista.transform.transform_mesh`, and is
measured as crs spec §3.1 measured it. The ledger records which work. A method
whose outcome changes fails here until the ledger changes with it, so coverage
can grow but never shrink by accident.

"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any
import warnings

import cartopy.crs as ccrs
import numpy as np
from packaging.version import Version
import pyproj
import pytest
import pyvista as pv

import geovista as gv
from geovista.common import from_cartesian
from geovista.crs import from_wkt
from geovista.transform import transform_mesh

if TYPE_CHECKING:
    from numpy.typing import NDArray

#: The section of the repository checks page that documents this check.
CHECK = "projection-coverage"

#: The version of PROJ that pyproj runs.
PROJ = Version(pyproj.proj_version_str)

#: The methods that project a global mesh cleanly, measured on 2026-10-24.
WORKS: frozenset[str] = frozenset(
    [
        "adams_ws1",
        "adams_ws2",
        "aea",
        "aitoff",
        "apian",
        "boggs",
        "bonne",
        "cea",
        "col_urban",
        "collg",
        "comill",
        "crast",
        "denoy",
        "eck1",
        "eck2",
        "eck3",
        "eck4",
        "eck5",
        "eck6",
        "eqc",
        "eqdc",
        "eqearth",
        "euler",
        "fahey",
        "fouc",
        "fouc_s",
        "gall",
        "gins8",
        "gn_sinu",
        "goode",
        "hammer",
        "hatano",
        "hourglass",
        "kav5",
        "kav7",
        "lagrng",
        "larr",
        "lask",
        "lcca",
        "leac",
        "loxim",
        "mbt_fps",
        "mbt_s",
        "mbtfpp",
        "mbtfpq",
        "mbtfps",
        "mill",
        "moll",
        "murd1",
        "murd3",
        "natearth",
        "natearth2",
        "nell",
        "nell_h",
        "ortel",
        "patterson",
        "poly",
        "putp1",
        "putp2",
        "putp3",
        "putp3p",
        "putp4p",
        "putp5",
        "putp5p",
        "putp6",
        "putp6p",
        "qua_aut",
        "robin",
        "rouss",
        "rpoly",
        "sinu",
        "times",
        "tissot",
        "urm5",
        "urmfps",
        "vandg",
        "vandg2",
        "vandg3",
        "vandg4",
        "vitk1",
        "wag1",
        "wag2",
        "wag3",
        "wag4",
        "wag5",
        "wag6",
        "wag7",
        "weren",
        "wink1",
        "wink2",
        "wintri",
    ]
)

#: The methods that fail, by their class of crs spec §3.2, or ``None`` for a method
#: no class holds yet.
_FAILING: dict[int | None, str] = {
    1: "merc webmerc tobmerc cc calcofi lcc ccon pconic murd2",
    2: (
        "ortho gnom nsper tpers geos stere ups sterea laea aeqd airy nicol "
        "adams_hemi alsk gs48 gs50 lee_os mil_os"
    ),
    3: (
        "tmerc etmerc utm gstmerc cass tcc tcea omerc somerc labrd ocea oea krovak "
        "mod_krovak nzmg bipc imw_p sch som lsat misrsom"
    ),
    4: "ob_tran bertin1953 tpeqd chamb",
    5: "igh igh_o imoll imoll_o peirce_q guyou healpix rhealpix interrupted",
    6: "isea ivea dsea tsea airocean spilhaus s2 qsc",
    None: "august bacon",
}

#: Each method that fails, and its class of crs spec §3.2.
FAILS: dict[str, int | None] = {
    method: kind for kind, methods in _FAILING.items() for method in methods.split()
}

#: Every projection method, of those PROJ classifies in ``proj -lP``.
METHODS: frozenset[str] = WORKS | frozenset(FAILS)

#: The operations PROJ offers that are not projections.
NOT_PROJECTIONS: frozenset[str] = frozenset(
    [
        "affine",
        "axisswap",
        "cart",
        "defmodel",
        "deformation",
        "geoc",
        "geocent",
        "geogoffset",
        "gridshift",
        "helmert",
        "hgridshift",
        "horner",
        "latlon",
        "latlong",
        "longlat",
        "lonlat",
        "molobadekas",
        "molodensky",
        "noop",
        "pipeline",
        "pop",
        "push",
        "set",
        "tinshift",
        "tmerczoned",
        "topocentric",
        "unitconvert",
        "vertoffset",
        "vgridshift",
        "xyzgridshift",
    ]
)

#: The methods newer than the PROJ that pyproj's wheels bundle, and the version of
#: PROJ each arrived in.
SINCE: dict[str, str] = {
    "dsea": "9.9.0",
    "hourglass": "9.9.0",
    "interrupted": "9.9.0",
    "ivea": "9.9.0",
    "tsea": "9.9.0",
}

#: The typical parameters a method needs before PROJ will build it.
PARAMETERS: dict[str, str] = {
    **dict.fromkeys(
        [
            "aea",
            "eqdc",
            "euler",
            "imw_p",
            "lcc",
            "murd1",
            "murd2",
            "murd3",
            "pconic",
            "tissot",
            "vitk1",
        ],
        "+lat_1=20 +lat_2=60",
    ),
    **dict.fromkeys(["bonne", "ccon"], "+lat_1=45"),
    "lcca": "+lat_0=35",
    "chamb": "+lat_1=10 +lon_1=30 +lon_2=40",
    "geos": "+h=35785831",
    "nsper": "+h=3000000",
    "tpers": "+h=5500000 +tilt=30 +azi=20",
    "gn_sinu": "+m=2 +n=3",
    "interrupted": "+base=sinu",
    "labrd": "+lat_0=-18.9 +lon_0=46.4372083 +azi=18.9 +k_0=0.9995",
    "lsat": "+lsat=2 +path=2",
    "misrsom": "+path=1",
    "ob_tran": "+o_proj=moll +o_lat_p=45 +o_lon_p=-90",
    "oea": "+m=1 +n=2",
    "omerc": "+lat_0=45 +lonc=0 +alpha=30",
    "sch": "+plat_0=30 +plon_0=0 +phdg_0=0",
    "tpeqd": "+lat_1=0 +lon_1=0 +lat_2=60 +lon_2=60",
    "urm5": "+n=0.9 +alpha=2 +q=4",
    "urmfps": "+n=0.5",
    "utm": "+zone=30",
}

#: The projection classes of cartopy that project a global mesh cleanly.
CARTOPY_WORKS: frozenset[str] = frozenset(
    [
        "Aitoff",
        "AlbersEqualArea",
        "EckertI",
        "EckertII",
        "EckertIII",
        "EckertIV",
        "EckertV",
        "EckertVI",
        "EqualEarth",
        "EquidistantConic",
        "Hammer",
        "LambertCylindrical",
        "Miller",
        "Mollweide",
        "PlateCarree",
        "Robinson",
        "Sinusoidal",
    ]
)

#: The projection classes of cartopy that fail, by their class of crs spec §3.2.
_CARTOPY_FAILING: dict[int, str] = {
    1: "Mercator LambertConformal LambertZoneII",
    2: (
        "Orthographic Gnomonic NearsidePerspective Geostationary Stereographic "
        "NorthPolarStereo SouthPolarStereo LambertAzimuthalEqualArea "
        "AzimuthalEquidistant"
    ),
    3: "TransverseMercator UTM OSGB OSNI EuroPP ObliqueMercator",
    4: "RotatedPole",
    5: "InterruptedGoodeHomolosine",
    6: "Spilhaus",
}

#: Each projection class of cartopy that fails, and its class of crs spec §3.2.
CARTOPY_FAILS: dict[str, int] = {
    name: kind for kind, names in _CARTOPY_FAILING.items() for name in names.split()
}

#: Every projection class of cartopy.
CARTOPY_CLASSES: frozenset[str] = CARTOPY_WORKS | frozenset(CARTOPY_FAILS)

#: The point array carrying each point's latitude through the cut of the seam.
LATITUDE = "gvCoverageLatitude"

#: A coordinate further out than this, in metres, has run away.
RUNAWAY = 1e8

#: A cell's area below this fraction of the median is too small to have a sign.
FOLD = 1e-9

#: A cell spanning more than this fraction of the projection is torn.
SPAN = 0.5

#: An edge longer than this multiple of the median of its band is torn.
EDGE = 10


def _crs(method: str) -> pyproj.CRS:
    """Build the CRS of a PROJ method, with the parameters it needs."""
    return pyproj.CRS(f"+proj={method} {PARAMETERS.get(method, '')}".strip())


def _cartopy(name: str) -> ccrs.Projection:
    """Build a projection class of cartopy, with the arguments it needs."""
    projection = getattr(ccrs, name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return projection(zone=30) if name == "UTM" else projection()


def _mesh() -> pv.PolyData:
    """Build the global 5° mesh, carrying the latitude of each point."""
    mesh = gv.Transform.from_1d(np.arange(-180, 181, 5.0), np.arange(-90, 91, 5.0))
    mesh.point_data[LATITUDE] = from_cartesian(mesh)[:, 1]
    return mesh


def _cells(mesh: pv.PolyData) -> tuple[NDArray[Any], NDArray[Any], NDArray[Any]]:
    """Find each cell's point ids, where each cell starts, and each vertex's next."""
    polys = mesh.GetPolys()
    offsets = np.asarray(pv.convert_array(polys.GetOffsetsArray()))
    ids = np.asarray(pv.convert_array(polys.GetConnectivityArray()))
    starts, ends = offsets[:-1], offsets[1:]
    following = np.arange(ids.size) + 1
    following[ends - 1] = starts
    return ids, starts, following


def _metres(crs: pyproj.CRS) -> float:
    """Find the metres in one unit of a CRS's horizontal axes.

    Parameters
    ----------
    crs : CRS
        The CRS of a projected mesh.

    Returns
    -------
    float
        The metres in one unit of its first axis. A unit of a geographic CRS is an
        angle, measured along the equator.

    """
    factor = crs.axis_info[0].unit_conversion_factor

    if not crs.is_geographic:
        return float(factor)

    # pyproj gives the coordinates of an axis declared in radians in degrees
    radians = np.radians(1.0) if factor == 1.0 else factor
    return float(radians * crs.ellipsoid.semi_major_metre)


def outcome(crs: pyproj.CRS | ccrs.Projection) -> tuple[str, str]:
    """Measure how a CRS takes the global 5° mesh, as crs spec §3.1 does.

    Parameters
    ----------
    crs : CRS or cartopy Projection
        The target of the projection.

    Returns
    -------
    tuple of str
        The first failure found, as its kind and a detail, or ``("works", "")``.

    """
    mesh = _mesh()

    with warnings.catch_warnings():
        # the outcome is geometric, so a warning, such as of an area of use, is not
        warnings.simplefilter("ignore")
        try:
            result = transform_mesh(mesh, crs)
        except Exception as error:  # noqa: BLE001
            return "raises", type(error).__name__

    return _measure(result)


def _measure(result: pv.PolyData) -> tuple[str, str]:
    """Measure a projected mesh for the failures of crs spec §3.1, in order.

    Parameters
    ----------
    result : PolyData
        The global 5° mesh, projected.

    Returns
    -------
    tuple of str
        The first failure found, as its kind and a detail, or ``("works", "")``.

    """
    points: NDArray[Any] = np.asarray(result.points)

    # every coordinate of every point, its height included
    if not np.all(np.isfinite(points)):
        return "non-finite", ""

    xy = points[:, :2]
    crs = from_wkt(result)
    assert crs is not None

    if np.abs(xy).max() * _metres(crs) > RUNAWAY:
        return "runaway", ""

    ids, starts, following = _cells(result)
    x, y = xy[ids, 0], xy[ids, 1]
    xn, yn = xy[ids[following], 0], xy[ids[following], 1]
    areas = 0.5 * np.add.reduceat(x * yn - xn * y, starts)
    scale = np.median(np.abs(areas[areas != 0]))
    signs = np.sign(areas[np.abs(areas) > FOLD * scale])

    if np.any(signs > 0) and np.any(signs < 0):
        minority = min(np.sum(signs > 0), np.sum(signs < 0))
        return "folded", f"{minority} cells"

    width, height = np.ptp(xy[:, 0]), np.ptp(xy[:, 1])
    cell_width = np.maximum.reduceat(x, starts) - np.minimum.reduceat(x, starts)
    cell_height = np.maximum.reduceat(y, starts) - np.minimum.reduceat(y, starts)

    if np.any(cell_width > SPAN * width) or np.any(cell_height > SPAN * height):
        return "torn", "span"

    latitudes = np.round(np.asarray(result.point_data[LATITUDE]), 6)
    bands = np.sort(np.vstack([latitudes[ids], latitudes[ids[following]]]), axis=0)
    _, band = np.unique(bands.T, axis=0, return_inverse=True)
    lengths = np.hypot(xn - x, yn - y)
    order = np.argsort(band, kind="stable")
    counts = np.bincount(band)
    for group in np.split(lengths[order], np.cumsum(counts)[:-1]):
        median = np.median(group)
        if median > 0 and np.any(group > EDGE * median):
            return "torn", "edge"

    return "works", ""


def test_methods_are_the_projections_proj_offers():
    """Every projection PROJ offers is in the ledger, and nothing else is."""
    offered = set(pyproj.list.get_proj_operations_map())
    unknown = sorted(offered - METHODS - NOT_PROJECTIONS)
    assert not unknown, (
        f"PROJ offers {', '.join(unknown)}, which the ledger does not hold: "
        "measure it into WORKS or FAILS, or add it to NOT_PROJECTIONS"
    )
    newer = {m for m in METHODS - offered if Version(SINCE.get(m, "0")) > PROJ}
    assert METHODS - offered == newer


def test_cartopy_classes_are_the_projections_cartopy_offers():
    """Every projection class cartopy offers is in the ledger, and nothing else is."""
    offered = {
        name
        for name, value in vars(ccrs).items()
        if inspect.isclass(value)
        and issubclass(value, ccrs.Projection)
        and value is not ccrs.Projection
        and not name.startswith("_")
    }
    assert offered == CARTOPY_CLASSES


def test_ledger_partitions_every_method():
    """Each method and class either works or fails, with its class of failure."""
    assert WORKS.isdisjoint(FAILS)
    assert WORKS | set(FAILS) == METHODS
    assert set(FAILS.values()) <= {1, 2, 3, 4, 5, 6, None}
    assert CARTOPY_WORKS.isdisjoint(CARTOPY_FAILS)
    assert CARTOPY_WORKS | set(CARTOPY_FAILS) == CARTOPY_CLASSES
    assert set(CARTOPY_FAILS.values()) <= {1, 2, 3, 4, 5, 6}


@pytest.mark.parametrize("method", sorted(METHODS))
def test_method_outcome(method):
    """A method works exactly when the ledger says it does.

    Holds crs spec §2 decision 12.
    """
    if method in SINCE and Version(SINCE[method]) > PROJ:
        pytest.skip(f"{method} arrived in PROJ {SINCE[method]}")

    kind, detail = outcome(_crs(method))

    if method in WORKS:
        assert kind == "works", f"{method} no longer works ({kind}: {detail})"
    else:
        assert kind != "works", f"{method} now works: move it from FAILS to WORKS"


@pytest.mark.parametrize("name", sorted(CARTOPY_CLASSES))
def test_cartopy_outcome(name):
    """A projection class of cartopy works exactly when the ledger says it does.

    Holds crs spec §2 decision 12.
    """
    kind, detail = outcome(_cartopy(name))

    if name in CARTOPY_WORKS:
        assert kind == "works", f"{name} no longer works ({kind}: {detail})"
    else:
        assert kind != "works", (
            f"{name} now works: move it from CARTOPY_FAILS to CARTOPY_WORKS"
        )


@pytest.mark.parametrize(
    ("method", "kind"),
    [
        ("ortho", "raises"),
        ("merc", "runaway"),
        ("aeqd", "folded"),
        ("igh", "torn"),
        ("stere", "non-finite"),
    ],
)
def test_every_failure_kind_is_detected(method, kind):
    """Each measure of a failure still fires, on a method that fails by it."""
    assert outcome(_crs(method))[0] == kind


def test_a_non_finite_height_is_measured():
    """A point whose z is not finite fails, as crs spec §3.1 requires of every point."""
    result = transform_mesh(_mesh(), _crs("eqc"))
    result.points[0, 2] = np.nan

    assert _measure(result)[0] == "non-finite"


def test_runaway_is_measured_in_metres():
    """The runaway limit is in metres, whatever unit the projection's axes are in.

    The axes of cartopy's LambertCylindrical are in units of 111,319.49 m, so its
    coordinates scaled by a thousand run 2 x 10¹⁰ m out, beyond the limit.

    """
    result = transform_mesh(_mesh(), _cartopy("LambertCylindrical"))
    result.points[:, :2] *= 1000

    assert _measure(result)[0] == "runaway"
