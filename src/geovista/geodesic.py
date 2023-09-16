"""Provide geodesic operators for geolocated meshes.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

from collections.abc import Iterable
from enum import Enum
import warnings

import numpy as np
from numpy.typing import ArrayLike
import pyproj
import pyvista as pv

from .common import (
    GV_FIELD_RADIUS,
    RADIUS,
    ZLEVEL_SCALE,
    _MixinStrEnum,
    distance,
    to_cartesian,
    wrap,
)
from .common import cast_UnstructuredGrid_to_PolyData as cast
from .crs import WGS84, to_wkt

__all__ = [
    "BBox",
    "GEODESIC_NPTS",
    "Preference",
    "line",
    "npoints",
    "npoints_by_idx",
    "panel",
    "wedge",
]

# Type aliases
Corners = tuple[float, float, float, float]

#: Default geodesic ellipse. See :func:`pyproj.get_ellps_map`.
ELLIPSE: str = "WGS84"

#: Number of equally spaced geodesic points between/including end-point/s.
GEODESIC_NPTS: int = 64

#: The bounding-box face geometry will contain ``BBOX_C**2`` cells.
BBOX_C: int = 256

#: The bounding-box tolerance on intersection.
BBOX_TOLERANCE: int = 0

#: Ratio that the bounding-box inner and outer faces are offset from the surface mesh.
BBOX_RADIUS_RATIO = 1e-1

#: Lookup table for cubed-sphere panel index by panel name.
PANEL_IDX_BY_NAME: dict[str, int] = {
    "africa": 0,
    "asia": 1,
    "pacific": 2,
    "americas": 3,
    "arctic": 4,
    "antarctic": 5,
}

#: Lookup table for cubed-sphere panel name by panel index.
PANEL_NAME_BY_IDX: dict[int, str] = {
    0: "africa",
    1: "asia",
    2: "pacific",
    3: "americas",
    4: "arctic",
    5: "antarctic",
}

#: Latitude (degrees) of a cubed-sphere panel corner.
CSC: float = np.rad2deg(np.arcsin(1 / np.sqrt(3)))

#: Cubed-sphere panel bounding-box longitudes and latitudes.
PANEL_BBOX_BY_IDX: dict[int, tuple[Corners, Corners]] = {
    0: ((-45, 45, 45, -45), (CSC, CSC, -CSC, -CSC)),
    1: ((45, 135, 135, 45), (CSC, CSC, -CSC, -CSC)),
    2: ((135, -135, -135, 135), (CSC, CSC, -CSC, -CSC)),
    3: ((-135, -45, -45, -135), (CSC, CSC, -CSC, -CSC)),
    4: ((-45, 45, 135, -135), (CSC, CSC, CSC, CSC)),
    5: ((-45, 45, 135, -135), (-CSC, -CSC, -CSC, -CSC)),
}

#: The number of cubed-sphere panels.
N_PANELS: int = len(PANEL_IDX_BY_NAME)

#: The default bounding-box preference.
PREFERENCE: str = "center"


# TODO: use StrEnum and auto when minimum supported python version is 3.11
class Preference(_MixinStrEnum, Enum):
    """Enumeration of geodesic mesh geometry preferences.

    Notes
    -----
    .. versionadded:: 0.3.0

    """

    CELL = "cell"
    CENTER = "center"
    POINT = "point"


class BBox:
    """A 3-D bounding-box constructed from geodesic lines or great circles."""

    def __init__(
        self,
        lons: ArrayLike,
        lats: ArrayLike,
        ellps: str | None = ELLIPSE,
        c: int | None = BBOX_C,
        triangulate: bool | None = False,
    ) -> None:
        """Create 3-D geodesic bounding-box to extract enclosed mesh, lines or point.

        The bounding-box region is specified in terms of its four corners, in
        degrees of longitude and latitude. As the bounding-box is a geodesic, it
        can only ever at most enclose half of an ellipsoid.

        The geometry of the bounding-box may be specified as either an open or
        closed longitude/latitude geometry i.e., 4 or 5 longitude/latitude values.

        Parameters
        ----------
        lons : ArrayLike
            The longitudes (degrees) of the bounding-box, in the half-closed interval
            [-180, 180). Note that, longitudes will be wrapped to this interval.
        lats : ArrayLike
            The latitudes (degrees) of the bounding-box, in the closed interval
            [-90, 90].
        ellps : str, default=ELLIPSE
            The ellipsoid for geodesic calculations. See :func:`pyproj.get_ellps_map`.
        c : float, default=BBOX_C
            The bounding-box face geometry will contain ``c**2`` cells.
        triangulate : bool, default=False
            Specify whether the bounding-box faces are triangulated.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if not isinstance(lons, Iterable):
            lons = [lons]
        if not isinstance(lats, Iterable):
            lats = [lats]

        lons = np.asanyarray(lons)
        lats = np.asanyarray(lats)
        n_lons, n_lats = lons.size, lats.size

        if n_lons != n_lats:
            emsg = (
                f"Require the same number of longitudes ({n_lons}) and "
                f"latitudes ({n_lats})."
            )
            raise ValueError(emsg)

        if n_lons < 4:
            emsg = (
                "Require a bounding-box geometry containing at least 4 "
                "longitude/latitude values to create the bounding-box manifold, "
                f"got '{n_lons}'."
            )
            raise ValueError(emsg)

        if n_lons > 5:
            emsg = (
                "Require a bounding-box geometry containing 4 (open) or 5 (closed) "
                "longitude/latitude values to create the bounding-box manifold, "
                f"got {n_lons}."
            )
            raise ValueError(emsg)

        # ensure the specified bbox geometry is open
        if n_lons == 5:
            if np.isclose(lons[0], lons[-1]) and np.isclose(lats[0], lats[-1]):
                lons, lats = lons[-1], lats[-1]
            else:
                wmsg = (
                    "The bounding-box was specified with 5 longitude/latitude values, "
                    "however the first and last values are not close enough to specify "
                    "a closed geometry - ignoring last value."
                )
                warnings.warn(wmsg, stacklevel=2)
                lons, lats = lons[:-1], lats[:-1]

        self.lons = lons
        self.lats = lats
        self.ellps = ellps
        self.c = c
        self.triangulate = triangulate
        # the resultant bounding-box mesh
        self._mesh = None
        # cache prior surface radius, as an optimisation
        self._surface_radius = None

    def __eq__(self, other) -> bool:
        result = NotImplemented
        if isinstance(other, BBox):
            result = False
            lhs = (self.ellps, self.c, self.triangulate)
            rhs = (other.ellps, other.c, other.triangulate)
            if all(x[0] == x[1] for x in zip(lhs, rhs)):
                if np.allclose(self.lons, other.lons):
                    result = np.allclose(self.lats, other.lats)
        return result

    def __ne__(self, other) -> bool:
        result = self == other
        if result is not NotImplemented:
            result = not result
        return result

    def __repr__(self) -> str:
        params = (
            f"ellps={self.ellps}, c={self.c}, n_points={self.mesh.n_points}, "
            f"n_cells={self.mesh.n_cells}"
        )
        result = f"{__package__}.{self.__class__.__name__}<{params}>"
        return result

    @property
    def mesh(self):
        """The bounding-box :class:`pyvista.PolyData` mesh."""
        if self._mesh is None:
            self._generate_bbox_mesh()
        return self._mesh

    def _init(self) -> None:
        """Bootstrap the bounding-box state.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        self._idx_map = np.empty((self.c + 1, self.c + 1), dtype=int)
        self._bbox_lons, self._bbox_lats = [], []
        self._bbox_count = 0
        self._geod = pyproj.Geod(ellps=self.ellps)
        self._npts = self.c - 1
        self._n_faces = self.c * self.c
        self._n_points = (self.c + 1) * (self.c + 1)

    def _bbox_face_edge_idxs(self) -> np.ndarray:
        """Get the bounding-box outer edge indices.

        Inspects the index map (_idx_map) topology to determine the sequence
        of indices that define the bounding-box edge/boundary. This sequence of
        indices is open i.e., it's implied that the last index is connected
        to the first in the sequence.

        The indices (_idx_map) reference the actual longitude/latitude
        values (_bbox_lons/_bbox_lats). This state is configured when
        generating the bounding-box face (_generate_bbox_face).

        Returns
        -------
        ndarray
            The indices of the bounding-box edge.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        edge = np.concatenate(
            [
                self._idx_map[0],
                self._idx_map[1:, -1],
                self._idx_map[-1, -2::-1],
                self._idx_map[-2:0:-1, 0],
            ]
        )
        return edge

    def _generate_bbox_face(self) -> None:
        """Construct 2-D geodetic bounding-box surface defined by corners.

        Given the longitude/latitude corners of the bounding-box and the number
        of faces that define the bounding-box mesh i.e., c**2, determine all
        the associated geodesic points (geometry) and indices (topology) of the
        bounding-box mesh.

        The indices (_idx_map) reference the longitude/latitude points
        (_bbox_lon/_bbox_lat), and together are required to create the
        resultant bounding-box :class:`pyvista.PolyData` mesh.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        # corner indices
        c1_idx, c2_idx, c3_idx, c4_idx = range(4)

        def bbox_extend(lons: tuple[float], lats: tuple[float]) -> None:
            assert len(lons) == len(lats)
            self._bbox_lons.extend(lons)
            self._bbox_lats.extend(lats)
            self._bbox_count += len(lons)

        def bbox_update(idx1, idx2, row=None, column=None) -> None:
            assert row is not None or column is not None
            if row is None:
                row = slice(None)
            if column is None:
                column = slice(None)
            glons, glats = npoints_by_idx(
                self._bbox_lons,
                self._bbox_lats,
                idx1,
                idx2,
                npts=self._npts,
                geod=self._geod,
            )
            self._idx_map[row, column] = (
                [idx1] + list(np.arange(self._npts) + self._bbox_count) + [idx2]
            )
            bbox_extend(glons, glats)

        # register bbox edge indices, and points
        bbox_extend(self.lons, self.lats)
        bbox_update(c1_idx, c2_idx, row=0)
        bbox_update(c4_idx, c3_idx, row=-1)
        bbox_update(c1_idx, c4_idx, column=0)
        bbox_update(c2_idx, c3_idx, column=-1)

        # register bbox inner indices and points
        for row_idx in range(1, self.c):
            row = self._idx_map[row_idx]
            bbox_update(row[0], row[-1], row=row_idx)

    def _generate_bbox_mesh(
        self, surface: pv.PolyData | None = None, radius: float | None = None
    ) -> None:
        """Construct 3-D geodetic bounding-box extruded surface defined by corners.

        The bounding-box mesh consists of an inner surface, an outer surface,
        and a skirt that joins these two surfaces together to create a mesh
        that is a manifold.

        The purpose of the bounding-box is to determine which faces/points of
        a third-party mesh are contained/enclosed within the bounding-box
        manifold.

        Note that, the bounding-box inner surface and outer surface are
        congruent.

        Parameters
        ----------
        surface : PolyData, optional
            The surface that the bounding-box will be enclosing.
        radius : float, optional
            The radius of the surface that the bounding-box will be enclosing.
            Note that, the `radius` is only used when the `surface` is not
            provided. Defaults to :data:`geovista.common.RADIUS`.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if surface is not None:
            radius = distance(surface)

        radius = RADIUS if radius is None else abs(float(radius))

        if radius != self._surface_radius:
            self._init()
            self._surface_radius = radius

            self._generate_bbox_face()
            skirt_faces = self._generate_bbox_skirt()

            # generate the face indices
            bbox_n_faces = self._n_faces * 2
            faces_n = np.broadcast_to(np.array([4], dtype=np.int8), (bbox_n_faces, 1))
            faces_c1 = np.ravel(self._idx_map[: self.c, : self.c]).reshape(-1, 1)
            faces_c2 = np.ravel(self._idx_map[: self.c, 1:]).reshape(-1, 1)
            faces_c3 = np.ravel(self._idx_map[1:, 1:]).reshape(-1, 1)
            faces_c4 = np.ravel(self._idx_map[1:, : self.c]).reshape(-1, 1)
            inner_faces = np.hstack([faces_c1, faces_c2, faces_c3, faces_c4])
            outer_faces = inner_faces + self._n_points
            faces = np.vstack([inner_faces, outer_faces])
            bbox_faces = np.hstack([faces_n, faces])

            # convert bbox lons/lats to ndarray (internal convenience i.e., boundary)
            self._bbox_lons = np.asanyarray(self._bbox_lons)
            self._bbox_lats = np.asanyarray(self._bbox_lats)

            # calculate the radii of the inner and outer bbox faces
            offset = self._surface_radius * BBOX_RADIUS_RATIO
            inner_radius = self._surface_radius - offset
            outer_radius = self._surface_radius + offset

            # generate the face points
            inner_xyz = to_cartesian(
                self._bbox_lons, self._bbox_lats, radius=inner_radius
            )
            outer_xyz = to_cartesian(
                self._bbox_lons, self._bbox_lats, radius=outer_radius
            )
            bbox_xyz = np.vstack([inner_xyz, outer_xyz])

            # include the bbox skirt
            bbox_faces = np.vstack([bbox_faces, skirt_faces])
            bbox_n_faces += skirt_faces.shape[0]

            # create the bbox mesh
            self._mesh = pv.PolyData(bbox_xyz, faces=bbox_faces, n_faces=bbox_n_faces)

            self._mesh.field_data[GV_FIELD_RADIUS] = np.array([radius])
            to_wkt(self._mesh, WGS84)

            if self.triangulate:
                self._mesh = self._mesh.triangulate()

    def _generate_bbox_skirt(self) -> np.ndarray:
        """Calculate indices of faces for boundary-box skirt.

        Determine the indices of the skirt that will join the inner and outer
        bounding-box surfaces to create a "water-tight" manifold.

        Returns
        -------
        ndarray
            The indices of the bounding-box skirt.

        Notes
        -----
        .. verseionadded:: 0.1.0

        """
        skirt_n_faces = 4 * self.c

        faces_n = np.broadcast_to(np.array([4], dtype=np.int8), (skirt_n_faces, 1))
        faces_c1 = self._bbox_face_edge_idxs().reshape(-1, 1)
        faces_c2 = np.roll(faces_c1, -1)
        faces_c3 = faces_c2 + self._n_points
        faces_c4 = np.roll(faces_c3, 1)

        faces = np.hstack([faces_n, faces_c1, faces_c2, faces_c3, faces_c4])

        return faces

    def boundary(
        self, surface: pv.PolyData | None = None, radius: float | None = None
    ) -> pv.PolyData:
        """Footprint of bounding-box intersecting on the provided mesh surface.

        The region of the bounding-box that intersects on the surface of the mesh
        that will be enclosed.

        Parameters
        ----------
        surface : PolyData, optional
            The :class:`pyvista.PolyData` mesh that will be enclosed by the
            bounding-box boundary.
        radius : float, optional
            The radius of the mesh that will be enclosed by the bounding-box
            boundary. Note that, the `radius` is only used when the `surface`
            is not provided. Defaults to :data:`geovista.common.RADIUS`.

        Returns
        -------
        PolyData
            The boundary of the bounding-box.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        self._generate_bbox_mesh(surface=surface, radius=radius)

        radius = self._surface_radius + self._surface_radius * ZLEVEL_SCALE

        edge_idxs = self._bbox_face_edge_idxs()
        edge_lons = self._bbox_lons[edge_idxs]
        edge_lats = self._bbox_lats[edge_idxs]
        edge_xyz = to_cartesian(edge_lons, edge_lats, radius=radius)
        edge = pv.lines_from_points(edge_xyz, close=True)

        edge.field_data[GV_FIELD_RADIUS] = np.array([radius])
        to_wkt(edge, WGS84)

        return edge

    def enclosed(
        self,
        surface: pv.PolyData,
        tolerance: float | None = BBOX_TOLERANCE,
        outside: bool | None = False,
        preference: str | Preference | None = None,
    ) -> pv.PolyData:
        """Extract region of the `surface` contained within the bounding-box.

        Note that, points that are on the surface of the bounding-box manifold are not
        considered within the bounding-box. See the `preference` and `tolerance`
        options.

        Parameters
        ----------
        surface : PolyData
            The :class:`pyvista.PolyData` mesh to be checked for containment.
        tolerance : float, default=BBOX_TOLERANCE
            The tolerance on the intersection operation with the `surface`,
            expressed as a fraction of the diagonal of the bounding-box.
        outside : bool, default=False
            By default, select those points of the `surface` that are inside
            the bounding-box. Otherwise, select those points that are outside
            the bounding-box.
        preference : str or Preference, optional
            Criteria for defining whether a face of a `surface` mesh is
            deemed to be enclosed by the bounding-box. A `preference` of
            ``cell`` requires all points defining the face to be within the
            bounding-box. A `preference` of ``center`` requires that only the
            face cell center is within the bounding-box. A `preference` of
            ``point`` requires at least one point that defines the face to be
            within the bounding-box. Defaults to :data:`PREFERENCE`.

        Returns
        -------
        PolyData
            The :class:`pyvista.PolyData` representing those parts of
            the provided `surface` enclosed by the bounding-box. This behaviour
            may be inverted with the `outside` parameter.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if preference is None:
            preference = PREFERENCE

        if not Preference.valid(preference):
            options = " or ".join(f"{item!r}" for item in Preference.values())
            emsg = f"Expected a preference of {options}, got '{preference}'."
            raise ValueError(emsg)

        preference = Preference(preference)
        self._generate_bbox_mesh(surface=surface)

        if preference == Preference.CENTER:
            original = surface
            surface = surface.cell_centers()

        # filter the surface with the bbox manifold mesh
        selected = surface.select_enclosed_points(
            self.mesh, tolerance=tolerance, inside_out=outside, check_surface=False
        )
        # name of the point mask generated by select_enclosed_points
        scalars = "SelectedPoints"

        # sample the surface with the enclosed cells to extract the bbox region
        if preference == Preference.CENTER:
            region = original.extract_cells(selected[scalars].view(bool))
        elif preference == Preference.POINT:
            region = selected.threshold(0.5, scalars=scalars, preference="cell")
        else:
            region = surface.extract_points(
                selected[scalars].view(bool), adjacent_cells=False
            )

        region = cast(region)

        return region


