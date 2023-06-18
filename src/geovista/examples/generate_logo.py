"""
Script to create a logo - rotating triangulated globe beneath "GV" text mask.

Things I couldn't get to work:

- Thicker "GV" text - a bold font would do it but that isn't configurable.
- Better z levels. Low poly land mass means that the sea base-layer must be set
much lower, and you can see the gap at the outer edges of the "G" and "V".

Ideas for configuring:

- Choose the 'official' rotation frame for the static logo.
- Colours. I just chose the ones from the Iris logo.
- Lighting of the various layers.
- Tilting the globe, as is done in the Iris logo.
- Level of triangulation/subdivision of the land mass.
- Size of the "GV" mask.
- A border for the "GV" mask? I tried one using PyVista edge detection but it
didn't render smoothly.

"""

from time import sleep

import cartopy.io.shapereader as shp
import numpy as np
from pyvista import Box, PointSet, PolyData, Text3D

from geovista import GeoPlotter, theme
from geovista.common import to_cartesian

# Touch the theme import.
_ = theme


# Size of the "GV" text relative to the full globe.
TEXT_SCALE_FACTOR = 0.4


def get_dim_size(bounds: tuple, dim: int) -> float:
    """Get a PolyData's max size in the given dimension, by parsing the bounds."""
    idx_lo = dim * 2
    bound_lo = bounds[idx_lo]
    bound_hi = bounds[idx_lo + 1]
    return bound_hi - bound_lo


def get_centered(polydata: PolyData) -> PointSet:
    """Make a version of the `polydata` that is centered on the canvas."""
    center: tuple = polydata.center
    return polydata.translate(np.array(center) * -1)


def land_polydata() -> PolyData:
    """Create a PolyData of the globe's landmasses, based on the Nat Earth shapefile."""
    land_shapefile = shp.natural_earth(
        resolution="110m", category="physical", name="land"
    )
    reader = shp.Reader(land_shapefile)

    polydata_list = []
    for geometry in reader.geometries():
        # Less complex coastlines.
        geometry = geometry.simplify(0.8, True)
        coords = geometry.exterior.coords
        n_points = len(coords)
        z_coords = np.zeros(n_points)
        coords_xyz = [*coords.xy, z_coords]

        # Convert geometry to PolyData.
        coords_array = np.array(coords_xyz).T
        face_nodes = [n_points + 1] + list(range(n_points)) + [0]
        polydata = PolyData(coords_array, faces=face_nodes, n_faces=1)

        # Give land some internal structure.
        # Triangulation allows further PyVista operations.
        polydata = polydata.triangulate()
        # Subdivide gives more aesthetically pleasing triangles.
        polydata = polydata.subdivide(2, "butterfly")

        # Position land on a globe.
        polydata.points = to_cartesian(
            polydata.points[:, 0], polydata.points[:, 1], zlevel=0
        )

        polydata_list.append(polydata)

    polydata_full = polydata_list[0]
    for polydata_sub in polydata_list[1:]:
        polydata_full = polydata_full.merge(polydata_sub)

    return polydata_full


text = Text3D("GV").triangulate()

# Create a PyVista box that will have the text cut out of it.
globe_bounds = np.array([-180, 180, -90, 90])
# Scale the box appropriately based on the existing text.
#  (Done this way because PyVista had problems upscaling the text).
text_xy_sizes = np.array([get_dim_size(text.bounds, i) for i in (0, 1)])
globe_xy_sizes = np.array([get_dim_size(tuple(globe_bounds), i) for i in (0, 1)])
scaling = np.max(globe_xy_sizes / text_xy_sizes) * TEXT_SCALE_FACTOR
box_bounds = list(globe_bounds / scaling)
# Give the box a z-thickness less than text - to facilitate boolean differencing.
box_bounds += list(np.array(text.bounds)[-2:] / 2)
box = Box(box_bounds, level=100).triangulate()

# Cut the text out of the box, then scale back up to lon-lat size.
text = get_centered(text)
box = get_centered(box)
diff = box - text
diff = diff.scale([scaling, scaling, 1])

# Use the cut-out as a text mask for the land.
text_mask = diff.project_points_to_plane()
text_mask.points = to_cartesian(
    text_mask.points[:, 0], text_mask.points[:, 1], zlevel=15
)

land = land_polydata()

my_plotter = GeoPlotter()
my_plotter.add_mesh(text_mask, color="white", lighting=False)
my_plotter.add_mesh(land, show_edges=True, edge_color="black", color="#aec928")
# The sea of the globe.
my_plotter.add_base_layer(color="#156475", radius=0.99)

my_plotter.show(cpos="yz", interactive_update=True)

# Rotate the land beneath the mask.
for _rot in range(240):
    sleep(1 / 24)
    new_points = land.rotate_z(3).points
    my_plotter.update_coordinates(new_points, land)
