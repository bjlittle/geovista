#!/usr/bin/env python3
"""Importable and runnable geovista example.

Notes
-----
.. versionadded:: 0.5.0

"""
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from itertools import combinations
from pathlib import Path

try:
    import h3
except ImportError:
    emsg = (
        "Missing optional dependency 'h3' is required for the "
        f"{Path(__file__).stem!r} example. Use pip or conda to install."
    )
    raise ImportError(emsg) from None

import numpy as np
from numpy import ma
from numpy.typing import ArrayLike
from pyvista import PolyData

import geovista
from geovista.geodesic import line
import geovista.theme

#: Missing Data Indicator
MDI = -1

#: Type alias
H3AssetLike = str | PolyData
H3Indexes = set[str]


@dataclass(slots=True)
class H3Asset:
    """Data container for Uber H3 assets."""

    icosahedron: H3AssetLike
    icosahedron_edges: H3AssetLike
    resolution_0: H3AssetLike
    resolution_1: H3AssetLike
    resolution_2: H3AssetLike
    resolution_3: H3AssetLike
    base_layer: H3AssetLike


@dataclass
class GeoSurface:
    """Data container for the geometry and topology of a geo-located surface."""

    lons: ArrayLike
    lats: ArrayLike
    connectivity: ArrayLike


def to_mesh(h3indexes: H3Indexes) -> PolyData:
    """Create a mesh surface for the provided Uber H3 cells.

    Parameters
    ----------
    h3indexes : set of str
        One or more 64-bit ``H3Index`` strings, specifying each cell to add to the mesh.

    Returns
    -------
    PolyData
        The H3 mesh surface.

    """
    nverts, lats, lons = [], [], []

    # Get the lat/lon vertices of each H3Index cell polygon.
    for h3index in h3indexes:
        boundary = h3.h3_to_geo_boundary(h3index, geo_json=False)
        boundary_lats, boundary_lons = zip(*boundary, strict=True)
        lats.extend(boundary_lats)
        lons.extend(boundary_lons)
        nverts.append(len(boundary_lats))

    # Create an empty cell connectivity for the mesh filled with MDI.
    # Note that, each cell may contain a variable number of vertices.
    shape = (len(nverts), np.max(nverts))
    connectivity = np.ones(shape, dtype=int) * MDI

    # Now populate the connectivity with the cell indices.
    start = 0
    for i, step in enumerate(nverts):
        connectivity[i, :step] = range(start, start + step)
        start += step

    # Create the mesh from the H3 geometry and topology.
    connectivity = ma.masked_equal(connectivity, MDI)
    mesh = geovista.Transform.from_unstructured(lons, lats, connectivity=connectivity)

    return mesh


def to_children(h3indexes: H3Indexes) -> H3Indexes:
    """Determine the child hexagon/pentagon cells of the parent cells.

    The child cells will be at the next resolution of the parent cell.

    Note that, a hexagon parent has 7 children, whereas a pentagon parent
    only has 6 children. A pentagon parent will always contain a pentagon
    child. A hexagon parent will never contain a pentagon child.

    Parameters
    ----------
    h3indexes : set of str
       One or more 64-bit ``H3Index`` strings of parent cells.

    Returns
    -------
    set of str
        The children cell indexes.

    """
    result = set()
    children = [h3.h3_to_children(h3index) for h3index in h3indexes]
    result.update(*children)

    return result


def generate_icosahedron_surface(resolution: int | None = 0) -> GeoSurface:
    """Find the location and connectivity of all pentagon cells.

    For each ``resolution`` there will always be 12 pentagons, centered at the
    vertices of the underlying (Platonic solid) icosahedron.

    Parameters
    ----------
    resolution : int
       The resolution of the Uber H3 mesh.

    Returns
    -------
    GeoSurface
       The lat/lon cell centers of the pentagon cells and the icosahedron
       face connectivity.

    """
    pairs = [h3.h3_to_geo(cell) for cell in sorted(h3.get_pentagon_indexes(resolution))]
    lats, lons = list(zip(*pairs, strict=True))

    # An icosahedron contains 20 equilateral triangle faces, 12 vertices and 30 edges.
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

    surface = GeoSurface(lons=lons, lats=lats, connectivity=connectivity)

    return surface


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
    # Generate the set of 30 unique vertex index pairs defining the icosahedron edges.
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
    combined = meshes[0].append_polydata(*meshes[1:])

    return combined


