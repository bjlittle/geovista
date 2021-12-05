.. geovista documentation master file, created by
   sphinx-quickstart on Sun Dec  5 00:40:32 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to GeoVista's documentation!
====================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. jupyter-execute::
    :hide-code:

    # configuration for pythreejs
    import pyvista
    pyvista.set_jupyter_backend("pythreejs")
    pyvista.global_theme.background = "white"
    pyvista.global_theme.window_size = [700, 500]
    pyvista.global_theme.axes.show = False
    #pyvista.global_theme.smooth_shading = True
    pyvista.global_theme.antialiasing = True

.. jupyter-execute::

    import numpy as np
    import geovista as gv

    M, N = 45, 90
    lats = np.linspace(-90, 90, M + 1)
    lons = np.linspace(-180, 180, N + 1)
    data = np.random.uniform(low=250, high=303, size=M * N)

    mesh = gv.Transform.from_1d(lons, lats, data=data, name="synthetic")

    plotter = gv.GeoPlotter()
    plotter.add_mesh(mesh, cmap='balance', show_edges=True)
    plotter.add_coastlines(resolution="10m", color="white")
    plotter.show()


