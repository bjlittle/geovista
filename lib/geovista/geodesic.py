from collections.abc import Iterable
from typing import Dict, Optional, Tuple, Union

import numpy as np
from numpy.typing import ArrayLike
import pyproj
import pyvista as pv

from .common import to_xyz, wrap
from .log import get_logger

__all__ = ["BBox", "npoints", "npoints_by_idx", "panel", "wedge"]

# Configure the logger.
logger = get_logger(__name__)

# type aliases
Corners = Tuple[float, float, float, float]

#: Default geodesic ellipse. See :func:`pyproj.get_ellps_map`.
ELLIPSE: str = "WGS84"

#: Number of equally spaced geodesic points between/including endpoint/s.
GEODESIC_NPTS: int = 64

#: The bounding-box face geometry will contain ``BBOX_C**2`` cells.
BBOX_C: int = 512

#: The bounding-box tolerance on intersection.
BBOX_TOLERANCE: int = 0

#: Lookup table for cubed sphere panel index by panel name.
PANEL_IDX_BY_NAME: Dict[str, int] = dict(
    africa=0,
    asia=1,
    pacific=2,
    americas=3,
    polar=4,
    antarctic=5,
)

#: Lookup table for cubed sphere panel name by panel index.
PANEL_NAME_BY_IDX: Dict[int, str] = {
    0: "africa",
    1: "asia",
    2: "pacific",
    3: "americas",
    4: "polar",
    5: "antarctic",
}

#: Latitude (degrees) of a cubed sphere panel corner.
CORNER: float = np.rad2deg(np.arcsin(1 / np.sqrt(3)))

#: Cubed sphere panel bounded-box longitudes and latitudes.
PANEL_BBOX_BY_IDX: Dict[int, Tuple[Corners, Corners]] = {
    0: ((-45, 45, 45, -45), (CORNER, CORNER, -CORNER, -CORNER)),
    1: ((45, 135, 135, 45), (CORNER, CORNER, -CORNER, -CORNER)),
    2: ((135, -135, -135, 135), (CORNER, CORNER, -CORNER, -CORNER)),
    3: ((-135, -45, -45, -135), (CORNER, CORNER, -CORNER, -CORNER)),
    4: ((-45, 45, 135, -135), (CORNER, CORNER, CORNER, CORNER)),
    5: ((-45, 45, 135, -135), (-CORNER, -CORNER, -CORNER, -CORNER)),
}

#: The number of cubed sphere panels.
N_PANELS: int = len(PANEL_IDX_BY_NAME)

#: Preference for an operation to be cell/face focused.
PREFERENCE_CELL: str = "cell"

#: Preference for an operation to be point/node focused.
PREFERENCE_POINT: str = "point"


def npoints(
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
    npts: Optional[int] = GEODESIC_NPTS,
    radians: Optional[bool] = False,
    include_start: Optional[bool] = False,
    include_end: Optional[bool] = False,
    geod: Optional[pyproj.Geod] = None,
) -> Tuple[Tuple[float], Tuple[float]]:
    """
    TBD

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
    npts: Optional[int] = GEODESIC_NPTS,
    radians: Optional[bool] = False,
    include_start: Optional[bool] = False,
    include_end: Optional[bool] = False,
    geod: Optional[pyproj.Geod] = None,
) -> Tuple[Tuple[float], Tuple[float]]:
    """
    TBD

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


