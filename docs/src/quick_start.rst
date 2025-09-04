.. include:: common.txt

.. _gv-quick-start:
.. _tippy-gv-quick-start:

:fa:`truck-fast` Quick Start
============================

Now that you've :ref:`installed <tippy-gv-installation>` ``geovista``, let's take a
quick tour to see some of the features and capabilities on offer.


Resources
---------

For convenience, ``geovista`` comes with numerous **pre-canned resources** to
help get you started on your visualization journey e.g., rasters, `VTK`_
meshes, `Natural Earth Features`_, and various Earth Science sample data.

``geovista`` will automatically download **versioned** resources on-the-fly,
as and when she needs them. However, if you want to download and cache all
``geovista`` resources to make them available offline, simply perform the
following on the command line:

.. code:: console

    $ geovista download --all


To view the manifest of registered resources:

.. code:: console

    $ geovsita download --list


.. note::
    :class: dropdown

    Want to know more?

    .. code:: console

        $ geovista download --help


Examples
--------

.. pyvista-plot::
   :context:
   :include-source: false
   :force_static:

   import pyvista
   pyvista.set_jupyter_backend('static')
   pyvista.global_theme.background = 'white'
   pyvista.global_theme.window_size = [400, 300]
   pyvista.global_theme.axes.show = False
   pyvista.global_theme.anti_aliasing = 'fxaa'


.. note::
  :class: margin, dropdown, toggle-shown

  The **Interactive Scene**
  `vtk.js <https://kitware.github.io/vtk-js/index.html>`_ backend does **not**
  support rendering text or points as spheres.


Let's explore some atmospheric and oceanographic model data using
``geovista``, which makes it easy to visualize **rectilinear**,
**curvilinear**, and **unstructured** meshes.


OISST AVHRR
^^^^^^^^^^^

This example renders a 2-D data array with 1-D X and Y **rectilinear**
coordinates as a :term:`mesh <Mesh>` of quadrilateral :term:`cells <Cell>` in
3-D with coastlines.

The data source is a `NOAA/NCEI Optimum Interpolation SST`_ (OISST) Advanced
Very High Resolution Radiometer (AVHRR)
:term:`rectilinear grid <Rectilinear Grid>` containing ``1,036,800``
quadrilateral cells and ``1,038,961`` :term:`points <Point>`.

The mesh is created from the bounds of 1-D geographic longitude and
latitude coordinates using the :meth:`~geovista.bridge.Transform.from_1d`
method. Each X and Y coordinate has 2 coordinate bounds describing
a quadrilateral cell.

A 2-D array of *Sea Surface Temperature* data located on the mesh cells
are rendered using the
:term:`perceptually uniform <Perceptually Uniform Colormap>`
`cmocean balance`_ diverging colormap, along with
`10m Natural Earth coastlines`_. Note that the land cells are masked.

.. pyvista-plot::
    :context:
    :optional:

    import geovista as gv
    from geovista.pantry.data import oisst_avhrr_sst

    # Load sample data.
    sample = oisst_avhrr_sst()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_1d(
        sample.lons,
        sample.lats,
        data=sample.data
    )

    # Plot the mesh with coastlines.
    p = gv.GeoPlotter()
    sargs = {"title": f"{sample.name} / {sample.units}"}
    p.add_mesh(
        mesh,
        cmap="balance",
        scalar_bar_args=sargs
    )
    p.add_coastlines(color="white")
    p.camera.zoom(1.2)
    p.show()


NEMO ORCA2
^^^^^^^^^^

This example renders a 2-D data array with 2-D X and Y **curvilinear**
coordinates as a :term:`mesh <Mesh>` of quadilateral :term:`cells <Cell>` in
3-D. A :term:`threshold <Threshold>` is applied to remove cells with masked
data. Coastlines and a :term:`base layer <Base Layer>` are also added before
the results are transformed to a flat 2-D surface with a `Plate Carrée`_
projection.

