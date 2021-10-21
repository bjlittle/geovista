from collections.abc import Iterable
from typing import List, Optional, Tuple

import numpy as np
from numpy.typing import ArrayLike
import pyproj
import pyvista as pv

from .common import to_xyz, wrap
from .log import get_logger

__all__ = ["bbox", "geodesic", "geodesic_by_idx"]

# Configure the logger.
logger = get_logger(__name__)

#: Geodesic ellipse for manifold creation. See :func:`pyproj.get_ellps_map`.
MANIFOLD_ELLIPSE: str = "WGS84"

#: Number of equally spaced geodesic points between/including endpoint/s.
MANIFOLD_NPTS: int = 50


def geodesic(
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
    npts: Optional[int] = MANIFOLD_NPTS,
    radians: Optional[bool] = False,
    include_start: Optional[bool] = True,
    include_end: Optional[bool] = True,
    geod: Optional[pyproj.Geod] = None,
) -> Tuple[List[float], List[float]]:
    """
    TBD

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if geod is None:
        geod = pyproj.Geod(ellps=MANIFOLD_ELLIPSE)

    initial_idx = 0 if include_start else 1
    terminus_idx = 0 if include_end else 1

    glonlats = geod.npts(
        start_lon,
        start_lat,
        end_lon,
        end_lat,
        npts,
        radians=radians,
        initial_idx=initial_idx,
        terminus_idx=terminus_idx,
    )
    glons, glats = zip(*glonlats)
    glons = list(wrap(glons))

    return glons, glats


def geodesic_by_idx(
    longitudes: ArrayLike,
    latitudes: ArrayLike,
    start_idx: int,
    end_idx: int,
    npts: Optional[int] = MANIFOLD_NPTS,
    radians: Optional[bool] = False,
    include_start: Optional[bool] = True,
    include_end: Optional[bool] = True,
    geod: Optional[pyproj.Geod] = None,
) -> Tuple[List[float], List[float]]:
    """
    TBD

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if geod is None:
        geod = pyproj.Geod(ellps=MANIFOLD_ELLIPSE)

    start_lonlat = longitudes[start_idx], latitudes[start_idx]
    end_lonlat = longitudes[end_idx], latitudes[end_idx]

    result = geodesic(
        *start_lonlat,
        *end_lonlat,
        npts=npts,
        radians=radians,
        include_start=include_start,
        include_end=include_end,
        geod=geod,
    )

    return result


def bbox(
    longitudes: ArrayLike,
    latitudes: ArrayLike,
    npts: Optional[int] = MANIFOLD_NPTS,
    ellps: Optional[str] = MANIFOLD_ELLIPSE,
    radius: Optional[float] = 1.0,
) -> pv.PolyData:
    """
    TBD

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if not isinstance(longitudes, Iterable):
        longitudes = [longitudes]
    if not isinstance(latitudes, Iterable):
        latitudes = [latitudes]

    lons = np.asanyarray(longitudes)
    lats = np.asanyarray(latitudes)
    n_lons, n_lats = lons.size, lats.size

    if n_lons != n_lats:
        emsg = (
            f"Require the same number of longitudes ({n_lons}) and "
            f"latitudes ({n_lats})."
        )
        raise ValueError(emsg)

    if n_lons < 4:
        emsg = (
            "Require a bbox geometry containing at least 4 longitude/latitude "
            f"values to create the bbox manifold, only got {n_lons}."
        )
        raise ValueError(emsg)

    if n_lons > 5:
        emsg = (
            "Require a bbox geometry containing 4 (open) or 5 (closed) "
            f"longitude/latitude values to create the bbox manifold, got {n_lons}."
        )
        raise ValueError(emsg)

    #
    # TODO: lon/lat range check i.e., (0, 180]
    #

    # ensure the specified bbox geometry is open
    if np.isclose(lons[0], lons[-1]) and np.isclose(lats[0], lats[-1]):
        lons, lats = lons[-1], lats[-1]

    geom_lons, geom_lats = [], []
    geod = pyproj.Geod(ellps=ellps)

    for start_idx in range(n_lons):
        end_idx = 0 if (start_idx + 1) == n_lons else start_idx + 1
        glons, glats = geodesic_by_idx(
            lons, lats, start_idx, end_idx, npts=npts, include_end=False, geod=geod
        )
        geom_lons.extend(glons)
        geom_lats.extend(glats)

    # corner indices
    c1, c2, c3, c4 = corner_idxs = np.arange(4) * npts
    # mid-point indices
    m12, m23, m34, m41 = corner_idxs + (npts // 2)

    # determine the bbox center
    center = len(geom_lons)
    geom_lons.append(geom_lons[m12])
    geom_lats.append(geom_lats[m23])

    logger.debug(f"corner idxs: {c1, c2, c3, c4}")
    logger.debug(f"midpoints idxs: {m12, m23, m34, m41}")
    logger.debug(f"geom outer pts: {len(geom_lons)}")
    logger.debug(f"center idx: {center}")

    idx_ranges_by_segment = {}
    outer_idxs = [c1, m12, c2, m23, c3, m34, c4, m41]

    for i in range(len(outer_idxs) - 1):
        start_idx, end_idx = outer_idxs[i], outer_idxs[i + 1]
        idx_ranges_by_segment[(start_idx, end_idx)] = list(range(start_idx, end_idx))

    idx_ranges_by_segment[(m41, c1)] = list(range(m41, m41 + (npts // 2)))
    quad_idxs = [(m12, center), (center, m34), (m23, center), (center, m41)]

    for start_idx, end_idx in quad_idxs:
        idx1 = len(geom_lons)
        idx2 = idx1 + npts - 1
        idx_middle = list(range(idx1, idx2 + 1))
        idx_ranges_by_segment[(start_idx, end_idx)] = [start_idx] + idx_middle
        idx_ranges_by_segment[(end_idx, start_idx)] = [end_idx] + idx_middle[::-1]

        glons, glats = geodesic_by_idx(
            geom_lons,
            geom_lats,
            start_idx,
            end_idx,
            npts=npts,
            include_start=False,
            include_end=False,
            geod=geod,
        )
        geom_lons.extend(glons)
        geom_lats.extend(glats)

    def build_quad(segments):
        quad = []
        for segment in segments:
            quad.extend(idx_ranges_by_segment[segment])
        return quad

    quad_faces = []
    quads = [
        [(c1, m12), (m12, center), (center, m41), (m41, c1)],
        [(m12, c2), (c2, m23), (m23, center), (center, m12)],
        [(center, m23), (m23, c3), (c3, m34), (m34, center)],
        [(m41, center), (center, m34), (m34, c4), (c4, m41)],
    ]
    for segments in quads:
        idxs = build_quad(segments)
        quad_face = [len(idxs)] + idxs
        quad_faces.append(quad_face)

    xyz = to_xyz(geom_lons, geom_lats, radius=radius)
    pdata = pv.PolyData(xyz, faces=quad_faces, n_faces=len(quad_faces))
    logger.debug(f"bbox: faces {pdata.n_faces}, points {pdata.n_points}")
    pdata = pdata.clean().triangulate()
    logger.debug(f"bbox: faces {pdata.n_faces}, points {pdata.n_points} (triangulated)")

    return pdata
