from typing import Tuple

import iris
from iris import NameConstraint
from iris.cube import Cube
import numpy as np

import geovista as gv
import geovista.theme


def prepare(fname: str, std_name: str) -> Tuple[Cube, np.ndarray, np.ndarray]:
    cubes = iris.load(fname)

    cube = cubes.extract_cube(std_name)
    lons = cube.coord("longitude").points
    lats = cube.coord("latitude").points
    base_lon_size = cube.attributes["base_lon_size"]
    base_lat_size = cube.attributes["base_lat_size"]

    cx = cubes.extract_cube(NameConstraint(var_name="cx")).data
    cy = cubes.extract_cube(NameConstraint(var_name="cy")).data

    dlon = cx * base_lon_size
    dlat = cy * base_lat_size

    fac = 0.5
    x1 = (lons - fac * dlon).reshape(-1, 1)
    x2 = (lons + fac * dlon).reshape(-1, 1)
    y1 = (lats - fac * dlat).reshape(-1, 1)
    y2 = (lats + fac * dlat).reshape(-1, 1)

    lons = np.hstack([x1, x2, x2, x1])
    lats = np.hstack([y1, y1, y2, y2])

    return cube, lons, lats


fname = "./gbl_2021112300.nc"
cube, lons, lats = prepare(fname, "sea_surface_wave_significant_height")

mesh = gv.Transform.from_unstructured(
    lons, lats, lons.shape, data=cube.data[0], name=cube.name()
)

plotter = gv.GeoPlotter()
sargs = dict(title=f"{cube.name()} / {cube.units}")
plotter.add_mesh(mesh, cmap="balance", show_edges=False, scalar_bar_args=sargs)
plotter.add_base_layer(texture=gv.natural_earth_hypsometric())
resolution = "10m"
plotter.add_coastlines(resolution=resolution, color="white")
plotter.add_axes()
plotter.add_text(
    f"Spherical Multi-Cell ({resolution} Coastlines)",
    position="upper_left",
    font_size=10,
    shadow=True,
)
plotter.show()
