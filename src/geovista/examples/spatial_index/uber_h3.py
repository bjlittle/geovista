#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""
Uber H3 Spatial Index
---------------------

This example demonstrates the Uber ``H3`` hexagonal hierarchical spatial index.

💼 Background
^^^^^^^^^^^^^

A spatial index is a structured collection of shapes that allows you to
approximately describe any region by simply taking a subset of shapes from that
index. The ``H3`` library, developed by Uber as an open source project, uses
hexagons to divide up the earth into cells. ``H3`` is hierarchical, meaning that
there are multiple resolutions of hexagonal meshes dividing the earth. Depending on
the resolution, these hexagonal cells range from **~1m^2** to **~4,000,000km^2**.

The coarsest mesh in ``H3``, the **base resolution mesh**, consists of
**110 hexagons** and **12 pentagons**, this is the starting point in a
hierarchical sequence of hexagonal meshes. Its structure is built on top of a
**base icosahedron**, the relationship between the **base icosahedron** and the
**base resolution mesh** informs the structure of the meshes of the further
meshes in the sequence.
Note that a spherical surface cannot be tessellated solely with hexagons;
pentagons are also required.

The **12 vertices** of the underlying **base icosahedron** anchor the center of
the **12 pentagon cells**, around which the **110 hexagon cells** are tessellated
to form a fixed base mesh. Note that the center of all pentagons are located over
ocean, which suits the business model of Uber. Incidentally, these are the locations
of most projection distortion.

``H3`` is a hierarchical geospatial index. Each cell has a unique 64-bit
``H3Index`` that identifies its geospatial location and position in the ``H3``
hierarchy. Every parent hexagonal cell is subdivided into **7 child
hexagonal cells**, and every parent pentagon cell is subdivided into **6 child
cells**, precisely one of which is a pentagon.

From the coarsest base resolution, consisting of **122 cells**, there are
a further 15 increasingly higher resolution hierarchical child meshes.
The finest resolution mesh consists of **569,707,381,193,162 cells**, with
each resolution **always** containing **12 pentagon cells** centered over the
**base icosahedron** vertices.

The average area of a base (coarsest) resolution hexagonal polyhedron cell is
**~4,357,449 km^2**, whereas the average area of the finest resolution
hexagonal cell is **~0.895 m^2**.

Given a ``H3Index``, it is trivial to calculate the resolution, location
and neighbours of a cell, as well as all its child cells and parent cell.
Note that the neighbours of a hexagon or a pentagon cell in a tessellated
mesh are equidistant, unlike a mesh consisting of triangular or rectangular
cells.

This example renders the ``H3`` base resolution mesh and the next 3 child
resolutions in the hierarchy, along with the base icosahedron and its
projected edges on the sphere.

Natural Earth coastlines are rendered to clarify geolocation, along with
a Natural Earth base layer.

The visibility of each actor, apart from the coastlines, can be toggled
interactively via checkbox buttons, allowing the viewer to easily explore
the relationship between the geometric objects rendered in the scene.

For further information see https://github.com/uber/h3.

.. tags::

    component: coastlines, component: texture,
    load: unstructured,
    widget: checkbox

.. attention::

    Optional package dependency `h3 <https://github.com/uber/h3>`_ is required.

----

