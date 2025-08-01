# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Support to find points or cells within a mesh using various techniques.

Notes
-----
.. versionadded:: 0.1.0

"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

import lazy_loader as lazy
from pykdtree.kdtree import KDTree as pyKDTree

from .common import VTK_CELL_IDS, StrEnumPlus, to_cartesian
from .crs import WGS84, from_wkt
from .transform import transform_points

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import ArrayLike
    import pyvista as pv

    # Type aliases
    NearestNeighbours = tuple[ArrayLike, ArrayLike]
    """Type alias for a tuple of nearest neighbour distances and indices.""" ""

    # these are type aliases
    CellIDs = list[int]
    CellIDLike = int | CellIDs

# lazy import third-party dependencies
np = lazy.load("numpy")

__all__ = [
    "KDTREE_EPSILON",
    "KDTREE_K",
    "KDTREE_LEAF_SIZE",
    "KDTREE_PREFERENCE",
    "KDTree",
    "NearestNeighbours",
    "SearchPreference",
    "find_cell_neighbours",
    "find_nearest_cell",
]

KDTREE_EPSILON: float = 0.0
"""The default kd-tree nearest neighbour epsilon."""

KDTREE_K: int = 1
"""The default kd-tree number of nearest neighbours."""

KDTREE_LEAF_SIZE: int = 16
"""The default kd-tree leaf-size."""

KDTREE_PREFERENCE: str = "point"
"""The default search preference."""


class SearchPreference(StrEnumPlus):
    """Enumeration of mesh geometry search preferences.

    Notes
    -----
    .. versionadded:: 0.3.0

    """

    CENTER = "center"
    """Preference to search the cell centers."""
    POINT = "point"
    """Preference to search the mesh points."""


class KDTree:  # numpydoc ignore=PR01
    """Construct a kd-tree for fast nearest neighbour search of a mesh.

    For further details, see https://github.com/storpipfugl/pykdtree.

    Notes
    -----
    .. versionadded:: 0.3.0

    """

    def __init__(
        self,
        mesh: pv.PolyData,
        /,
        *,
        leaf_size: int | None = None,
        preference: str | SearchPreference | None = None,
    ) -> None:
        """Construct kd-tree for nearest neighbour search of mesh points/cell centers.

        Note that, the cell centers will be calculated from the mesh geometry and do not
        require to be provided.

        The geolocated mesh data points are converted to cartesian coordinates on a S2
        sphere, as the kd-tree implementation uses Euclidean distance as the metric for
        nearest neighbours.

        Nearest neighbour queries are optionally multi-threaded using OpenMP. For
        further details see https://github.com/storpipfugl/pykdtree.

        Parameters
        ----------
        mesh : PolyData
            The mesh used to construct the kd-tree.
        leaf_size : int, optional
            The number of data points per tree leaf. Used to control the memory overhead
            of the kd-tree. Increasing the leaf size will reduce the memory overhead and
            construction time, but increase the query time. Defaults to
            :data:`KDTREE_LEAF_SIZE`.
        preference : str or SearchPreference, optional
            Construct the kd-tree from the `mesh` points ``point`` or cell centers
            ``center``. Also see :class:`SearchPreference`. Defaults to
            :data:`KDTREE_PREFERENCE`.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        if leaf_size is None:
            leaf_size = KDTREE_LEAF_SIZE

        leaf_size = int(leaf_size)

        if preference is None:
            preference = KDTREE_PREFERENCE

        if not SearchPreference.valid(preference):
            options = " or ".join(f"{item!r}" for item in SearchPreference.values())
            emsg = f"Expected a preference of {options}, got '{preference}'."
            raise ValueError(emsg)

        self._preference = SearchPreference(preference)
        xyz = (
            mesh.points
            if self._preference == SearchPreference.POINT
            else mesh.cell_centers().points
        )
        crs = from_wkt(mesh)

        if crs is None:
            crs = WGS84

        if crs != WGS84:
            transformed = transform_points(
                src_crs=crs, tgt_crs=WGS84, xs=xyz[:, 0], ys=xyz[:, 1]
            )
            # TODO @bjlittle: Clarify zlevel preservation for non-WGS84 point-clouds.
            xyz = to_cartesian(transformed[:, 0], transformed[:, 1])

        self._n_points: int = xyz.shape[0]
        self._mesh_type = mesh.__class__.__name__
        self._kdtree = pyKDTree(xyz, leafsize=leaf_size)

    def __repr__(self) -> str:
        """Serialize kd-tree representation.

        Returns
        -------
        str

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        klass = f"{self.__class__.__name__}"
        mesh = f"<{self._mesh_type} N POINTS: {self._n_points}>"
        leaf_size = f"leaf_size={self.leaf_size}"
        preference = f"preference='{self.preference}'"
        return f"{klass}({mesh}, {leaf_size}, {preference})"

    @property
    def leaf_size(self) -> int:
        """The number of data points per tree leaf.

        Used to control the memory overhead of the kd-tree. Increasing the leaf size
        will reduce the memory overhead and construction time, but increase the query
        time.

        Returns
        -------
        int
            The leaf size i.e., the number of data points per leaf, for the tree
            creation.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        result = self._kdtree.leafsize
        assert isinstance(result, int)
        return result

    @property
    def n_points(self) -> int:
        """Number of mesh points registered with the kd-tree.

        Returns
        -------
        int
            The number of mesh points in the kd-tree.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        return self._n_points

    @property
    def points(self) -> np.ndarray:
        """The cartesian data points registered with the kd-tree.

        Returns
        -------
        np.ndarray
            The cartesian data points in the kd-tree.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        return self._kdtree.data.reshape(-1, 3).copy()

    @property
    def preference(self) -> SearchPreference:
        """The target mesh geometry to search.

        Focus either on the mesh points or the mesh cell centers.

        Returns
        -------
        SearchPreference
            The preference of mesh geometry to search.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        return self._preference

    def query(
        self,
        lons: float | ArrayLike,
        lats: float | ArrayLike,
        /,
        *,
        k: int | None = None,
        epsilon: float | None = None,
        distance_upper_bound: float | None = None,
        radius: float | None = None,
        zlevel: float | ArrayLike | None = None,
        zscale: float | None = None,
    ) -> NearestNeighbours:
        """Query the kd-tree for `k` nearest neighbours per point-of-interest.

        Parameters
        ----------
        lons : float or ArrayLike
            One or more longitude values for the query points-of-interest.
        lats : float or ArrayLike
            One or more latitude values for the query points-of-interest.
        k : int, optional
            The number of nearest neighbours to find per point-of-interest. Defaults
            to :data:`KDTREE_K`.
        epsilon : non-negative float, optional
            Return approximate nearest neighbours; the k-th returned value
            is guaranteed to be no further than (1 + epsilon) times the distance
            to the real k-th nearest neighbour. Defaults to :data:`KDTREE_EPSILON`.
        distance_upper_bound : non-negative float, optional
            Return only neighbors within this distance. This is used to prune tree
            searches.
        radius : float, optional
            The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.
        zlevel : float or ArrayLike, default=0.0
            The z-axis level. Used in combination with the `zscale` to offset the
            `radius` by a proportional amount i.e., ``radius * zlevel * zscale``.
            If `zlevel` is not a scalar, then its shape must match or broadcast
            with the shape of `lons` and `lats`.
        zscale : float, optional
            The proportional multiplier for z-axis `zlevel`. Defaults to
            :data:`geovista.common.ZLEVEL_SCALE`.

        Returns
        -------
        NearestNeighbours
            The Euclidean distance and index of the k nearest neighbours for each
            query point-of-interest.

        Notes
        -----
        .. versionadded:: 0.3.0

        """
        if k is None:
            k = KDTREE_K

        if epsilon is None:
            epsilon = KDTREE_EPSILON

        xyz = to_cartesian(lons, lats, radius=radius, zlevel=zlevel, zscale=zscale)

        result = self._kdtree.query(
            xyz, k=k, eps=epsilon, distance_upper_bound=distance_upper_bound
        )
        assert isinstance(result, tuple)
        assert len(result) == 2
        return result


