.. title:: GeoVista

.. jupyter-execute::
   :hide-code:

   # configure pyvista for pythreejs
   import pyvista
   pyvista.set_jupyter_backend("pythreejs")
   pyvista.global_theme.background = "white"
   pyvista.global_theme.window_size = [700, 500]
   pyvista.global_theme.axes.show = True
   #pyvista.global_theme.anti_aliasing = "fxaa"


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

In the meantime, here's an interactive ``geovista`` amuse-bouche to whet your appetite...

.. jupyter-execute::

   import geovista as gv
   from geovista.pantry import lfric_sst


   # Load the Met Office LFRic C48 unstructured cube-sphere sample data.
   sample = lfric_sst()

   # Create the mesh from the sample data.
   mesh = gv.Transform.from_unstructured(
       sample.lons,
       sample.lats,
       connectivity=sample.connectivity,
       data=sample.data,
   )

   # Plot the mesh.
   plotter = gv.GeoPlotter()
   sargs = dict(title=f"{sample.name} / {sample.units}")
   plotter.add_mesh(mesh, scalar_bar_args=sargs, cmap="balance", show_edges=True)
   plotter.add_coastlines(resolution="10m", color="white")
   plotter.add_axes()
   plotter.show()
