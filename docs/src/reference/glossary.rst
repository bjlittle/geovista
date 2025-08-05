.. include:: ../common.txt

.. _gv-reference-glossary:
.. _tippy-gv-reference-glossary:

:fa:`spell-check` Glossary
==========================

Say what you mean. Mean what you say.


.. glossary::

    Actor
        Represents an object (geometry and properties) in a rendered scene.
        See `vtkActor`_.

    Base Layer
        A surface mesh that may be texture mapped, and lies beneath another
        mesh typically to fill holes in that mesh.

    Cell
        A cell is the geometry between points that defines the connectivity
        or topology of a mesh. See `What is a Cell?`_

    Connectivity
        An array of offsets that index into an array of points to define how
        cells are constructed from those points.

    Coordinate Reference System
        A Coordinate Reference System defines how your geo-referenced spatial
        data relates to real locations on the Earth’s surface. Abbreviated to
        CRS.

    Curvilinear Grid
        For example, a qudrilateral-cell surface that can be created from an
        array of 2-D ``x`` and ``y`` spatial points.

    Environment
        A `pixi environment`_ is a collection of one or more
        :term:`features <Feature>` that encapsulate its dependencies,
        configurations and tasks. Environments can be installed and
        activated to run :term:`tasks <Task>`. Our environments are
        defined under the ``[tool.pixi.environments]`` table in the
        ``pyproject.toml`` manifest file. See these `design considerations`_
        for further details.

    Face
        A polygonal cell in a mesh geometry. Also see :term:`Cell`.

    Feature
        A `pixi feature`_ defines part of an
        :term:`environment <Environment>` and may contain ``dependencies``,
        ``platforms``, ``channels``, ``tasks`` and various other configurations.
        Our features are defined under ``[tools.pixi.feature.<feature-name>.*]``
        tables in the ``pyproject.toml`` manifest file. See these
        `design considerations`_ for further details.

    Land Mask
        Typically a boolean array used to indicate the cells in a mesh that
        represent land.

    Manifold
        A water-tight, closed geometric structure e.g., a sphere.

    Mesh
        A spatially referenced dataset that may be a surface or volume in 3-D
        space. See `What is a Mesh?`_

    MyST
        *Markedly Structured Text* is a rich and extensible flavour of ``Markdown``
        for authoring technical and scientific documents. See `myst-nb`_ and
        `myst-parser`_ from the `Executable Books`_ organisation.

    Node
        Nodes are the vertices of a mesh. Also see :term:`Point`.

    Perceptually Uniform Colormap
        A colormap in which equal steps in data are perceived as equal steps
        in the color space.

    Point
        Points are the vertices of the mesh, also referred to as the Cartesian
        coordinates of the underlying structure. See `What is a Point?`_

    Rectilinear Grid
        For example, a quadrilateral-cell surface that can be created from an
        array of 1-D ``x`` and ``y`` spatial points.

    Sea Mask
        Typically a boolean array used to indicate the cells in a mesh that
        represent water e.g., river, lake, sea, ocean.

    Task
        A `pixi task`_ is defined as part of a :term:`feature <Feature>`
        to perform a cross-platform workflow command within an
        :term:`environment <Environment>`. Tasks are defined under the
        ``[tool.pixi.feature.<feature-name>.tasks.<task-name>]`` table in the
        ``pyproject.toml`` manifest file. See the `tasks documentation`_.
        for further details.

    Texture Map
        A graphical technique where a raster image is wrapped over the
        surface of a geometric object.

    Threshold
        To remove the cells from a mesh based on criteria of data associated
        with the mesh cells or points. See `PyVista threshold`_.

    Unstructured Mesh
        A surface that is created from a geometry of points and a topology of
        indices that define how cells are constructed from those points. See
        :term:`Connectivity`.

    Warp
        Extrude the points in a mesh by a proportional amount along the
        surface normals. See `PyVista warp_by_scalar`_.


.. comment

    Page link URL resources in alphabetical order:


.. _PyVista threshold: https://docs.pyvista.org/api/core/_autosummary/pyvista.datasetfilters.threshold
.. _PyVista warp_by_scalar: https://docs.pyvista.org/api/core/_autosummary/pyvista.datasetfilters.warp_by_scalar
.. _What is a Cell?: https://docs.pyvista.org/user-guide/what-is-a-mesh.html#what-is-a-cell
.. _What is a Point?: https://docs.pyvista.org/user-guide/what-is-a-mesh.html#what-is-a-point
.. _What is a Mesh?: https://docs.pyvista.org/user-guide/what-is-a-mesh.html#what-is-a-mesh
.. _design considerations: https://pixi.sh/latest/workspace/multi_environment/#design-considerations
.. _pixi environment: https://pixi.sh/latest/reference/pixi_manifest/#the-environments-table
.. _pixi feature: https://pixi.sh/latest/reference/pixi_manifest/#the-feature-table
.. _pixi task: https://pixi.sh/latest/reference/pixi_manifest/#the-tasks-table
.. _tasks documentation: https://pixi.sh/latest/workspace/advanced_tasks/
.. _vtkActor: https://vtk.org/doc/nightly/html/classvtkActor.html#details