def find_cell_neighbours(mesh: pv.PolyData, cid: CellIDLike) -> CellIDs:
    """Find all the cells neighbouring the given `cid` cell/s of the `mesh`.

    A cell is deemed to neighbour a `cid` cell if it shares at least one
    vertex.

    Parameters
    ----------
    mesh : PolyData
        The mesh defining the points cells.
    cid : int or list of int
        The offset of the cell/s in the `mesh` that is/are the focus of the
        neighbourhood.

    Returns
    -------
    list of int
        The sorted list of neighbouring cell-ids.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if not isinstance(cid, Iterable):
        cid = [cid]

    pids = []
    for idx in cid:
        # NOTE: pyvista 0.38.0: cell_point_ids(idx) -> get_cell(idx).point_ids
        pids.extend(mesh.get_cell(idx).point_ids)

    # determine the unique points
    pids = np.unique(list(pids))
    # get the cell-ids of cells containing at least one common point
    result = set(mesh.extract_points(pids)[VTK_CELL_IDS])
    # remove the original cell/s
    result -= set(cid)

    return sorted(result)


def find_nearest_cell(
    mesh: pv.PolyData,
    /,
    x: float,
    y: float,
    z: float | None = 0,
    *,
    single: bool | None = False,
) -> CellIDLike:
    """Find the cell in the `mesh` that is closest to the point-of-interest (POI).

    Assumes that the POI is in the canonical units of the `gvCRS`
    associated with the `mesh`, otherwise assumes geographic longitude
    and latitude.

    If the POI is coincident with a vertex of the `mesh`, then the
    ``cellID`` of each cell face which shares that vertex is returned.

    Parameters
    ----------
    mesh : PolyData
        The mesh defining the points, cells and CRS.
    x : float
        The POI x-coordinate. Defaults to ``longitude`` if no `mesh` CRS is
        available.
    y : float
        The POI y-coordinate. Defaults to ``latitude`` if no `mesh` CRS is
        available.
    z : float, optional
        The POI z-coordinate, if applicable. Defaults to zero.
    single : bool, default=False
        Enforce expectation of only one nearest ``cellID`` result. Otherwise,
        a sorted list of ``cellIDs`` are returned.

    Returns
    -------
    int or list of int
        The cellID of the closest mesh cell, or the cellIDs that share the
        coincident point-of-interest as a node.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    crs = from_wkt(mesh)
    poi = to_cartesian(x, y)[0] if crs in [WGS84, None] else (x, y, z)
    cid = mesh.find_closest_cell(poi)

    # NOTE: pyvista 0.38.0: cell_point_ids(cid) -> get_cell(cid).point_ids
    pids = np.asanyarray(mesh.get_cell(cid).point_ids)
    points = mesh.points[pids]
    mask = np.all(np.isclose(points, poi), axis=1)
    poi_is_vertex = np.any(mask)

    if poi_is_vertex:
        pid = pids[mask][0]
        result = sorted(mesh.extract_points(pid)[VTK_CELL_IDS])
    else:
        result = [cid]

    if single:
        if (count := len(result)) > 1:
            emsg = f"Expected to find 1 cell but found {count}, got CellIDs {result}."
            raise ValueError(emsg)
        (result,) = result

    return result
