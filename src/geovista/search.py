"""
This module contains convenience functionality to find points or cells
within a mesh using various techniques.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

from collections.abc import Iterable
from typing import List, Optional, Union

import numpy as np
from pyvista import PolyData

from .common import to_xyz
from .crs import WGS84, from_wkt

__all__ = ["find_cell_neighbours", "find_nearest_cell"]

# type aliases
CellIDs = List[int]
CellIDLike = Union[int, CellIDs]


def find_cell_neighbours(mesh: PolyData, cid: CellIDLike) -> CellIDs:
    """
    Determine all the cells neighbouring the given `cid` cell/s of the `mesh`.

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
    list of ints
        The sorted list of neighbouring cell-ids.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if not isinstance(cid, Iterable):
        cid = [cid]

    pids = []
    for idx in cid:
        # XXX: pyvista 0.38.0: cell_point_ids(idx) -> get_cell(idx).point_ids
        pids.extend(mesh.cell_point_ids(idx))

    # determine the unique points
    pids = np.unique(list(pids))
    # get the cell-ids of cells containing at least one common point
    result = set(mesh.extract_points(pids)["vtkOriginalCellIds"])
    # remove the original cell/s
    result -= set(cid)

    return sorted(result)


def find_nearest_cell(
    mesh: PolyData,
    x: float,
    y: float,
    z: Optional[float] = 0,
    single: Optional[bool] = False,
) -> CellIDLike:
    """
    Determine the ``cellID`` of the cell in the `mesh` that is closest
    to the provided point-of-interest (POI).

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
    poi = to_xyz(x, y)[0] if crs in [WGS84, None] else (x, y, z)
    cid = mesh.find_closest_cell(poi)

    # XXX: pyvista 0.38.0: cell_point_ids(cid) -> get_cell(cid).point_ids
    pids = np.asanyarray(mesh.cell_point_ids(cid))
    points = mesh.points[pids]
    mask = np.all(np.isclose(points, poi), axis=1)
    poi_is_vertex = np.any(mask)

    if poi_is_vertex:
        pid = pids[mask][0]
        result = sorted(mesh.extract_points(pid)["vtkOriginalCellIds"])
    else:
        result = [cid]

    if single:
        if (count := len(result)) > 1:
            emsg = (
                f"Expected to find 1 cell but found {count}, " f"got CellIDs {result}."
            )
            raise ValueError(emsg)
        (result,) = result

    return result