def line(
    lons: ArrayLike,
    lats: ArrayLike,
    surface: pv.PolyData | None = None,
    radius: float | None = None,
    npts: int | None = None,
    ellps: str | None = None,
    close: bool | None = False,
    zlevel: int | None = None,
    zscale: float | None = None,
) -> pv.PolyData:
    """Geodesic line consisting of one or more connected geodesic line segments.

    Note that, as a convenience, if a single value is provided for `lons` and ``N``
    values are provided for `lats`, then the longitude value will be automatically
    repeated ``N`` times, and vice versa. Where ``N >= 2``.

    Parameters
    ----------
    lons : ArrayLike
        The longitudes (degrees) of the geodesic line segments, in the half-closed
        interval [-180, 180). Note that, longitudes will be wrapped to this
        interval.
    lats : ArrayLike
        The latitudes (degrees) of the geodesic line segments, in the closed
        interval [-90, 90].
    surface : PolyData, optional
        The surface that the geodesic line will be rendered over.
    radius : float, optional
        The radius of the surface that the geodesic line will be rendered over.
        Note that, the `radius` is only used when the `surface` is not
        provided. Defaults to :data:`geovista.common.RADIUS`.
    npts : float, default=GEODESIC_NPTS
        The number of equally spaced geodesic points in a line segment, excluding
        the segment end-point, but including the segment start-point i.e., `npts`
        must be at least 2.
    ellps : str, default=ELLIPSE
        The ellipsoid for geodesic calculations. See :func:`pyproj.get_ellps_map`.
    close : bool, default=False
        Whether to close the geodesic line segments into a loop i.e., the last
        point is connected to the first point.
    zlevel : int, default=1
        The z-axis level. Used in combination with the `zscale` to offset the
        `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
    zscale : float, optional
        The proportional multiplier for z-axis `zlevel`. Defaults to
        :data:`geovista.common.ZLEVEL_SCALE`.

    Returns
    -------
    PolyData
        The geodesic line.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if surface is not None:
        radius = distance(surface)
    else:
        radius = RADIUS if radius is None else abs(float(radius))

    zscale = ZLEVEL_SCALE if zscale is None else float(zscale)
    zlevel = 1 if zlevel is None else int(zlevel)
    radius += radius * zlevel * zscale

    if npts is None:
        npts = GEODESIC_NPTS

    if ellps is None:
        ellps = ELLIPSE

    if not isinstance(lons, Iterable):
        lons = [lons]

    if not isinstance(lats, Iterable):
        lats = [lats]

    lons, lats = np.asanyarray(lons), np.asanyarray(lats)

    # check whether to auto-repeat lons or lats
    if lons.size == 1 or lats.size == 1:
        if lons.size + lats.size > 2:
            if lons.size == 1:
                lons = np.repeat(lons[0], lats.size)
            else:
                lats = np.repeat(lats[0], lons.size)

    n_lons, n_lats = lons.size, lats.size

    if n_lons != n_lats:
        emsg = (
            f"Require the same number of longitudes ({n_lons}) and "
            f"latitudes ({n_lats})."
        )
        raise ValueError(emsg)

    if n_lons < 2:
        emsg = (
            "Require a line geometry containing at least 2 longitude/latitude "
            f"values, got '{n_lons}'."
        )
        raise ValueError(emsg)

    lons = wrap(lons)

    # check for minimal loop corner case
    if np.isclose(lons[0], lons[-1]) and np.isclose(lats[0], lats[-1]):
        if n_lons == 2:
            emsg = (
                "Require a closed line (loop) geometry containing at least 3 "
                f"longitude/latitude values, got '{n_lons}'."
            )
            raise ValueError(emsg)

    line_lons, line_lats = [], []
    geod = pyproj.Geod(ellps=ellps)

    for idx in range(n_lons - 1):
        glons, glats = npoints_by_idx(
            lons,
            lats,
            idx,
            idx + 1,
            npts=npts,
            include_start=True,
            include_end=False,
            geod=geod,
        )
        line_lons.extend(glons)
        line_lats.extend(glats)

    # finally, include the end-point
    line_lons.append(lons[-1])
    line_lats.append(lats[-1])

    xyz = to_cartesian(line_lons, line_lats, radius=radius)
    lines = pv.lines_from_points(xyz, close=close)

    lines.field_data[GV_FIELD_RADIUS] = np.array([radius])
    to_wkt(lines, WGS84)

    return lines


def npoints(
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
    npts: int | None = GEODESIC_NPTS,
    radians: bool | None = False,
    include_start: bool | None = False,
    include_end: bool | None = False,
    geod: pyproj.Geod | None = None,
) -> tuple[tuple[float], tuple[float]]:
    """Calculate geodesic mid-points between provided start and end points.

    Given a single start-point and end-point, calculate the equally spaced
    intermediate longitude and latitude `npts` points along the geodesic line
    that spans between the start and end points.

    Note that, longitudes (degrees) will be wrapped to the half-closed interval
    [-180, 180).

    Parameters
    ----------
    start_lon : float
        The longitude of the start-point for the geodesic line.
    start_lat : float
        The latitude of the start-point for the geodesic line.
    end_lon : float
        The longitude of the end-point for the geodesic line.
    end_lat : float
        The latitude of the end-point for the geodesic line.
    npts : int, default=GEODESIC_NPTS
        The number of points to be returned, which may include the start-point
        and/or the end-point, if required.
    radians : bool, default=False
        If ``True``, the start and end points are assumed to be in radians,
        otherwise degrees.
    include_start : bool, default=False
        Whether to include the start-point in the geodesic points returned.
    include_end : bool, default=False
        Whether to include the end-point in the geodesic points returned.
    geod : Geod, optional
        Definition of the ellipsoid for geodesic calculations. Defaults to
        :data:`ELLIPSE`.

    Returns
    -------
    tuple of tuples
        Tuple of (longitude, latitude) points along the geodesic line
        between the start-point and the end-point.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if geod is None:
        geod = pyproj.Geod(ellps=ELLIPSE)

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
    glons = tuple(wrap(glons))

    return glons, glats


