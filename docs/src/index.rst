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

In the meantime, here's an interactive ``geovista`` amuse-bouche to whet your appetite...

.. jupyter-execute::

   import geovista as gv
   from geovista.samples import ww3_gbl_tri_hs

   # Load the WAVEWATCH III (WW3) global unstructured triangular sample data.
   sample = ww3_gbl_tri_hs()

   # Create the mesh from the sample data.
   mesh = gv.Transform.from_unstructured(
       sample.lons, sample.lats, sample.connectivity, data=sample.data
   )

   # Plot the mesh.
   plotter = gv.GeoPlotter()
   plotter.add_mesh(mesh, cmap="balance", show_edges=True)
   plotter.add_base_layer(texture=gv.natural_earth_hypsometric(), zlevel=-5)
   plotter.add_coastlines(resolution="10m", color="white")
   plotter.show()