"""  # noqa: D205,D212,D400

# %%
# 🦉 Walk-Through
# ^^^^^^^^^^^^^^^
#
# First, let's ``import`` the package dependencies required by the example.
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from itertools import combinations

try:
    import h3
except ImportError:
    emsg = (
        "Missing optional dependency 'h3' is required for the "
        "`uber_h3.py` example. Use pip or conda to install."
    )
    raise ImportError(emsg) from None

import numpy as np
from numpy import ma
from numpy.typing import ArrayLike
from pyvista import Actor, PolyData

import geovista
from geovista.geodesic import line
import geovista.theme  # noqa: F401

# %%
# As a convenience, we create some **type aliases** and **data containers**
# to simplify the code and improve readability. Firstly, the ``H3Asset``
# container holds the various VTK actors that will be rendered within
# the scene.

# Missing Data Indicator
MDI = -1

# Convenient type aliases
type H3AssetLike = str | PolyData
type H3Indexes = set[str]


@dataclass(slots=True)
class H3Asset:
    """Data container of Uber H3 assets."""

    icosahedron: H3AssetLike
    icosahedron_edges: H3AssetLike
    resolution_0: H3AssetLike
    resolution_1: H3AssetLike
    resolution_2: H3AssetLike
    resolution_3: H3AssetLike
    base_layer: H3AssetLike


# %%
# The ``GeoSurface`` container holds the **geometry** and **topology** of the
# ``H3`` **base icosahedron**.


@dataclass
class GeoSurface:
    """Geometry and topology of a geo-located surface."""

    lons: ArrayLike
    lats: ArrayLike
    connectivity: ArrayLike


# %%
# The ``generate_icosahedron_surface`` function generates the geometry
# and topology of the ``H3`` **base icosahedron**, which is the foundation
# of the entire Uber ``H3`` spatial index.


def generate_icosahedron_surface(resolution: int | None = 0) -> GeoSurface:
    """Find the location and connectivity of all pentagon cells.

    For each ``resolution`` there will always be 12 pentagons,
    centered at the vertices of the underlying (Platonic solid)
    icosahedron.

    Parameters
    ----------
    resolution : int
       The resolution of the Uber H3 mesh.

    Returns
    -------
    GeoSurface
       The lat/lon cell centers of the pentagon cells and the
       icosahedron face connectivity.

    """
    pairs = [h3.cell_to_latlng(cell) for cell in sorted(h3.get_pentagons(resolution))]
    lats, lons = list(zip(*pairs, strict=True))

    # An icosahedron contains 20 equilateral triangle faces,
    # 12 vertices and 30 edges.
    connectivity = [
        [0, 1, 2],
        [0, 3, 1],
        [0, 2, 4],
        [0, 4, 5],
        [0, 5, 3],
        [1, 6, 2],
        [1, 3, 7],
        [1, 7, 6],
        [2, 6, 8],
        [2, 8, 4],
        [4, 8, 10],
        [4, 10, 5],
        [5, 10, 9],
        [5, 9, 3],
        [3, 9, 7],
        [11, 6, 7],
        [11, 8, 6],
        [11, 10, 8],
        [11, 9, 10],
        [11, 7, 9],
    ]

    return GeoSurface(lons=lons, lats=lats, connectivity=connectivity)


# %%
# The ``GeoSurface`` created by the ``generate_icosahedron_surface`` function
# is then used to create a :class:`pyvista.PolyData` mesh containing only the
# **geodesic edges** of the **base icosahedron**.
#
# Rendering these geodesic edges will help clarify to the viewer the position
# of the underlying icosahedron even when it is obscured by a texture mapped
# base layer.


def generate_geodesic_edges(surface: GeoSurface) -> PolyData:
    """Create the mesh of icosahedron geodesic edges.

    Parameters
    ----------
    surface : GeoSurface
       The 12 lat/lon vertices and connectivity of the 20 icosahedron faces.

    Returns
    -------
    PolyData
        The mesh of icosahedron geodesic edges.

    """
    # Generate the set of 30 unique vertex index pairs defining
    # the icosahedron edges.
    segments = set()
    for vertices in surface.connectivity:
        pairs = [tuple(sorted(pair)) for pair in combinations(vertices, 2)]
        segments.update(pairs)

    # Create the geodesic lines between each edge vertex.
    meshes = []
    for idx0, idx1 in segments:
        lons = [surface.lons[idx0], surface.lons[idx1]]
        lats = [surface.lats[idx0], surface.lats[idx1]]
        meshes.append(line(lons, lats))

    # Combine the geodesic lines into one mesh.
    return meshes[0].append_polydata(*meshes[1:])


# %%
# The ``to_children`` function generates all the child cells at the
# next (finer) resolution for each parent cell represented in the set
# of ``H3Index`` strings.


def to_children(h3indexes: H3Indexes) -> H3Indexes:
    """Determine the child cells of the parent cells.

    The child hexagon/pentagon cells will be at the next
    resolution (finer) of the parent cell resolution (coarser).

    Note that a hexagon parent has 7 children, whereas a pentagon
    parent only has 6 children. A pentagon parent will always
    contain a pentagon child. A hexagon parent will never contain
    a pentagon child.

    Parameters
    ----------
    h3indexes : set of str
       One or more 64-bit ``H3Index`` strings of parent cells.

    Returns
    -------
    set of str
        The children cell indexes.

    """
    result: set[str] = set()
    children = [h3.cell_to_children(h3index) for h3index in h3indexes]
    result.update(*children)

    return result


# %%
# The ``to_mesh`` function converts a set of ``H3Index`` strings,
# each of which represent a cell from the same resolution in the
# Uber ``H3`` spatial hierarchy, into a :class:`pyvista.PolyData`
# mesh surface.
#
# Together, the ``to_children`` and ``to_mesh`` functions can be used
# to generate the mesh surface of any resolution in the Uber ``H3``
# spatial hierarchy.


def to_mesh(h3indexes: H3Indexes) -> PolyData:
    """Create a mesh surface for the provided Uber H3 cells.

    Parameters
    ----------
    h3indexes : set of str
        One or more 64-bit ``H3Index`` strings, specifying each
        cell to add to the mesh.

    Returns
    -------
    PolyData
        The H3 mesh surface.

    """
    nverts: list[int] = []
    lats: list[float] = []
    lons: list[float] = []

    # Get the lat/lon vertices of each H3Index cell polygon.
    for h3index in h3indexes:
        boundary = h3.cell_to_boundary(h3index)
        boundary_lats, boundary_lons = zip(*boundary, strict=True)
        lats.extend(boundary_lats)
        lons.extend(boundary_lons)
        nverts.append(len(boundary_lats))

    # Create an empty cell connectivity for the mesh filled
    # with MDI. Note that each cell may contain a variable
    # number of vertices.
    shape = (len(nverts), np.max(nverts))
    connectivity = np.ones(shape, dtype=int) * MDI

    # Now populate the connectivity with the cell indices.
    start = 0
    for i, step in enumerate(nverts):
        connectivity[i, :step] = range(start, start + step)
        start += step

    # Create the mesh from the H3 geometry and topology.
    connectivity = ma.masked_equal(connectivity, MDI)

    return geovista.Transform.from_unstructured(lons, lats, connectivity=connectivity)


# %%
# The ``add_checkboxes`` function adds a checkbox button widget to the
# ``plotter`` for each ``H3Asset`` actor, which includes the following:
#
# * A Natural Earth texture mapped base layer.
# * The icosahedron surface.
# * The icosahedron geodesic edges.
# * The base resolution mesh (coarsest).
# * The next 3 child resolution meshes (increasingly finer).


def add_checkboxes(
    plotter: geovista.GeoPlotter, colors: H3Asset, actors: H3Asset
) -> None:
    """Render the checkbox for each ``H3Asset``.

    A checkbox is created for each actor that allows the
    visibility of the actor to be toggled on/off within the
    `plotter` scene.

    Parameters
    ----------
    plotter : GeoPlotter
       The plotter to render the checkboxes.
    colors : H3Asset
       The color of each checkbox asset.
    actors : H3Asset
       The VTK actors to be toggled by each checkbox.

    """
    color_off = "white"
    size, pad = 30, 3
    x, y = 10, 10
    offset = size * 0.2

    def callback(actor: Actor, flag: bool) -> None:
        actor.SetVisibility(flag)

    for i, slot in enumerate(sorted(H3Asset.__slots__)):
        plotter.add_checkbox_button_widget(
            partial(callback, getattr(actors, slot)),
            value=True,
            color_on=getattr(colors, slot),
            color_off=color_off,
            size=size,
            position=(x, y + i * (size + pad)),
        )

        title = " ".join([word.capitalize() for word in slot.split("_")])
        x_offset = x + size + offset
        y_offset = y + i * (size + pad) + offset
        plotter.add_text(
            title,
            position=(x_offset, y_offset),
            font_size=8,
            color=getattr(colors, slot),
        )


# %%
# .. only:: on_rtd
#
#   .. note::
#     The checkboxes will **not** be rendered when viewing the documentation on
#     ``ReadtheDocs``, as the appropriate VTK widget is not supported in this
#     headless environment.

# %%
# Finally, we create the :class:`~geovista.geoplotter.GeoPlotter` and add the
# **base icosahedron** surface and geodesic edges,
# a Natural Earth base layer and coastlines.
#
# We also use the :func:`h3.get_res0_cells` function to bootstrap the
# Uber ``H3`` hierarchy by generating the ``H3Index`` strings for all
# the cells participating in the base (coarsest) resolution .
#
# The ``to_mesh`` function is then used to convert the ``H3Index`` strings
# into a :class:`pyvista.PolyData` mesh surface, which is then added to
# the plotter. The ``to_children`` function is then used to generate the
# ``H3Index`` strings for the next 3 child resolutions, which are then
# converted into mesh surfaces and also added to the plotter.


def main() -> None:
    """Plot the Uber H3 spatial index.

    Notes
    -----
    .. versionadded:: 0.5.0

    """
    color = H3Asset(
        icosahedron="grey",
        icosahedron_edges="darkgrey",
        resolution_0="black",
        resolution_1="orange",
        resolution_2="lightblue",
        resolution_3="lightgrey",
        base_layer="blue",
    )

    indexes_resolution_0 = h3.get_res0_cells()
    mesh_resolution_0 = to_mesh(indexes_resolution_0)
    indexes_resolution_1 = to_children(indexes_resolution_0)
    mesh_resolution_1 = to_mesh(indexes_resolution_1)
    indexes_resolution_2 = to_children(indexes_resolution_1)
    mesh_resolution_2 = to_mesh(indexes_resolution_2)
    indexes_resolution_3 = to_children(indexes_resolution_2)
    mesh_resolution_3 = to_mesh(indexes_resolution_3)

    # Create the icosahedron surface.
    surface = generate_icosahedron_surface()
    icosahedron = geovista.Transform.from_unstructured(
        surface.lons, surface.lats, connectivity=surface.connectivity
    )

    p = geovista.GeoPlotter()
    style = "wireframe"
    actor_base_layer = p.add_base_layer(
        texture=geovista.natural_earth_hypsometric(), zlevel=0
    )
    actor_resolution_0 = p.add_mesh(
        mesh_resolution_0,
        style=style,
        line_width=4,
        color=color.resolution_0,
        zlevel=60,
        lighting=False,
    )
    actor_icosahedron_edges = p.add_mesh(
        generate_geodesic_edges(surface),
        line_width=4,
        color=color.icosahedron_edges,
        zlevel=60,
        lighting=False,
    )
    actor_resolution_1 = p.add_mesh(
        mesh_resolution_1,
        style=style,
        line_width=3,
        color=color.resolution_1,
        zlevel=10,
        lighting=False,
    )
    actor_resolution_2 = p.add_mesh(
        mesh_resolution_2,
        style=style,
        line_width=2,
        color=color.resolution_2,
        zlevel=5,
        lighting=False,
    )
    actor_resolution_3 = p.add_mesh(
        mesh_resolution_3,
        style=style,
        line_width=1,
        color=color.resolution_3,
        zlevel=1,
        lighting=False,
    )
    actor_icosahedron = p.add_mesh(
        icosahedron, show_edges=True, color=color.icosahedron
    )

    actor = H3Asset(
        icosahedron=actor_icosahedron,
        icosahedron_edges=actor_icosahedron_edges,
        resolution_0=actor_resolution_0,
        resolution_1=actor_resolution_1,
        resolution_2=actor_resolution_2,
        resolution_3=actor_resolution_3,
        base_layer=actor_base_layer,
    )
    add_checkboxes(p, color, actor)

    p.add_text(
        "Uber H3: Hexagonal Hierarchical Spatial Index",
        position="upper_left",
        font_size=10,
    )
    p.add_coastlines()
    p.camera.zoom(1.5)
    p.show()


if __name__ == "__main__":
    main()
