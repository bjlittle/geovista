from collections.abc import Iterable
from typing import Optional, Tuple

import numpy as np
from numpy.typing import ArrayLike
import pyproj
import pyvista as pv

from .common import to_xyz, wrap
from .log import get_logger

__all__ = ["BBox", "geodesic", "geodesic_by_idx"]

# Configure the logger.
logger = get_logger(__name__)

#: Default geodesic ellipse. See :func:`pyproj.get_ellps_map`.
ELLIPSE: str = "WGS84"

#: Number of equally spaced geodesic points between/including endpoint/s.
GEODESIC_NPTS: int = 64

#: The bounding-box face geometry will contain ``BBOX_C**2`` cells.
BBOX_C: int = 512

#: The bounding-box tolerance on intersection.
BBOX_TOLERANCE: int = 0


def geodesic(
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


def geodesic_by_idx(
    longitudes: ArrayLike,
    latitudes: ArrayLike,
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
        longitudes: ArrayLike,
        latitudes: ArrayLike,
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

        self.longitudes = lons
        self.latitudes = lats
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
            glons, glats = geodesic_by_idx(
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
        bbox_extend(self.longitudes, self.latitudes)
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
        selected = surface.select_enclosed_points(self.mesh, tolerance=tolerance, inside_out=outside)
        mesh = selected.threshold(0.5, scalars="SelectedPoints", preference="cell")
        return mesh

    def enclosed_cells(
        self,
        surface: pv.PolyData,
        tolerance: Optional[float] = BBOX_TOLERANCE,
        outside: Optional[bool] = False,
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
        selected = surface.select_enclosed_points(self.mesh, tolerance=tolerance, inside_out=outside)
        cells = selected["SelectedPoints"].view(bool)
        return cells