The data source is a `Nucleus for European Modelling of the Ocean`_ (NEMO)
ORCA2 global ocean tripolar :term:`curvilinear grid <Curvilinear Grid>`
containing ``26,640`` quadrilateral cells and ``106,560``
:term:`points <Point>`.

As the grid is curvilinear, it is created from the bounds of 2-D geographic
longitude and latitude coordinates using the
:meth:`~geovista.bridge.Transform.from_2d` method. Each X and Y
coordinate has 4 coordinate bounds describing a quadrilateral cell.

As ORCA2 is an ocean model, we use a `threshold`_ to remove ``10,209`` ``nan``
:term:`land mask <Land Mask>` cells , and :term:`texture map <Texture Map>`
a base layer underneath with a `1:50m Natural Earth I`_
raster.

A :term:`perceptually uniform <Perceptually Uniform Colormap>`
`cmocean thermal`_ colormap is used to render the *Sea Water Potential
Temperature* data located on the grid cells, which is then complemented with
`10m Natural Earth coastlines`_.

Finally, a `cartopy`_ :term:`CRS <Coordinate Reference System>`
is used to transform the :term:`actors <Actor>` in the scene to the
`Equidistant Cylindrical`_ (Plate Carrée`) conformal cylindrical
projection.

.. note::
    :class: dropdown

    Basic projection support is available within ``geovista`` for
    **Cylindrical** and **Pseudo-Cylindrical** projections. As ``geovista``
    matures, we'll aim to enrich that capability and complement it with
    other classes of projections, such as **Azimuthal** and **Conic**.


.. pyvista-plot::
    :context:
    :optional:

    import cartopy.crs as ccrs

    import geovista as gv
    from geovista.pantry.data import nemo_orca2

    # Load sample data.
    sample = nemo_orca2()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_2d(
        sample.lons,
        sample.lats,
        data=sample.data
    )

    # Remove cells from the mesh with NaN values.
    mesh = mesh.threshold()

    # Plot the mesh on a Plate Carrée projection using a cartopy CRS.
    p = gv.GeoPlotter(crs=ccrs.PlateCarree())
    sargs = {"title": f"{sample.name} / {sample.units}"}
    p.add_mesh(
        mesh,
        cmap="thermal",
        scalar_bar_args=sargs
    )
    p.add_base_layer(texture=gv.natural_earth_1())
    p.add_coastlines(color="white")
    p.view_xy()
    p.camera.zoom(1.4)
    p.show()


WAVEWATCH III
^^^^^^^^^^^^^

``geovista`` provides rich support for easily constructing a
:term:`mesh <Mesh>` surface from various unstructured Earth Science model
data.

To demonstrate this we create a `WAVEWATCH III`_ (WW3) unstructured
triangular mesh from 1-D X and Y **unstructured** coordinates and 2-D
:term:`connectivity <Connectivity>` using the
:meth:`~geovista.bridge.Transform.from_unstructured` method.

The ``sample.connectivity``, with shape ``(30559, 3)``, is used to index into
the ``16,160`` 1-D geographical longitude and latitude points to create a
mesh containing ``30,559`` triangular :term:`cells <Cell>`.

A 1-D array of *Sea Surface Wave Significant Height* data is located on
the mesh :term:`nodes <Node>`, which is then interpolated across the
mesh cells and rendered with the
:term:`perceptually uniform <Perceptually Uniform Colormap>`
`cmocean balance`_ divergent colormap.

As the WAVEWATCH III contains no land based cells, the
`1:50m Natural Earth Cross-Blended Hypsometric Tints`_
:term:`texture mapped <Texture Map>` :term:`base layer <Base Layer>` is
visible underneath without the need to `threshold`_ the mesh.

Finally, the render is decorated with `10m Natural Earth coastlines`_.

.. pyvista-plot::
    :context:
    :optional:

    import geovista as gv
    from geovista.pantry.data import ww3_global_tri

    # Load the sample data.
    sample = ww3_global_tri()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
    )

    # Plot the mesh.
    p = gv.GeoPlotter()
    sargs = {"title": f"{sample.name} / {sample.units}"}
    p.add_mesh(
        mesh,
        cmap="balance",
        scalar_bar_args=sargs
    )
    p.add_coastlines(color="white")
    p.add_base_layer(texture=gv.natural_earth_hypsometric())
    p.view_xy(negative=True)
    p.camera.zoom(1.2)
    p.show()


Finite Volume Community Ocean Model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This final example showcases how `PyVista`_ can take visualization of Earth
Science data to the next dimension, quite literally.

We use `Finite Volume Community Ocean Model`_ (FVCOM) data to create an
extruded :term:`mesh <Mesh>` of the `Plymouth Sound and Tamar River`_
bathymetry in Cornwall, England.

First the :meth:`~geovista.bridge.Transform.from_unstructured` method is used
to create a triangular mesh from 1-D X and Y **unstructured** coordinates and
2-D :term:`connectivity <Connectivity>`.

A 1-D array of *Sea Floor Depth Below Geoid* data is added to the mesh
:term:`cells <Cell>`, but also the mesh :term:`points <Point>`, which
are then used to displace the mesh points by a proportionally scaled amount
in the direction of the mesh surface normals.

This displacement or :term:`warping <Warp>` of the mesh reveals the relief of
the river and sea floor bathymetry, which we are then free to explore
interactively.

.. pyvista-plot::
    :context:
    :optional:

    import geovista as gv
    from geovista.pantry.data import fvcom_tamar

    # Load the sample data.
    sample = fvcom_tamar()

    # Create the mesh from the sample data.
    mesh = gv.Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.face,
        name="face",
    )

    # Warp the mesh nodes by the bathymetry.
    mesh.point_data["node"] = sample.node
    mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
    mesh.warp_by_scalar(scalars="node", inplace=True, factor=2e-5)

    # Plot the mesh.
    p = gv.GeoPlotter()
    sargs = {"title": f"{sample.name} / {sample.units}"}
    p.add_mesh(
        mesh,
        cmap="deep",
        scalar_bar_args=sargs
    )
    p.view_poi()
    p.show()


And Finally ...
---------------

Hopefully this whirlwind tour of ``geovista`` has whet your appetite for much
more!

If so, then let's explore the :ref:`next steps <tippy-gv-next-steps>` on your
``geovista`` journey.


.. comment

    Page link URL resources in alphabetical order:

.. _1:50m Natural Earth Cross-Blended Hypsometric Tints: https://www.naturalearthdata.com/downloads/50m-raster-data/50m-cross-blend-hypso/
.. _1:50m Natural Earth I: https://www.naturalearthdata.com/downloads/50m-raster-data/50m-natural-earth-1/
.. _10m Natural Earth coastlines: https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-coastline/
.. _ESRI spatial reference: https://spatialreference.org/ref/esri/54030/
.. _Equidistant Cylindrical: https://proj4.org/en/stable/operations/projections/eqc.html
.. _Finite Volume Community Ocean Model: https://www.fvcom.org/
.. _NASA Blue Marble: https://visibleearth.nasa.gov/collection/1484/blue-marble
.. _NOAA/NCEI Optimum Interpolation SST: https://www.ncei.noaa.gov/products/optimum-interpolation-sst
.. _Nucleus for European Modelling of the Ocean: https://forge.nemo-ocean.eu/nemo/nemo/-/wikis/home
.. _Plate Carrée: https://cartopy.readthedocs.io/stable/reference/projections.html#cartopy.crs.PlateCarree
.. _Plymouth Sound and Tamar River: https://www.google.com/maps/place/Plymouth+Sound/@50.3337382,-4.2215988,12z/data=!4m5!3m4!1s0x486c93516bbce307:0xded7654eaf4f8f83!8m2!3d50.3638359!4d-4.1441365
.. _Robinson: https://proj4.org/en/stable/operations/projections/robin.html
.. _WAVEWATCH III: https://github.com/NOAA-EMC/WW3
.. _threshold: https://docs.pyvista.org/api/core/_autosummary/pyvista.datasetfilters.threshold
