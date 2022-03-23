.. title:: GeoVista

.. jupyter-execute::
   :hide-code:

   # configure pyvista for pythreejs
   import pyvista
   pyvista.set_jupyter_backend("pythreejs")
   pyvista.global_theme.background = "white"
   pyvista.global_theme.window_size = [700, 500]
   pyvista.global_theme.axes.show = True
   pyvista.global_theme.antialiasing = True


.. toctree::
   :maxdepth: 1
   :caption: Contents:


.. raw:: html

   <h1 align="center">
     <img src="https://raw.githubusercontent.com/bjlittle/geovista/main/branding/logo/secondary/geovistalogo2.png" alt="GeoVista">
   </h1>
   <h4 align="center">
       Cartographic rendering and mesh analytics powered by <a href="https://docs.pyvista.org/index.html">PyVista</a>
   </h4>
   <br>

We're just bootstrapping ``geovista`` and its documentation, so please be patient 👍

In the meantime, here's a ``geovista`` amuse-bouche to whet your appetite...

Render a mesh from a uniform grid with random cell data and 1:10m Natural Earth coastlines.

.. jupyter-execute::

   import numpy as np
   import geovista as gv


   # Generate a synthetic uniform grid.
   M, N = 45, 90
   lats = np.linspace(-90, 90, M + 1)
   lons = np.linspace(-180, 180, N + 1)
   data = np.random.uniform(low=250, high=303, size=M * N)

   # Create a mesh from the grid.
   mesh = gv.Transform.from_1d(lons, lats, data=data)

   plotter = gv.GeoPlotter()
   plotter.add_mesh(mesh, cmap='balance', show_edges=True)
   plotter.add_coastlines(resolution="10m", color="white")
   plotter.show()

Render a base layer mesh with 1:10m Natural Earth coastlines and a geo-located
Natural Earth down-sampled 1:50m cross-blended hypsometric tints raster with
shaded relief and water.

.. jupyter-execute::

   import geovista as gv
   from geovista.cache import natural_earth_hypsometric


   plotter = gv.GeoPlotter()
   plotter.add_base_layer(texture=natural_earth_hypsometric())
   plotter.add_coastlines(resolution="10m", color="white")
   plotter.show()

Render a base layer mesh again, but on a Mollweide projection.

Note that, ``geovista`` understands a ``cartopy`` CRS, thanks to ``cartopy`` v0.20+
inheriting from ``pyproj.CRS`` goodness.

In fact, ``geovista`` directly leverages the capability and benefits of ``pyproj``.
So what ``pyproj`` can do, ``geovista`` can do also 🚀🥳

.. jupyter-execute::

   from cartopy.crs import Mollweide
   import geovista as gv
   from geovista.cache import natural_earth_hypsometric


   plotter = gv.GeoPlotter(crs=Mollweide())
   plotter.add_base_layer(texture=natural_earth_hypsometric())
   plotter.view_xy()
   plotter.show()
