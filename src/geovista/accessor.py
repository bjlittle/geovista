# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""The ``gv`` namespace that geovista adds to every pyvista mesh.

Importing :mod:`geovista` registers it, so every mesh has ``mesh.gv``. It
imports only :mod:`pyvista` here, and reads the mesh as it is used, so that
importing :mod:`geovista` stays light.

Notes
-----
.. versionadded:: 0.6.0

"""

from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

import pyvista as pv

if TYPE_CHECKING:
    from pyproj import CRS

    from .globe import Globe

__all__ = ["GeoVistaAccessor"]


def _same(one: object, two: object) -> bool:
    """Compare two values, either of which may be ``None``.

    Parameters
    ----------
    one : object
        A value, or ``None``.
    two : object
        Another value, or ``None``.

    Returns
    -------
    bool
        Whether both are ``None``, or neither is and they are equal.

    """
    if one is None or two is None:
        return one is None and two is None
    return bool(one == two)


@pv.register_dataset_accessor("gv", pv.DataSet)
class GeoVistaAccessor:
    """The ``gv`` namespace that geovista adds to every pyvista mesh.

    It holds how geovista describes the mesh: its globe and its CRS, each
    read from the mesh's field data at every access, so it never goes stale.
    Neither can be set, and reading never changes the mesh.

    Two namespaces are equal when their meshes have equal CRSs and equal
    globes, whatever their points.

    Parameters
    ----------
    mesh : pyvista.DataSet
        The mesh.

    Notes
    -----
    .. versionadded:: 0.6.0

    Examples
    --------
    >>> import geovista as gv
    >>> import pyvista as pv
    >>> mesh = pv.Sphere(radius=1.0)
    >>> mesh.gv.globe == gv.Globe()
    True
    >>> mesh.gv.crs is None
    True

    """

    __slots__ = ("__weakref__", "_mesh")

    def __init__(self, mesh: pv.DataSet) -> None:
        """Hold the mesh the namespace describes.

        Parameters
        ----------
        mesh : pyvista.DataSet
            The mesh.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        self._mesh = mesh

    @property
    def globe(self) -> Globe | None:
        """The globe the mesh records.

        Returns
        -------
        Globe or None
            The globe, read as :meth:`geovista.globe.Globe.from_mesh` reads
            it, or ``None`` when it cannot be read.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        from .globe import Globe  # noqa: PLC0415

        return Globe.from_mesh(self._mesh)

    @globe.setter
    def globe(self, _value: object) -> NoReturn:
        """Refuse to set the globe, which describes where the points are.

        Parameters
        ----------
        _value : object
            The globe, which is refused.

        Raises
        ------
        AttributeError
            Always.

        """
        emsg = (
            "mesh.gv.globe cannot be set, since a globe describes where a "
            "mesh's points are. Use geovista.core.resize(mesh, globe=...) to "
            "move them and record it."
        )
        raise AttributeError(emsg)

    @property
    def crs(self) -> CRS | None:
        """The CRS of the mesh.

        Returns
        -------
        pyproj.CRS or None
            The CRS, read from the mesh's WKT as
            :func:`geovista.crs.from_wkt` reads it, or ``None``.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        from .crs import from_wkt  # noqa: PLC0415

        return from_wkt(self._mesh)

    @crs.setter
    def crs(self, _value: object) -> NoReturn:
        """Refuse to set the CRS, which describes where the points are.

        Parameters
        ----------
        _value : object
            The CRS, which is refused.

        Raises
        ------
        AttributeError
            Always.

        """
        emsg = (
            "mesh.gv.crs cannot be set, since a CRS describes where a mesh's "
            "points are. Use geovista.transform.transform_mesh to move them "
            "and record it."
        )
        raise AttributeError(emsg)

    def __eq__(self, other: object) -> bool:
        """Compare the CRSs and globes of two meshes, never their geometry.

        Parameters
        ----------
        other : object
            The other namespace.

        Returns
        -------
        bool
            Whether the meshes have equal CRSs and equal globes.

        """
        if not isinstance(other, GeoVistaAccessor):
            return NotImplemented
        return _same(self.crs, other.crs) and _same(self.globe, other.globe)

    # a namespace follows a mesh that can change, so it cannot be hashed
    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        """Name geovista, and the globe and CRS of the mesh.

        Returns
        -------
        str
            The repr, showing a globe that cannot be read by its error.

        """
        try:
            globe = repr(self.globe)
        except ValueError as err:
            globe = f"<cannot be read: {err}>"
        crs = self.crs
        name = None if crs is None else crs.name
        return f"<geovista namespace: globe={globe}, crs={name!r}>"
