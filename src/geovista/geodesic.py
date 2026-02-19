# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Provide geodesic operators for geolocated meshes.

Notes
-----
.. versionadded:: 0.1.0

"""

from __future__ import annotations

from typing import TYPE_CHECKING
import warnings

import lazy_loader as lazy

from .common import (
    GV_FIELD_RADIUS,
    GV_MANIFOLD_CELL_IDS,
    RADIUS,
    ZLEVEL_SCALE,
    StrEnumPlus,
    distance,
    to_cartesian,
    wrap,
)
from .common import cast_UnstructuredGrid_to_PolyData as cast
from .crs import WGS84, CRSLike, from_wkt, to_wkt
from .transform import transform_mesh, transform_points

if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy as np
    from numpy.typing import ArrayLike
    import pyproj
    import pyvista as pv

# lazy import third-party dependencies
np = lazy.load("numpy")
pyproj = lazy.load("pyproj")
pv = lazy.load("pyvista")

__all__ = [
    "BBOX_C",
    "BBOX_OUTSIDE",
    "BBOX_RADIUS_RATIO",
    "BBOX_TOLERANCE",
    "ELLIPSE",
    "GEODESIC_NPTS",
    "N_PANELS",
    "PANEL_BBOX_BY_IDX",
    "PANEL_IDX_BY_NAME",
    "PANEL_NAMES",
    "PANEL_NAME_BY_IDX",
    "PREFERENCE",
    "BBox",
    "Corners",
    "EnclosedPreference",
    "line",
    "npoints",
    "npoints_by_idx",
    "panel",
    "wedge",
]

# this is a type alias
type Corners = tuple[float, float, float, float]
"""Type alias for the corners of a bounding-box."""

# constants
ELLIPSE: str = "WGS84"
"""Default geodesic ellipse. See :func:`pyproj.list.get_ellps_map`."""

GEODESIC_NPTS: int = 64
"""Number of equally spaced geodesic points between/including end-point/s."""

BBOX_C: int = 256
"""The bounding-box face geometry will contain ``BBOX_C**2`` cells."""

BBOX_OUTSIDE: bool = False
"""Preference for selecting sample points outside/inside bounding-box."""

BBOX_RADIUS_RATIO: float = 1e-1
"""Ratio the bounding-box inner and outer faces are offset from the surface mesh."""

BBOX_TOLERANCE: float = 1e-6
"""The bounding-box tolerance on intersection."""

PANEL_IDX_BY_NAME: dict[str, int] = {
    "africa": 0,
    "asia": 1,
    "pacific": 2,
    "americas": 3,
    "arctic": 4,
    "antarctic": 5,
}
"""Lookup table for cubed-sphere panel index by panel name."""

PANEL_NAME_BY_IDX: dict[int, str] = {
    0: "africa",
    1: "asia",
    2: "pacific",
    3: "americas",
    4: "arctic",
    5: "antarctic",
}
"""Lookup table for cubed-sphere panel name by panel index."""

PANEL_NAMES: list[str] = list(PANEL_IDX_BY_NAME.keys())
"""Cubed-sphere panel names."""

CSC: float = np.rad2deg(np.arcsin(1 / np.sqrt(3)))
"""Latitude (degrees) of a cubed-sphere panel corner."""

PANEL_BBOX_BY_IDX: dict[int, tuple[Corners, Corners]] = {
    0: ((-45, 45, 45, -45), (CSC, CSC, -CSC, -CSC)),
    1: ((45, 135, 135, 45), (CSC, CSC, -CSC, -CSC)),
    2: ((135, -135, -135, 135), (CSC, CSC, -CSC, -CSC)),
    3: ((-135, -45, -45, -135), (CSC, CSC, -CSC, -CSC)),
    4: ((-45, 45, 135, -135), (CSC, CSC, CSC, CSC)),
    5: ((-45, 45, 135, -135), (-CSC, -CSC, -CSC, -CSC)),
}
"""Cubed-sphere panel bounding-box longitudes and latitudes."""

N_PANELS: int = len(PANEL_IDX_BY_NAME)
"""The number of cubed-sphere panels."""

PREFERENCE: str = "center"
"""The default bounding-box preference."""


class EnclosedPreference(StrEnumPlus):
    """Enumeration of mesh geometry enclosed preferences.

    Notes
    -----
    .. versionadded:: 0.3.0

    """

    CELL = "cell"
    """Enclosed if all cell vertices within bounding-box manifold."""
    CENTER = "center"
    """Enclosed if cell center within bounding-box manifold."""
    POINT = "point"
    """Enclosed if at least one cell vertex within bounding-box manifold."""


class BBox:  # numpydoc ignore=PR01
    """A 3D bounding-box constructed from geodesic lines or great circles."""

    def __init__(
        self,
        xs: ArrayLike,
        ys: ArrayLike,
        *,
        crs: CRSLike | None = WGS84,
        ellps: str | None = ELLIPSE,
        c: int = BBOX_C,
        triangulate: bool | None = False,
    ) -> None:
        """Create 3D geodesic bounding-box to extract enclosed mesh, lines or point.

        The bounding-box region is specified in terms of its four corners using
        coordinates defined by the projection `crs` (defaults to
        :data:`geovista.crs.WGS84`). As the bounding-box is a geodesic
        composed of great-circle lines, it can only ever at most enclose
        half of an ellipsoid.

        The geometry of the bounding-box may be specified as either an open or
        closed point geometry i.e., 4 or 5 corner values.

        Parameters
        ----------
        xs : ArrayLike
            The x-coordinates of the bounding-box in canonical `crs` units.
            Note that longitudes will be wrapped to the half-closed interval
            ``[-180, 180)``.
        ys : ArrayLike
            The y-coordinates of the bounding-box in canonical `crs` units.
            Note that latitudes are in the closed interval ``[-90, 90]``.
        crs : str, optional
            The Coordinate Reference System of the provided `xs` and `ys`.
            Defaults to :data:`geovista.crs.WGS84`.
        ellps : str, optional
            The ellipsoid for geodesic calculations. See
            :func:`pyproj.list.get_ellps_map`. Defaults to :data:`ELLIPSE`.
        c : float, optional
            The bounding-box face geometry will contain ``c**2`` cells.
            Defaults to :data:`BBOX_C`.
        triangulate : bool, optional
            Specify whether the bounding-box faces are triangulated. Defaults to
            ``False``.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        xs = np.atleast_1d(xs)
        ys = np.atleast_1d(ys)
        nx, ny = xs.size, ys.size

        if nx != ny:
            emsg = f"Require the same number of x points ({nx}) and y points ({ny})."
            raise ValueError(emsg)

        if nx < 4:
            emsg = (
                "Require a bounding-box geometry containing at least 4 "
                "x/y values to create the bounding-box manifold, "
                f"got '{nx}'."
            )
            raise ValueError(emsg)

        if nx > 5:
            emsg = (
                "Require a bounding-box geometry containing 4 (open) or 5 (closed) "
                "x/y values to create the bounding-box manifold, "
                f"got {nx}."
            )
            raise ValueError(emsg)

        # ensure the specified bbox geometry is open
        if nx == 5:
            if not (np.isclose(xs[0], xs[-1]) and np.isclose(ys[0], ys[-1])):
                wmsg = (
                    "geovista bounding-box was specified with 5 x/y "
                    "values, however the first and last values are not close enough to "
                    "specify a closed geometry - ignoring last value."
                )
                warnings.warn(wmsg, stacklevel=2)
            xs, ys = xs[:-1], ys[:-1]

        self.xs = xs
        """The x points of the bounding-box in canonical CRS units."""
        self.ys = ys
        """The y points of the bounding-box in canonical CRS units."""
        self.crs = crs
        """The coordinate reference system of the bounding-box points."""
        self.ellps = ellps
        """The ellipsoid defining the geodesic surface."""
        self.c = c
        """The number of cells that define the bounding-box face geometry i.e., c^2."""
        self.triangulate = triangulate
        """Whether the bounding-box faces are triangulated."""
        # the resultant bounding-box mesh
        self._mesh: pv.PolyData | None = None
        # the bounding-box mesh edges
        self._outline: pv.PolyData | None = None
        # enclosed preference for points outside/inside manifold
        self._outside = BBOX_OUTSIDE
        # enclosed cell preference
        self._preference = EnclosedPreference(PREFERENCE)
        # cache prior surface radius, as an optimisation
        self._surface_radius: float | None = None
        # enclosed tolerance of intersection operation
        self._tolerance = BBOX_TOLERANCE

        if self.crs != WGS84:
            latlon = transform_points(
                xs=self.xs, ys=self.ys, src_crs=self.crs, tgt_crs=WGS84
            )
            self.lons = latlon[:, 0]
            self.lats = latlon[:, 1]
        else:
            self.lons = xs
            self.lats = ys

    def __call__(self, surface: pv.PolyData) -> pv.PolyData:
        """Extract region of the `surface` contained within the bounding-box.

        Parameters
        ----------
        surface : PolyData
            The :class:`~pyvista.PolyData` mesh to be checked for containment.

        Returns
        -------
        PolyData
            The :class:`~pyvista.PolyData` representing those parts of the
            provided `surface` enclosed by the bounding-box.

        See Also
        --------
        enclosed : Equivalent method.
        outside : Property that selects points inside/outside manifold.
        preference : Property that specifies criterion for `surface` cell inclusion.
        tolerance : Property that controls manifold intersection tolerance.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        return self.enclosed(surface)

    def __eq__(self, other: object) -> bool:
        """Perform an equality comparison with the `other` operand.

        Parameters
        ----------
        other : object
            Equality comparison performed with this operand.

        Returns
        -------
        bool
            Equality comparison result.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        result: bool = NotImplemented
        if isinstance(other, BBox):
            result = False
            lhs = (self.ellps, self.c, self.triangulate)
            rhs = (other.ellps, other.c, other.triangulate)
            if all(x[0] == x[1] for x in zip(lhs, rhs, strict=True)) and np.allclose(
                self.lons, other.lons
            ):
                result = np.allclose(self.lats, other.lats)
        return result

    def __hash__(self) -> int:
        """Support hash-based collections.

        Returns
        -------
        int
            The computed :func:`hash` value of the instance.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        return hash(
            (
                self.crs,
                self.ellps,
                self.c,
                self.triangulate,
                self.xs.tobytes(),
                self.ys.tobytes(),
            )
        )

    def __ne__(self, other: object) -> bool:
        """Perform an inequality comparison with the `other` operand.

        Parameters
        ----------
        other : object
            Inequality comparison performed with this operand.

        Returns
        -------
        bool
            Inequality comparison result.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        result = self == other
        if result is not NotImplemented:
            result = not result
        return result

    def __repr__(self) -> str:
        """Serialize :class:`BBox` representation.

        Returns
        -------
        str
            String representation of the instance.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        params = (
            f"crs={self.crs}, ellps={self.ellps}, c={self.c}, "
            f"n_points={self.mesh.n_points}, n_cells={self.mesh.n_cells}"
        )

        return f"{__package__}.{self.__class__.__name__}<{params}>"

    @property
    def mesh(self) -> pv.PolyData:
        """The manifold bounding-box mesh.

        Returns
        -------
        PolyData
            The bounding-box mesh.

        Notes
        -----
        .. versionadded:: 0.1.0

        Examples
        --------
        Add a ``C32`` bounding-box around the Gulf of Guinea.
        The geodesic bounding-box is generated by defining 4 longitude-latitude
        corners. Natural Earth coastlines are also rendered along
        with a texture mapped Natural Earth base layer.

        >>> import geovista
        >>> from geovista.geodesic import BBox
        >>> p = geovista.GeoPlotter()
        >>> _ = p.add_base_layer(
        ...     texture=geovista.natural_earth_hypsometric(), opacity=0.5
        ... )
        >>> bbox = BBox(xs=[-15, 20, 25, -15], ys=[-25, -20, 15, 10], c=32)
        >>> _ = p.add_mesh(bbox.mesh, color="white")
        >>> p.camera.zoom(1.5)
        >>> p.show()

        """
        if self._mesh is None:
            self._generate_bbox_mesh()
        return self._mesh

    @property
    def outline(self) -> pv.PolyData:
        """The manifold bounding-box mesh edges.

        Returns
        -------
        PolyData
            The bounding-box mesh edges.

        Notes
        -----
        .. versionadded:: 0.6.0

        Examples
        --------
        Add the geodesic bounding-box manifold for the Arctic cubed-sphere
        panel along with its edges. A texture mapped Natural Earth base layer
        is also rendered.

        >>> import geovista
        >>> from geovista.geodesic import panel
        >>> p = geovista.GeoPlotter()
        >>> _ = p.add_base_layer(texture=geovista.natural_earth_1(), opacity=0.5)
        >>> bbox = panel("arctic")
        >>> _ = p.add_mesh(bbox.mesh, color="orange")
        >>> _ = p.add_mesh(bbox.outline, color="yellow", line_width=3)
        >>> p.view_vector(vector=(1, 1, 0))
        >>> p.camera.zoom(1.5)
        >>> p.show()

        """
        if self._mesh is None:
            self._generate_bbox_mesh()
        if self._outline is None:
            self._outline = self.mesh.extract_feature_edges()
        return self._outline

    @property
    def outside(self) -> bool:
        """The preference to select points outside/inside the bounding-box.

        Returns
        -------
        bool
            Manifold bounding-box selection preference.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        return self._outside

    @outside.setter
    def outside(self, value: bool | None) -> None:
        """Set preference to select points outside/inside the bounding-box.

        Parameters
        ----------
        value : bool
            Whether to select points outside/inside the bounding-box.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        if value is not None:
            self._outside = bool(value)

    @property
    def preference(self) -> EnclosedPreference:
        """The criterion for cell containment within the bounding-box.

        Returns
        -------
        EnclosedPreference
            The bounding-box enclosed preference.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        return self._preference

    @preference.setter
    def preference(self, value: str | EnclosedPreference | None) -> None:
        """Set the criterion for cell containment within the bounding-box.

        Parameters
        ----------
        value : str or EnclosedPreference
            The bounding-box enclosed preference for cell membership.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        if value is not None:
            if not EnclosedPreference.valid(value):
                options = " or ".join(
                    f"{item!r}" for item in EnclosedPreference.values()
                )
                emsg = f"Expected a preference of {options}, got '{value}'."
                raise ValueError(emsg)

            self._preference = EnclosedPreference(value)

    @property
    def tolerance(self) -> float:
        """The tolerance of the bounding-box manifold intersection.

        See :meth:`~pyvista.DataSetFilters.select_interior_points` for further
        details.

        Returns
        -------
        float
            The bounding-box manifold intersection tolerance.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value: float | None) -> None:
        """Set the tolerance of the bounding-box manifold intersection.

        Parameters
        ----------
        value : float
            The bounding-box manifold intersection tolerance.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        if value is not None:
            self._tolerance = float(value)

    def _init(self) -> None:
        """Bootstrap the bounding-box state.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        self._idx_map = np.empty((self.c + 1, self.c + 1), dtype=int)
        self._bbox_lons: list[float] = []
        self._bbox_lats: list[float] = []
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
        return np.concatenate(
            [
                self._idx_map[0],
                self._idx_map[1:, -1],
                self._idx_map[-1, -2::-1],
                self._idx_map[-2:0:-1, 0],
            ]
        )

    def _generate_bbox_face(self) -> None:
        """Construct 2D geodetic bounding-box surface defined by corners.

        Given the longitude/latitude corners of the bounding-box and the number
        of faces that define the bounding-box mesh i.e., c**2, determine all
        the associated geodesic points (geometry) and indices (topology) of the
        bounding-box mesh.

        The indices (_idx_map) reference the longitude/latitude points
        (_bbox_lon/_bbox_lat), and together are required to create the
        resultant bounding-box :class:`~pyvista.PolyData` mesh.

        Notes
        -----
        .. versionadded:: 0.1.0

        """
        # corner indices
        c1_idx, c2_idx, c3_idx, c4_idx = range(4)

        def bbox_extend(lons: Sequence[float], lats: Sequence[float]) -> None:
            """Register the bounding box longitudes and latitudes.

            Parameters
            ----------
            lons : iterable of float
                The bounding box longitudes.
            lats : iterable of float
                The bounding box latitudes.

            """
            assert len(lons) == len(lats)
            self._bbox_lons.extend(lons)
            self._bbox_lats.extend(lats)
            self._bbox_count += len(lons)

        def bbox_update(
            idx1: int, idx2: int, row: int | None = None, column: int | None = None
        ) -> None:
            """Generate and register a sampled geodesic bounding box line.

            The line is either a row or column that is a bounding box edge, or
            a row or column that traverses across the surface of the bounding box.

            Parameters
            ----------
            idx1 : int
                The start index of the bounding box, located on an edge.
            idx2 : int
                The end index of the bounding box, located on an edge.
            row : int, optional
                The index of the bounding box row. If not provided, the column spans
                all rows.
            column : int, optional
                The index of the bounding box column. If not provided, the row spans
                all columns.

            """
            assert row is not None or column is not None
            row_slice = np.s_[:] if row is None else np.s_[row]
            column_slice = np.s_[:] if column is None else np.s_[column]

            glons, glats = npoints_by_idx(
                self._bbox_lons,
                self._bbox_lats,
                start_idx=idx1,
                end_idx=idx2,
                npts=self._npts,
                geod=self._geod,
            )
            self._idx_map[row_slice, column_slice] = [
                idx1,
                *(np.arange(self._npts) + self._bbox_count),
                idx2,
            ]
            bbox_extend(glons, glats)

        # register bbox edge indices, and points
        bbox_extend(self.lons, self.lats)
        bbox_update(c1_idx, c2_idx, row=0)
        bbox_update(c4_idx, c3_idx, row=-1)
        bbox_update(c1_idx, c4_idx, column=0)
        bbox_update(c2_idx, c3_idx, column=-1)

        # register bbox inner indices and points
        for row_idx in range(1, self.c):
            row_idx_map = self._idx_map[row_idx]
            bbox_update(row_idx_map[0], row_idx_map[-1], row=row_idx)

    def _generate_bbox_mesh(
        self, surface: pv.PolyData | None = None, *, radius: float | None = None
    ) -> None:
        """Construct 3D geodetic bounding-box extruded surface defined by corners.

        The bounding-box mesh consists of an inner surface, an outer surface,
        and a skirt that joins these two surfaces together to create a mesh
        that is a manifold.

        The purpose of the bounding-box is to determine which faces/points of
        a third-party mesh are contained/enclosed within the bounding-box
        manifold.

        Note that the bounding-box inner surface and outer surface are
        congruent.

        Parameters
        ----------
        surface : PolyData, optional
            The surface that the bounding-box will be enclosing.
        radius : float, optional
            The radius of the surface that the bounding-box will be enclosing.
            Note that the `radius` is only used when the `surface` is not
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

            # create the bbox mesh
            self._mesh = pv.PolyData(bbox_xyz, faces=bbox_faces)

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

        return np.hstack([faces_n, faces_c1, faces_c2, faces_c3, faces_c4])

    def boundary(
        self, surface: pv.PolyData | None = None, *, radius: float | None = None
    ) -> pv.PolyData:
        """Footprint of bounding-box intersecting on the provided mesh surface.

        The region of the bounding-box that intersects on the surface of the mesh
        that will be enclosed.

        Parameters
        ----------
        surface : PolyData, optional
            The :class:`~pyvista.PolyData` mesh that will be enclosed by the
            bounding-box boundary.
        radius : float, optional
            The radius of the spherical mesh that will be enclosed by the
            bounding-box
            boundary. Note that the `radius` is only used when the `surface`
            is not provided. Defaults to :data:`geovista.common.RADIUS`.

        Returns
        -------
        PolyData
            The boundary of the bounding-box.

        Notes
        -----
        .. versionadded:: 0.1.0

        Examples
        --------
        Add the boundary of a ``C32`` bounding-box to the plotter for a region
        around the Gulf of Guinea. The geodesic bounding-box is generated by
        defining 4 longitude-latitude corners.

        The boundary is generated from where the bounding-box intersects with the
        surface of the C48 Sea Surface Temperature (SST) cubed-sphere mesh.

        >>> import geovista
        >>> from geovista.geodesic import BBox
        >>> from geovista.pantry.meshes import lfric_sst
        >>> p = geovista.GeoPlotter()
        >>> mesh = lfric_sst()
        >>> _ = p.add_mesh(mesh, cmap="balance")
        >>> bbox = BBox(xs=[-15, 20, 25, -15], ys=[-25, -20, 15, 10], c=32)
        >>> _ = p.add_mesh(bbox.boundary(mesh), color="orange", line_width=3)
        >>> p.view_yz()
        >>> p.show()

        """
        self._generate_bbox_mesh(surface=surface, radius=radius)

        assert isinstance(self._surface_radius, float)
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
        /,
        *,
        tolerance: float | None = None,
        outside: bool | None = None,
        preference: str | EnclosedPreference | None = None,
    ) -> pv.PolyData:
        """Extract region of the `surface` contained within the bounding-box.

        Note that points that are on the surface of the bounding-box manifold are not
        considered within the bounding-box. See the `preference` and `tolerance`
        options.

        Parameters
        ----------
        surface : PolyData
            The :class:`~pyvista.PolyData` mesh to be checked for containment.
        tolerance : float, optional
            The tolerance on the intersection operation with the `surface`,
            expressed as a fraction of the diagonal of the bounding-box.
            See :meth:`~pyvista.DataSetFilters.select_interior_points` for
            further details. Defaults to :data:`BBOX_TOLERANCE`.
        outside : bool, optional
            By default, select those points of the `surface` that are inside
            the bounding-box. Otherwise, select those points that are outside
            the bounding-box. Defaults to :data:`BBOX_OUTSIDE`.
        preference : str or EnclosedPreference, optional
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
            The :class:`~pyvista.PolyData` representing those parts of
            the provided `surface` enclosed by the bounding-box. This behaviour
            may be inverted with the `outside` parameter.

        Notes
        -----
        .. versionadded:: 0.1.0

        Examples
        --------
        Add the boundary of a ``C32`` bounding-box to the plotter for a region
        around the Gulf of Guinea. The geodesic bounding-box is generated by
        defining 4 longitude-latitude corners.

        Add the region enclosed by a ``C32`` bounding-box manifold to the
        plotter for a region around the ``0`` meridian. The geodesic
        bounding-box is generated by defining 4 longitude-latitude corners.

        The region is generated from all cells of the C48 Sea Surface Temperature
        (SST) cubed-sphere mesh that have their cell ``center`` enclosed by the
        bounding-box manifold.

        >>> import geovista
        >>> from geovista.geodesic import BBox
        >>> from geovista.pantry.meshes import lfric_sst
        >>> p = geovista.GeoPlotter()
        >>> _ = p.add_base_layer(texture=geovista.natural_earth_hypsometric())
        >>> mesh = lfric_sst()
        >>> bbox = BBox(xs=[-15, 20, 25, -15], ys=[-25, -20, 15, 10], c=32)
        >>> region = bbox.enclosed(mesh)
        >>> _ = p.add_mesh(region, cmap="balance")
        >>> p.view_yz()
        >>> p.show()

        The same ``region`` is rendered again, but with the land mask cells removed
        using the :meth:`pyvista.DataSetFilters.threshold` filter.

        >>> p = geovista.GeoPlotter()
        >>> _ = p.add_base_layer(texture=geovista.natural_earth_hypsometric())
        >>> _ = p.add_mesh(region.threshold(), cmap="balance")
        >>> p.view_yz()
        >>> p.show()

        """
        original = surface

        self.tolerance = tolerance
        self.outside = outside
        self.preference = preference

        # capture the current active scalars name
        active_scalars_name = surface.active_scalars_name

        crs = from_wkt(surface)

        if crs is not None:
            if transformed := crs != WGS84:
                if self.preference == EnclosedPreference.CENTER:
                    surface[GV_MANIFOLD_CELL_IDS] = np.arange(surface.n_cells)

                surface = transform_mesh(surface, tgt_crs=WGS84)
        else:
            # assume we have a raw mesh with cartesian points
            transformed = False

        # perform after transformation to avoid cloud specific transform behaviour
        if self.preference == EnclosedPreference.CENTER:
            surface = surface.cell_centers()

        self._generate_bbox_mesh(surface=surface)

        # filter the surface with the bbox manifold mesh
        selected = surface.select_interior_points(
            self.mesh,
            method="cell_locator",
            locator_tolerance=self.tolerance,
            inside_out=self.outside,
            check_surface=False,
        )
        # name of the point mask generated by select_interior_points
        scalars = "selected_points"

        # sample the surface with the enclosed cells to extract the bbox region
        if self.preference == EnclosedPreference.CENTER:
            mask = selected[scalars]
            idxs = surface[GV_MANIFOLD_CELL_IDS][mask] if transformed else mask
            region = original.extract_cells(idxs)
        elif self.preference == EnclosedPreference.POINT:
            original.point_data[scalars] = selected[scalars]
            region = original.threshold(0.5, scalars=scalars, preference="cell")
        else:
            region = original.extract_points(selected[scalars], adjacent_cells=False)

        # ensure to preserve active scalars name
        region.active_scalars_name = active_scalars_name

        return cast(region)


def line(
    lons: ArrayLike,
    lats: ArrayLike,
    *,
    surface: pv.PolyData | None = None,
    radius: float | None = None,
    npts: int | None = None,
    ellps: str | None = None,
    close: bool | None = False,
    zlevel: int | None = None,
    zscale: float | None = None,
) -> pv.PolyData:
    """Geodesic line consisting of one or more connected geodesic line segments.

    Note that as a convenience, if a single value is provided for `lons` and ``N``
    values are provided for `lats`, then the longitude value will be automatically
    repeated ``N`` times, and vice versa, providing ``N >= 2``.

    Parameters
    ----------
    lons : ArrayLike
        The longitudes (degrees) of the geodesic line segments, in the half-closed
        interval ``[-180, 180)``. Note that longitudes will be wrapped to this
        interval.
    lats : ArrayLike
        The latitudes (degrees) of the geodesic line segments, in the closed
        interval ``[-90, 90]``.
    surface : PolyData, optional
        The surface that the geodesic line will be rendered over.
    radius : float, optional
        The radius of the spherical surface that the geodesic line will be
        rendered over.
        Note that the `radius` is only used when the `surface` is not
        provided. Defaults to :data:`geovista.common.RADIUS`.
    npts : float, optional
        The number of equally spaced geodesic points in a line segment, excluding
        the segment end-point, but including the segment start-point i.e., `npts`
        must be at least 2. Defaults to :data:`GEODESIC_NPTS`.
    ellps : str, optional
        The ellipsoid for geodesic calculations. See :func:`pyproj.list.get_ellps_map`.
        Defaults to :data:`ELLIPSE`.
    close : bool, optional
        Whether to close the geodesic line segments into a loop i.e., the last
        point is connected to the first point. Defaults to ``False``.
    zlevel : int, optional
        The z-axis level. Used in combination with the `zscale` to offset the
        `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
        Defaults to ``1``.
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

    Examples
    --------
    Add the anti-meridian great circle to the plotter. A texture mapped Natural Earth
    base layer is also rendered.

    >>> import geovista
    >>> from geovista.geodesic import line
    >>> p = geovista.GeoPlotter()
    >>> _ = p.add_base_layer(texture=geovista.natural_earth_1())
    >>> meridian = line(lons=-180, lats=[90, 0, -90])
    >>> _ = p.add_mesh(meridian, color="orange", line_width=3)
    >>> p.view_xy()
    >>> p.show()

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

    lons, lats = np.atleast_1d(lons), np.atleast_1d(lats)

    # check whether to auto-repeat lons or lats
    if (lons.size == 1 or lats.size == 1) and (lons.size + lats.size > 2):
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
    if np.isclose(lons[0], lons[-1]) and np.isclose(lats[0], lats[-1]) and n_lons == 2:
        emsg = (
            "Require a closed line (loop) geometry containing at least 3 "
            f"longitude/latitude values, got '{n_lons}'."
        )
        raise ValueError(emsg)

    line_lons: list[float] = []
    line_lats: list[float] = []
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
    *,
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

    Note that longitudes (degrees) will be wrapped to the half-closed interval
    ``[-180, 180)``.

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
    npts : int, optional
        The number of points to be returned, which may include the start-point
        and/or the end-point, if required. Defaults to :data:`GEODESIC_NPTS`.
    radians : bool, optional
        If ``True``, the start and end points are assumed to be in radians,
        otherwise degrees. Defaults to ``False``.
    include_start : bool, optional
        Whether to include the start-point in the geodesic points returned. Defaults to
        ``False``.
    include_end : bool, optional
        Whether to include the end-point in the geodesic points returned. Defaults to
        ``False``.
    geod : Geod, optional
        Definition of the ellipsoid for geodesic calculations. Defaults to
        :data:`ELLIPSE`.

    Returns
    -------
    tuple
        Tuple of longitude points and latitude points along the geodesic line
        between the start-point and the end-point.

    Notes
    -----
    .. versionadded:: 0.1.0

    Examples
    --------
    >>> from geovista.geodesic import npoints
    >>> import numpy as np
    >>> points = npoints(start_lon=-10, start_lat=20, end_lon=10, end_lat=30, npts=5)
    >>> np.array(points, dtype=np.float16)
    array([[-6.887, -3.69 , -0.41 ,  2.963,  6.43 ],
           [21.84 , 23.62 , 25.34 , 26.98 , 28.53 ]], dtype=float16)

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
    glons, glats = zip(*glonlats, strict=True)
    glons = tuple(wrap(glons))

    return glons, glats


def npoints_by_idx(
    lons: ArrayLike,
    lats: ArrayLike,
    start_idx: int,
    end_idx: int,
    *,
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

    Note that longitudes (degrees) will be wrapped to the half-closed interval
    ``[-180, 180)``.

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
    npts : int, optional
        The number of points to be returned, which may include the start-point
        and/or the end-point, if required. Defaults to :data:`GEODESIC_NPTS`.
    radians : bool, optional
        If ``True``, the `lons` and `lats` are assumed to be in radians,
        otherwise degrees. Defaults to ``False``.
    include_start : bool, optional
        Whether to include the start-point in the geodesic points returned. Defaults
        to ``False``.
    include_end : bool, optional
        Whether to include the end-point in the geodesic points returned. Defaults to
        ``False``.
    geod : Geod, optional
        Definition of the ellipsoid for geodesic calculations. Defaults to
        :data:`ELLIPSE`.

    Returns
    -------
    tuple
        Tuple of longitude points and latitude points along the geodesic line
        between the start-point and the end-point.

    Notes
    -----
    .. versionadded:: 0.1.0

    Examples
    --------
    >>> from geovista.geodesic import npoints_by_idx
    >>> import numpy as np
    >>> points = npoints_by_idx(
    ...     lons=[-10, 0, 10], lats=[20, 25, 30], start_idx=0, end_idx=1, npts=5
    ... )
    >>> np.array(points, dtype=np.float16)
    array([[-8.38 , -6.746, -5.09 , -3.414, -1.718],
           [20.88 , 21.73 , 22.58 , 23.4  , 24.22 ]], dtype=float16)


    """
    if geod is None:
        geod = pyproj.Geod(ellps=ELLIPSE)

    start_lonlat = lons[start_idx], lats[start_idx]
    end_lonlat = lons[end_idx], lats[end_idx]

    return npoints(
        *start_lonlat,
        *end_lonlat,
        npts=npts,
        radians=radians,
        include_start=include_start,
        include_end=include_end,
        geod=geod,
    )


def panel(
    name: int | str,
    /,
    *,
    ellps: str | None = ELLIPSE,
    c: int = BBOX_C,
    triangulate: bool | None = False,
) -> BBox:
    """Create boundary-box for specific cubed-sphere panel.

    Parameters
    ----------
    name : int or str
        The cubed-sphere index, see :data:`PANEL_NAME_BY_IDX`, or name, see
        :data:`PANEL_IDX_BY_NAME`, which specifies the panel bounding-box,
        see :data:`PANEL_BBOX_BY_IDX`.
    ellps : str, optional
        The ellipsoid for geodesic calculations. See :func:`pyproj.list.get_ellps_map`.
        Defaults to :data:`ELLIPSE`.
    c : float, optional
        The bounding-box face geometry will contain ``c**2`` cells. Defaults
        to :data:`BBOX_C`.
    triangulate : bool, optional
        Specify whether the panel bounding-box faces are triangulated. Defaults to
        ``False``.

    Returns
    -------
    BBox
        The bounding-box that encloses the required cubed-sphere panel.

    Notes
    -----
    .. versionadded:: 0.1.0

    Examples
    --------
    Add a ``wireframe`` bounding-box to the plotter for the ``americas`` panel of a
    cubed-sphere. The geodesic bounding-box is generated from the 4 corners of the
    cubed-sphere panel located over Americas.  A texture mapped Natural Earth base
    layer is also rendered.

    >>> import geovista
    >>> from geovista.geodesic import panel
    >>> p = geovista.GeoPlotter()
    >>> _ = p.add_base_layer(texture=geovista.natural_earth_hypsometric(), opacity=0.5)
    >>> bbox = panel("americas", c=5, triangulate=True)
    >>> _ = p.add_mesh(bbox.mesh, color="orange", show_edges=True)
    >>> p.view_xz()
    >>> p.show()

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
                f"[0, {N_PANELS - 1}], got '{idx}'."
            )
            raise ValueError(emsg)

    lons, lats = PANEL_BBOX_BY_IDX[idx]

    return BBox(lons, lats, ellps=ellps, c=c, triangulate=triangulate)


def wedge(
    lon1: float,
    lon2: float,
    *,
    ellps: str | None = ELLIPSE,
    c: int = BBOX_C,
    triangulate: bool | None = False,
) -> BBox:
    """Create geodesic bounding-box manifold wedge from the north to the south pole.

    Parameters
    ----------
    lon1 : float
        The first longitude (degrees) defining the geodesic wedge region.
    lon2 : float
        The second longitude (degrees) defining the geodesic wedge region.
    ellps : str, optional
        The ellipsoid for geodesic calculations. See :func:`pyproj.list.get_ellps_map`.
        Defaults to :data:`ELLIPSE`.
    c : float, optional
        The bounding-box face geometry will contain ``c**2`` cells. Defaults
        to :data:`BBOX_C`.
    triangulate : bool, optional
        Specify whether the wedge bounding-box faces are triangulated. Defaults to
        ``False``.

    Returns
    -------
    BBox
        The bounding-box that encloses the required geodesic wedge.

    Notes
    -----
    .. versionadded:: 0.1.0

    Examples
    --------
    Add a ``C8`` sixty-degree wide ``wireframe`` bounding-box wedge to the plotter. A
    texture mapped NASA Blue Marble base layer is also rendered.

    >>> import geovista
    >>> from geovista.geodesic import wedge
    >>> p = geovista.GeoPlotter()
    >>> _ = p.add_base_layer(texture=geovista.blue_marble(), opacity=0.5)
    >>> bbox = wedge(-30, 30, c=5)
    >>> _ = p.add_mesh(bbox.mesh, color="orange", show_edges=True)
    >>> p.view_yz()
    >>> p.show()

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
