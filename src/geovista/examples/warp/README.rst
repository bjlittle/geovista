Warp Mesh
=========

These examples show how to make plots where an elevation offset is applied to
each mesh point -- i.e. the mesh has a visible "height" above the surface.

In ``pyvista``, applying an offset to each point is called a "warp".
In particular, the function :meth:`~pyvista.DataSetFilters.warp_by_scalar` is
used to displace each point by some amount in the direction of the mesh
surface normals.

.. note::
    The mesh normals must first be computed,
    using :meth:`~pyvista.PolyDataFilters.compute_normals`.

See `Computing Surface Normals <https://docs.pyvista.org/version/stable/examples/01-filter/compute-normals.htm>`_
for a fuller description of warping in general.

For a *cartographic* mesh, naturally, the surface normals give the upward
direction, and the warp is simply a vertical displacement.

The scalar warping array is often elevation data, usually with a scale factor
for emphasis.
:ref:`geotiff-elevation-example` is a good demonstration of this.
However, you can of course display any scalar mesh data as a relief in this way.