def npoints_by_idx(
    lons: ArrayLike,
    lats: ArrayLike,
    start_idx: int,
    end_idx: int,
    npts: int | None = GEODESIC_NPTS,
    radians: bool | None = False,
    include_start: bool | None = False,
    include_end: bool | None = False,
    geod: pyproj.Geod | None = None,
) -> tuple[tuple[float], tuple[float]]:
    """Calculate geodesic mid-points between provided start and end indices.

    Given a single start-point index and end-point index, calculate the equally
    spaced intermediate longitude and latitude `npts` points along the geodesic
    line that spans between the start and end points.

    Note that, longitudes (degrees) will be wrapped to the half-closed interval
    [-180, 180).

    Parameters
    ----------
    lons : ArrayLike
        The longitudes to be sampled by the provided indices.
    lats : ArrayLike
        The latitudes to be sampled by the provided indices.
    start_idx : int
        The index of the start-point.
    end_idx : int
        The index of the end-point.
    npts : int, default=GEODESIC_NPTS
        The number of points to be returned, which may include the start-point
        and/or the end-point, if required
    radians : bool, default=False
        If ``True``, the `lons` and `lats` are assumed to be in radians,
        otherwise degrees.
    include_start : bool, default=False
        Whether to include the start-point in the geodesic points returned.
    include_end : bool, default=False
        Whether to include the end-point in the geodesic points returned.
    geod : Geod, optional
        Definition of the ellipsoid for geodesic calculations. Defaults to
        :data:`ELLIPSE`.

    Returns
    -------
    tuple of tuples
        Tuple of (longitude, latitude) points along the geodesic line
        between the start-point and the end-point.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if geod is None:
        geod = pyproj.Geod(ellps=ELLIPSE)

    start_lonlat = lons[start_idx], lats[start_idx]
    end_lonlat = lons[end_idx], lats[end_idx]

    result = npoints(
        *start_lonlat,
        *end_lonlat,
        npts=npts,
        radians=radians,
        include_start=include_start,
        include_end=include_end,
        geod=geod,
    )

    return result


def panel(
    name: int | str,
    ellps: str | None = ELLIPSE,
    c: int | None = BBOX_C,
    triangulate: bool | None = False,
) -> BBox:
    """Create boundary-box for specific cubed-sphere panel.

    Parameters
    ----------
    name : int or str
        The cubed-sphere index, see :data:`PANEL_NAME_BY_IDX`, or name, see
        :data:`PANEL_IDX_BY_NAME`, which specifies the panel bounding-box,
        see :data:`PANEL_BBOX_BY_IDX`.
    ellps : str, default=ELLIPSE
        The ellipsoid for geodesic calculations. See :func:`pyproj.get_ellps_map`.
    c : float, default=BBOX_C
        The bounding-box face geometry will contain ``c**2`` cells.
    triangulate : bool, default=False
        Specify whether the panel bounding-box faces are triangulated.

    Returns
    -------
    BBox
        The bounding-box that encloses the required cubed-sphere panel.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if isinstance(name, str):
        if name.lower() not in PANEL_IDX_BY_NAME:
            ordered = sorted(PANEL_IDX_BY_NAME)
            valid = ", ".join(f"'{kind}'" for kind in ordered[:-1])
            valid = f"{valid} or '{ordered[-1]}'"
            emsg = f"Panel name must be either {valid}, got '{name}'."
            raise ValueError(emsg)
        idx = PANEL_IDX_BY_NAME[name.lower()]
    else:
        idx = name
        if idx not in range(N_PANELS):
            emsg = (
                f"Panel index must be in the closed interval "
                f"[0, {N_PANELS-1}], got '{idx}'."
            )
            raise ValueError(emsg)

    lons, lats = PANEL_BBOX_BY_IDX[idx]

    return BBox(lons, lats, ellps=ellps, c=c, triangulate=triangulate)


def wedge(
    lon1: float,
    lon2: float,
    ellps: str | None = ELLIPSE,
    c: int | None = BBOX_C,
    triangulate: bool | None = False,
) -> BBox:
    """Create geodesic bounding-box wedge from the north-pole to the south-pole.

    Parameters
    ----------
    lon1 : float
        The first longitude (degrees) defining the geodesic wedge region.
    lon2 : float
        The second longitude (degrees) defining the geodesic wedge region.
    ellps : str, default=ELLIPSE
        The ellipsoid for geodesic calculations. See :func:`pyproj.get_ellps_map`.
    c : float, default=BBOX_C
        The bounding-box face geometry will contain ``c**2`` cells.
    triangulate : bool, default=False
        Specify whether the wedge bounding-box faces are triangulated.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    delta = abs(lon1 - lon2)

    if 0 < delta >= 180:
        emsg = (
            "A geodesic wedge must have an absolute longitudinal difference "
            f"(degrees) in the open interval (0, 180), got '{delta}'."
        )
        raise ValueError(emsg)

    lons = (lon1, lon2, lon2, lon1)
    lats = (90, 90, -90, -90)

    return BBox(lons, lats, ellps=ellps, c=c, triangulate=triangulate)