def add_checkboxes(
    plotter: geovista.GeoPlotter, colors: H3Asset, actors: H3Asset
) -> None:
    """Render the checkbox for each ``H3Asset``.

    A checkbox is created for each actor will allows the visibility
    of the actor to be toggled on/off within the `plotter` scene.

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

    def callback(actor, flag):
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
        plotter.add_text(
            title,
            position=(x + size + offset, y + i * (size + pad) + offset),
            font_size=8,
            shadow=True,
            color=getattr(colors, slot),
        )


def main() -> None:
    """Create Uber H3 hexagonal hierarchical spatial index meshes.

    This example demonstrates the relationship between the base icosahedron
    Platonic solid of H3 and its base resolution mesh consisting of
    110 hexagons and 12 pentagons. Note that, a spherical surface cannot be
    tessellated solely with hexagons; pentagons are also required.

    The 12 vertices of the underlying icosahedron anchors the position of the
    pentagon cell centers, around which the hexagons are tessellated to form
    a fixed base mesh. Note that, all pentagons are located over ocean, which
    suits the business model of Uber, and incidentally are the locations of
    most projection distortion.

    H3 is a hierarchical geospatial index. Each cell has a unique 64-bit
    ``H3Index`` that identifies its geospatial location and position in the H3
    hierarchy. Every parent hexagonal cell is subdivided into 7 child
    hexagonal cells, and every parent pentagon is subdivided into 6 child
    cells, one of which is a pentagon.

    From the coarsest base resolution, consisting of 122 cells, there are
    a further 15 increasingly higher resolution hierarchical child meshes.
    The finest resolution mesh consists of 569,707,381,193,162 cells, with
    each resolution always containing 12 pentagons centered over the base
    icosahedron vertices.

    The average area of a base resolution hexagonal polyhedron cell is
    ~4,357,449 km^2, whereas the average area of the finest resolution
    hexagonal cell is ~0.895 m^2.

    Given a ``H3Index``, it is trivial to calculate the resolution, location
    and neighbours of a cell, as well as all its child cells and parent cell.
    Note that, the neighbours of a hexagon or a pentagon in a tessellated
    mesh are equidistant, unlike a mesh consisting of triangles or squares.

    This example renders the H3 base resolution mesh and the next 3 child
    resolutions in the hierarchy, along with the base icosahedron and its
    projected edges on the sphere.

    Natural Earth coastlines are rendered to clarify geolocation, along with
    a Natural Earth base layer.

    The visibility of each actor, apart from the coastlines, can be toggled
    interactively via checkbox buttons, allowing the viewer to easily explore
    the relationship between the geometric objects rendered in the scene.

    For further information see https://h3geo.org/.

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

    indexes_resolution_0 = h3.get_res0_indexes()
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

    plotter = geovista.GeoPlotter()
    style = "wireframe"
    actor_base_layer = plotter.add_base_layer(
        texture=geovista.natural_earth_hypsometric(), zlevel=0
    )
    actor_resolution_0 = plotter.add_mesh(
        mesh_resolution_0,
        style=style,
        line_width=4,
        color=color.resolution_0,
        zlevel=60,
        lighting=False,
    )
    actor_icosahedron_edges = plotter.add_mesh(
        generate_geodesic_edges(surface),
        line_width=4,
        color=color.icosahedron_edges,
        zlevel=60,
        lighting=False,
    )
    actor_resolution_1 = plotter.add_mesh(
        mesh_resolution_1,
        style=style,
        line_width=3,
        color=color.resolution_1,
        zlevel=10,
        lighting=False,
    )
    actor_resolution_2 = plotter.add_mesh(
        mesh_resolution_2,
        style=style,
        line_width=2,
        color=color.resolution_2,
        zlevel=5,
        lighting=False,
    )
    actor_resolution_3 = plotter.add_mesh(
        mesh_resolution_3,
        style=style,
        line_width=1,
        color=color.resolution_3,
        zlevel=1,
        lighting=False,
    )
    actor_icosahedron = plotter.add_mesh(
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
    add_checkboxes(plotter, color, actor)

    plotter.add_text(
        "Uber H3: Hexagonal Hierarchical Spatial Index",
        position="upper_left",
        font_size=10,
        shadow=True,
    )
    plotter.add_coastlines()
    plotter.show()


if __name__ == "__main__":
    main()