class BBox:
    """
    TBD

    Notes
    -----
    .. versionadded:: 0.1.0

    """

    RADIUS_RATIO = 3e-2

    def __init__(
        self,
        lons: ArrayLike,
        lats: ArrayLike,
        ellps: Optional[str] = ELLIPSE,
        radius: Optional[float] = 1.0,
        c: Optional[int] = BBOX_C,
        triangulate: Optional[bool] = False,
    ):
        """
        TBD

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
                "Require a bounded-box geometry containing at least 4 longitude/latitude "
                f"values to create the bounded-box manifold, only got {n_lons}."
            )
            raise ValueError(emsg)

        if n_lons > 5:
            emsg = (
                "Require a bounded-box geometry containing 4 (open) or 5 (closed) "
                "longitude/latitude values to create the bounded-box manifold, "
                f"got {n_lons}."
            )
            raise ValueError(emsg)

        # ensure the specified bbox geometry is open
        if np.isclose(lons[0], lons[-1]) and np.isclose(lats[0], lats[-1]):
            lons, lats = lons[-1], lats[-1]

        self.lons = lons
        self.lats = lats
        self.ellps = ellps
        self.radius = radius
        self.c = c
        self.triangulate = triangulate

        # initialise
        self._idx_map = np.empty((self.c + 1, self.c + 1), dtype=int)
        self._bbox_lons, self._bbox_lats = [], []
        self._bbox_count = 0
        self._geod = pyproj.Geod(ellps=ellps)
        self._npts = self.c - 1
        self._n_faces = self.c * self.c
        self._n_points = (self.c + 1) * (self.c + 1)

        offset = self.radius * self.RADIUS_RATIO
        self._inner_radius = self.radius - offset
        self._outer_radius = self.radius + offset

        logger.debug(f"c: {self.c}")
        logger.debug(f"n_faces: {self._n_faces}")
        logger.debug(f"idx_map: {self._idx_map.shape}")
        logger.debug(
            f"radii: {self.radius}, {self._inner_radius}, {self._outer_radius}"
        )

        self._generate_mesh()

    def __eq__(self, other) -> bool:
        result = NotImplemented
        if isinstance(other, BBox):
            result = False
            lhs = (self.ellps, self.c, self.triangulate)
            rhs = (other.ellps, other.c, other.triangulate)
            if all(map(lambda x: x[0] == x[1], zip(lhs, rhs))) and np.isclose(
                self.radius, other.radius
            ):
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

    def _face_edge_idxs(self) -> ArrayLike:
        """
        TBD

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

    def _generate_face(self) -> None:
        """
        TBD

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        # corner indices
        c1_idx, c2_idx, c3_idx, c4_idx = range(4)

        def bbox_extend(lons: Tuple[float], lats: Tuple[float]) -> None:
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

    def _generate_mesh(self) -> None:
        """
        TBD

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        self._generate_face()
        skirt_faces = self._generate_skirt()

        # generate the face indices
        bbox_n_faces = self._n_faces * 2
        faces_N = np.broadcast_to(np.array([4], dtype=np.int8), (bbox_n_faces, 1))
        faces_c1 = np.ravel(self._idx_map[: self.c, : self.c]).reshape(-1, 1)
        faces_c2 = np.ravel(self._idx_map[: self.c, 1:]).reshape(-1, 1)
        faces_c3 = np.ravel(self._idx_map[1:, 1:]).reshape(-1, 1)
        faces_c4 = np.ravel(self._idx_map[1:, : self.c]).reshape(-1, 1)
        inner_faces = np.hstack([faces_c1, faces_c2, faces_c3, faces_c4])
        outer_faces = inner_faces + self._n_points
        faces = np.vstack([inner_faces, outer_faces])
        bbox_faces = np.hstack([faces_N, faces])

        # convert bbox lons/lats to ndarray (internal convenience i.e., boundary)
        self._bbox_lons = np.asanyarray(self._bbox_lons)
        self._bbox_lats = np.asanyarray(self._bbox_lats)

        # generate the face points
        inner_xyz = to_xyz(self._bbox_lons, self._bbox_lats, radius=self._inner_radius)
        outer_xyz = to_xyz(self._bbox_lons, self._bbox_lats, radius=self._outer_radius)
        bbox_xyz = np.vstack([inner_xyz, outer_xyz])

        # include the bbox skirt
        bbox_faces = np.vstack([bbox_faces, skirt_faces])
        bbox_n_faces += skirt_faces.shape[0]

        # create the mesh
        self.mesh = pv.PolyData(bbox_xyz, faces=bbox_faces, n_faces=bbox_n_faces)
        logger.debug(
            f"bbox: n_faces={self.mesh.n_faces}, n_points={self.mesh.n_points}"
        )

        if self.triangulate:
            self.mesh = self.mesh.triangulate()
            logger.debug(
                f"bbox: n_faces={self.mesh.n_faces}, n_points={self.mesh.n_points} (tri)"
            )

    def _generate_skirt(self) -> ArrayLike:
        """
        TBD

        Notes
        -----
        .. verseionadded:: 0.1.0

        """
        skirt_n_faces = 4 * self.c
        faces_N = np.broadcast_to(np.array([4], dtype=np.int8), (skirt_n_faces, 1))
        faces_c1 = self._face_edge_idxs().reshape(-1, 1)
        faces_c2 = np.roll(faces_c1, -1)
        faces_c3 = faces_c2 + self._n_points
        faces_c4 = np.roll(faces_c3, 1)
        faces = np.hstack([faces_N, faces_c1, faces_c2, faces_c3, faces_c4])
        logger.debug(f"skirt_n_faces: {skirt_n_faces}")
        return faces

    def boundary(self, radius: Optional[float] = None):
        """
        TBD

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        # TODO: address "fudge-factor" zlevel
        if radius is None:
            radius = 1.0 + 1.0 / 1e4

        edge_idxs = self._face_edge_idxs()
        edge_lons = self._bbox_lons[edge_idxs]
        edge_lats = self._bbox_lats[edge_idxs]
        edge_xyz = to_xyz(edge_lons, edge_lats, radius=radius)
        edge = pv.lines_from_points(edge_xyz, close=True)
        return edge

    def enclosed(
        self,
        surface: pv.PolyData,
        tolerance: Optional[float] = BBOX_TOLERANCE,
        outside: Optional[bool] = False,
        preference: str = PREFERENCE_CELL,
    ) -> pv.UnstructuredGrid:
        """
        Extract the region of the ``surface`` contained within the
        bounded-box as a mesh.

        Note that, any ``surface`` points that are on the edge of the
        bounded-box will be deemed to be inside, and so will the cells
        associated with those ``surface`` points.

        Parameters
        ----------
        surface : PolyData
            The :class:`~pyvista.PolyData` mesh to be checked for containment.
        tolerance : float, default=0
            The tolerance on the intersection operation with the ``surface``,
            expressed as a fraction of the diagonal of the bounding box.
        outside : bool, default=False
            By default, select those points of the ``surface`` that are inside
            the bounded-box. Otherwise, select those points that are outside
            the bounded-box.
        preference : str, default="cell"
            Extract the bounded ``surface`` region based on ``cell`` centers.
            Otherwise, base the extraction on any ``point`` or node of a
            ``surface`` face being enclosed by the bounded-box.

        Returns
        -------
        UnstructuredGrid
            The :class:`~pyvista.UnstructuredGrid` representing those parts of
            the provided ``surface`` enclosed by the bounded-box. This behaviour
            may be inverted with the ``outside`` parameter.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if preference is None:
            preference = PREFERENCE_CELL

        if preference not in [PREFERENCE_POINT, PREFERENCE_CELL]:
            emsg = (
                f"Preference must be either '{PREFERENCE_POINT}' or "
                f"'{PREFERENCE_CELL}', got '{preference}'."
            )
            raise ValueError(emsg)

        if preference == PREFERENCE_CELL:
            original = surface
            surface = surface.cell_centers()

        selected = surface.select_enclosed_points(
            self.mesh, tolerance=tolerance, inside_out=outside
        )

        if preference == PREFERENCE_CELL:
            mesh = original.extract_cells(selected["SelectedPoints"].view(bool))
        else:
            mesh = selected.threshold(0.5, scalars="SelectedPoints", preference="cell")

        return mesh

    def enclosed_cells(
        self,
        surface: pv.PolyData,
        tolerance: Optional[float] = BBOX_TOLERANCE,
        outside: Optional[bool] = False,
        preference: str = PREFERENCE_CELL,
    ) -> ArrayLike:
        """
        Identify the cells of the ``surface`` contained within the
        bounded-box.

        Note that, any ``surface`` points that are on the edge of the
        bounded-box will be deemed to be inside, and so will the cells
        associated with those ``surface`` points.

        Parameters
        ----------
        surface : PolyData
            The :class:`~pyvista.PolyData` mesh to be checked for containment.
        tolerance : float, default=0
            The tolerance on the intersection operation with the ``surface``,
            expressed as a fraction of the diagonal of the bounding box.
        outside : bool, default=False
            By default, select those points of the ``surface`` that are inside
            the bounded-box. Otherwise, select those points that are outside
            the bounded-box.
        preference : str, default="cell"
            Extract the bounded ``surface`` region based on ``cell`` centers.
            Otherwise, base the extraction on any ``point`` or node of a
            ``surface`` face being enclosed by the bounded-box.

        Returns
        -------
        ArrayLike
            A boolean array, with the same shape as the ``surface.cell_data``,
            indicating those cells that are inside (``True``) and those that
            are outside (``False``). This behaviour may be inverted with the
            ``outside`` parameter.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        if preference is None:
            preference = PREFERENCE_CELL

        if preference not in [PREFERENCE_POINT, PREFERENCE_CELL]:
            emsg = (
                f"Preference must be either '{PREFERENCE_POINT}' or "
                f"'{PREFERENCE_CELL}', got '{preference}'."
            )
            raise ValueError(emsg)

        if preference == PREFERENCE_CELL:
            surface = surface.cell_centers()

        selected = surface.select_enclosed_points(
            self.mesh, tolerance=tolerance, inside_out=outside
        )
        cells = selected["SelectedPoints"].view(bool)
        return cells


def panel(
    name: Union[int, str],
    ellps: Optional[str] = ELLIPSE,
    radius: Optional[float] = 1.0,
    c: Optional[int] = BBOX_C,
    triangulate: Optional[bool] = False,
) -> BBox:
    """
    TBD

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if isinstance(name, str):
        if name.lower() not in PANEL_IDX_BY_NAME.keys():
            ordered = sorted(PANEL_IDX_BY_NAME.keys())
            names = ", ".join(f"'{key}'" for key in ordered[:-1])
            names = f"{names} or '{ordered[-1]}'"
            emsg = f"Panel name must be either {names}, got '{name}'."
            raise ValueError(emsg)
        idx = PANEL_IDX_BY_NAME[name]
    else:
        idx = name
        if idx not in range(N_PANELS):
            emsg = (
                f"Panel index must be in the closed interval "
                f"[0, {N_PANELS-1}], got '{idx}'."
            )
            raise ValueError(emsg)

    lons, lats = PANEL_BBOX_BY_IDX[idx]
    return BBox(lons, lats, ellps=ellps, radius=radius, c=c, triangulate=triangulate)


def wedge(
    lon1: float,
    lon2: float,
    ellps: Optional[str] = ELLIPSE,
    radius: Optional[float] = 1.0,
    c: Optional[int] = BBOX_C,
    triangulate: Optional[bool] = False,
) -> BBox:
    """
    TBD

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    delta = abs(lon1 - lon2)
    if 0 < delta >= 180:
        emsg = (
            "A geodesic wedge must have a longitude difference in the "
            f"open interval (0, 180), got '{delta}'."
        )
        raise ValueError(emsg)
    lons = (lon1, lon2, lon2, lon1)
    lats = (90, 90, -90, -90)
    return BBox(lons, lats, ellps=ellps, radius=radius, c=c, triangulate=triangulate)
