.. include:: ../common.txt

.. _gv-developer-documentation:
.. _tippy-gv-developer-documentation:

:fa:`square-pen` Documentation
==============================

Here we provide some high-level guidelines and best practice advice for authors and
contributors wishing to build and render the documentation.

.. _gv-developer-documentation-building:
.. _tippy-gv-developer-documentation-building:

:fa:`screwdriver-wrench` Building
---------------------------------

The documentation is built using `sphinx`_ to parse and render `reStructuredText`_
(``rst``) documents into ``HTML``.

We also use `myst-parser`_, a ``sphinx`` and `docutils`_ extension to parse and convert
:term:`MyST` to ``rst``, and `myst-nb`_ to execute and convert
`Jupyter Notebooks`_ into ``sphinx`` documents.

.. seealso::
    :class: margin, dropdown, toggle-shown

    For configuration details see ``Makefile`` and ``conf.py``.

The documentation is built using `sphinx-build`_ and the `GNU make`_ tool from within
the ``docs`` directory e.g.,

.. code:: console

    $ cd docs
    $ make <make-task>

The following sections describe the ``make`` tasks that are available.


:fa:`pump-medical` Hygiene
~~~~~~~~~~~~~~~~~~~~~~~~~~

Start afresh with confidence by performing documentation hygiene to purge various build artifacts.

.. table:: Housekeeping Tasks
    :widths: 1 3
    :align: center

    +-------------------------+----------------------------------------------------------------------------------+
    | Make Task               | Description                                                                      |
    +=========================+==================================================================================+
    | :guilabel:`clean`       | Purge all `sphinx-autoapi`_, `sphinx-gallery`_, `sphinx-tags`_, carousel, and    |
    |                         | other `sphinx-build`_ artifacts.                                                 |
    +-------------------------+----------------------------------------------------------------------------------+
    | :guilabel:`clean-all`   | Perform both a ``clean`` and ``clean-cache``.                                    |
    +-------------------------+----------------------------------------------------------------------------------+
    | :guilabel:`clean-cache` | Purge the `myst-nb`_ Jupyter cache. See `myst-nb configuration`_                 |
    |                         | for further details.                                                             |
    +-------------------------+----------------------------------------------------------------------------------+


:fa:`pen-to-square` Build
~~~~~~~~~~~~~~~~~~~~~~~~~

Build the documentation along with various controls to limit image creation. Note that building the documentation
static images and interactive scenes can be resource hungry and time consuming.

.. table:: Build Tasks
    :widths: 1 3
    :align: center

    +----------------------------+-------------------------------------------------------------------------+
    | Make Task                  | Description                                                             |
    +============================+=========================================================================+
    | :guilabel:`html`           | Build the full suite of documentation including all images and scenes.  |
    +----------------------------+-------------------------------------------------------------------------+
    | :guilabel:`html-docstring` | Build the full suite of documentation and only the ``docstring`` images |
    |                            | and scenes.                                                             |
    +----------------------------+-------------------------------------------------------------------------+
    | :guilabel:`html-gallery`   | Build the full suite of documentation and only the `sphinx-gallery`_    |
    |                            | images and scenes, which also includes the carousel.                    |
    +----------------------------+-------------------------------------------------------------------------+
    | :guilabel:`html-inline`    | Build the full suite of documentation and only inline documentation     |
    |                            | images and scenes.                                                      |
    +----------------------------+-------------------------------------------------------------------------+
    | :guilabel:`html-noplot`    | Build the full suite of documentation with no static images and no      |
    |                            | interactive scenes.                                                     |
    +----------------------------+-------------------------------------------------------------------------+
    | :guilabel:`html-tutorial`  | Build the full suite of documentation and only the tutorial notebooks.  |
    +----------------------------+-------------------------------------------------------------------------+


:fab:`readme` Render
~~~~~~~~~~~~~~~~~~~~

How-to serve the rendered documentation for inspection in a local browser.

.. table:: Render Tasks
    :widths: 1 3
    :align: center

    +------------------------+-------------------------------------------------------------------------------------+
    | Make Task              | Description                                                                         |
    +========================+=====================================================================================+
    | :guilabel:`serve-html` | Start a local ``HTTP`` server on port ``11000`` to view the rendered documentation. |
    |                        | This is necessary in order to support interactive scenes.                           |
    +------------------------+-------------------------------------------------------------------------------------+


:fa:`vial-circle-check` Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Perform documentation quality assurance.

.. table:: Test Tasks
    :widths: 1 3
    :align: center

    +-----------------------+----------------------------------------------------------------------------------+
    | Make Task             | Description                                                                      |
    +=======================+==================================================================================+
    | :guilabel:`doctest`   | Execute `sphinx.ext.doctest`_ to test code snippets within the documentation.    |
    +-----------------------+----------------------------------------------------------------------------------+


.. _gv-developer-documentation-branding:
.. _tippy-gv-developer-documentation-branding:

:fa:`heart-circle-check` Branding
---------------------------------

Our icons are provided by `Font Awesome`_. Font Awesome (Free) is licensed under the
`Creative Commons Attribution 4.0 International License`_ (CC BY 4.0).

Static icon assets are located in the ``docs/src/_static/images/icons`` directory,
along with the Font Awesome ``LICENSE.txt`` file. Refer to the ``docs/src/conf.py``
for asset configuration details.

Other branding assets are available from the `geovista-media`_ repository.

The branding RGB colour is ``#80d050``.


:fa:`pencil` Logo Font
~~~~~~~~~~~~~~~~~~~~~~

.. figure:: ../_static/geovista-title.svg
    :align: center
    :alt: GeoVista Logo Title
    :width: 25%

    GeoVista Logo Title

The ``geovista`` logo title is rendered using the `La Machine Company`_ TrueType font.


:fab:`github` Continuous Integration
------------------------------------

.. |ci-docs| image:: https://github.com/bjlittle/geovista/actions/workflows/ci-docs.yml/badge.svg
    :target: https://github.com/bjlittle/geovista/actions/workflows/ci-docs.yml
.. |rtd| image:: https://readthedocs.org/projects/geovista/badge/?version=latest
    :target: https://geovista.readthedocs.io/en/latest/?badge=latest

The following documentation workflows are available:

.. table:: Documentation Workflows
    :widths: 1 2
    :align: center

    +-----------+----------------------------------------------------------------------------------+
    | Workflow  | Description                                                                      |
    +===========+==================================================================================+
    | |ci-docs| | The `ci-docs.yml`_ :term:`GHA workflow <GHA>` executes `sphinx.ext.doctest`_ to  |
    |           | test code snippets within the documentation.                                     |
    |           |                                                                                  |
    |           | Also see the documentation :ref:`tippy-gv-developer-documentation-pixi-workflow` |
    |           | :guilabel:`doctest` task.                                                        |
    +-----------+----------------------------------------------------------------------------------+
    | |rtd|     | The `.readthedocs.yml`_ workflow builds and publishes our documentation on the   |
    |           | `ReadtheDocs`_ (RTD) platform.                                                   |
    |           |                                                                                  |
    |           | See the `Versions`_ section for each ``tag`` release of the documentation hosted |
    |           | on RTD along with the :guilabel:`latest` render of the ``main`` branch, and a    |
    |           | :guilabel:`stable` render of the latest ``tag`` release.                         |
    |           |                                                                                  |
    |           | Refer to the `Builds`_ section for a render of the documentation for each        |
    |           | ``pull-request``.                                                                |
    +-----------+----------------------------------------------------------------------------------+


.. _gv-developer-documentation-copyright-and-license:
.. _tippy-gv-developer-documentation-copyright-and-license:

:fa:`file-contract` Copyright & License
---------------------------------------

Source code must contain the following copyright and license preamble at the top of the file:

.. code::

    # Copyright (c) 2021, GeoVista Contributors.
    #
    # This file is part of GeoVista and is distributed under the 3-Clause BSD license.
    # See the LICENSE file in the package root directory for licensing details.

Quality assurance of preamble compliance is provided by the `ruff`_ preview rule
`CPY001`_ (``flake8-copyright``).

Configuration of this `single preview rule`_ is defined in the ``pyproject.toml`` file.
For further details refer to the following TOML tables:

* ``[tool.ruff.lint]``
* ``[tool.ruff.lint.flake8-copyright]``
* ``[tool.ruff.lint.per-file-ignores]``


.. _gv-developer-documentation-cross-references:
.. _tippy-gv-developer-documentation-cross-references:

:fa:`up-right-from-square` Cross-References
-------------------------------------------

Arbitrary locations are cross-referenced using ``reStructuredText`` labels and the ``sphinx``
`:ref: <https://www.sphinx-doc.org/en/master/usage/referencing.html#cross-referencing-arbitrary-locations>`__
role.

For consistency, the following structure is recommended for our labels:

- A label should be prefixed with ``gv-`` to indicate inclusion within the
  ``geovista`` namespace.
- The ``gv-`` prefix should then be followed by the name of the file
  containing the label, with hyphens replacing spaces and special characters,
  and all characters in lower case e.g., ``gv-next-steps`` for the
  ``docs/src/next_steps.rst`` document. Include the sub-directory structure in
  the label if the file is not in the ``docs/src`` root directory, e.g.,
  ``gv-developer-towncrier`` for the ``docs/src/developer/towncrier.rst``
  document.
- If appropriate, the label should then be followed by the title of the section
  or subsection it's referencing, with hyphens replacing spaces and special
  characters, and all characters in lower case e.g.,
  ``gv-developer-documentation-cross-references`` for the
  :ref:`gv-developer-documentation-cross-references` section in this
  ``docs/src/developer/documentation.rst`` document. If the label doesn't proceed
  a section or subsection title, then use a suitable description that is concise
  and uniquely identifies the location within the document. Avoid using
  abbreviations or acronyms unless strictly necessary.

.. tip::
    :class: dropdown, toggle-shown

    A label prefixed with ``tippy-gv-`` instead of ``gv-`` will have a
    `sphinx-tippy`_ tooltip rendered for each of its cross-reference links e.g.,
    hover over this
    :ref:`tippy-gv-developer-documentation-cross-references` tooltip enabled link
    :fa:`arrow-pointer`:fa:`computer-mouse`

A top-level label **must** be present on the **first line** of a document.

An `include directive`_ may be used on the first line of a document providing
convenient access to common project references e.g.,

.. code:: rst

    .. include:: common.txt

Where the ``common.txt`` file is located in the ``docs/src`` root directory.

Otherwise, the top-level label **must** follow the `include directive`_ e.g., the
``docs/src/developer/documentation.rst`` document has the following preamble:

.. code:: rst

    .. include:: ../common.txt

    .. _gv-developer-documentation:
    .. _tippy-gv-developer-documentation:

    :fa:`square-pen` Documentation
    ==============================


.. _gv-developer-documentation-pixi-workflow:
.. _tippy-gv-developer-documentation-pixi-workflow:

:fa:`share-nodes` Pixi Workflow
-------------------------------

The documentation may be built and rendered using `pixi run <https://pixi.sh/latest/reference/cli/pixi/run>`__
tasks, all of which do not require to be executed within the ``docs`` directory, unlike the above
:ref:`tippy-gv-developer-documentation-building` ``make`` tasks e.g.,

.. code:: console

    $ pixi run <pixi-task>

.. table:: Pixi Tasks
    :widths: 1 3
    :align: center
    :name: documentation-pixi-workflow

    +-------------------------+----------------------------------------------------------------------------------+
    | Pixi Task               | Description                                                                      |
    +=========================+==================================================================================+
    | :guilabel:`clean`       | Purge all `sphinx-autoapi`_, `sphinx-gallery`_, `sphinx-tags`_, carousel, and    |
    |                         | other `sphinx-build`_ artifacts.                                                 |
    +-------------------------+----------------------------------------------------------------------------------+
    | :guilabel:`clean-all`   | Perform both a ``clean`` and ``clean-cache`` tasks.                              |
    +-------------------------+----------------------------------------------------------------------------------+
    | :guilabel:`clean-cache` | Purge the `myst-nb`_ Jupyter cache. See `myst-nb configuration`_                 |
    |                         | for further details.                                                             |
    +-------------------------+----------------------------------------------------------------------------------+
    | :guilabel:`doctest`     | Execute `sphinx.ext.doctest`_ to test code snippets within the documentation.    |
    |                         | Note that the ``clean`` task is called prior to running this task.               |
    +-------------------------+----------------------------------------------------------------------------------+
    | :guilabel:`make`        | Build the documentation using ``html-noplot`` by default. Pass either ``html``,  |
    |                         | ``html-docstring``, ``html-gallery``, ``html-inline`` or ``html-tutorial`` as an |
    |                         | argument to override the default ``html-noplot`` behaviour. Note that the        |
    |                         | ``clean`` task is called prior to running this task.                             |
    +-------------------------+----------------------------------------------------------------------------------+
    | :guilabel:`serve-html`  | Build the documentation using ``html-noplot`` by default and start a local       |
    |                         | ``HTTP`` server on port ``11000`` to view the rendered documentation. This is    |
    |                         | necessary in order to support interactive scenes. Pass either ``html``,          |
    |                         | ``html-docstring``, ``html-gallery``, ``html-inline`` or ``html-tutorial`` as an |
    |                         | argument to override the default ``html-noplot`` behaviour. Note that the        |
    |                         | ``clean`` and ``make`` tasks are called prior to running this task.              |
    +-------------------------+----------------------------------------------------------------------------------+

.. tip::
    :class: dropdown, toggle-shown

    Apply the ``--frozen`` option to avoid `pixi`_ checking and updating the ``pixi.lock`` file.

    e.g., To only build the ``Gallery`` examples and serve the rendered documentation:

    .. code:: console

        $ pixi run --frozen serve-html html-gallery


.. _gv-developer-documentation-tagging:
.. _tippy-gv-developer-documentation-tagging:

:fa:`tags` Tagging
------------------

.. note::
  :class: margin, dropdown, toggle-shown

  Tags are configured in the ``docs/src/conf.py`` file.

Themed content :ref:`tippy-gv-tagoverview` are supported using `sphinx-tags`_.

Tags provide a simple and intuitive way to group and filter content, improving
discoverability and browsing. This allows users to easily explore or quickly
find related topics and content.

:ref:`Gallery Examples <tippy-gv-examples>` must contain one or more content
tags using the ``tags`` directive to highlight noteworthy topics demonstrated
within the example e.g.,

.. code:: rst

    .. tags::

        component: manifold, filter: contour

A tag consists of a lower-case ``category: topic`` pair, where:

* ``category`` is a domain area of interest,
* ``topic`` is a specific subject within that domain, and
* a colon (``:``) separates each of the above tag components

Single word tags are preferred. However, consider using a hyphen (``-``) to
separate a multi-word ``category`` or ``topic`` within a tag e.g.,
``data-type: point-cloud``.

Endeavour to group tags of the same ``category`` on the same line, ordered
alphabetically by ``topic``. Note that multiple tags must be separated by a
comma (``,``).

Tags may span multiple contiguous lines, ordered alphabetically by ``category``
e.g.,

.. code:: rst

    .. tags::

        component: coastlines, component: manifold, component: texture,
        filter: threshold,
        render: camera, render: subplots,
        sample: unstructured,
        style: opacity

.. table:: Content Tags
    :widths: 1 2 2
    :align: center

    +------------------------+----------------------------------------------------+------------------------------------------------+
    | Category               | Topic                                              | Description                                    |
    +========================+====================================================+================================================+
    | :guilabel:`component`  | ``coastlines``, ``graticule``, ``manifold``,       | Content that demonstrates the use of a         |
    |                        | ``texture``, ``vectors``                           | specific feature.                              |
    +------------------------+----------------------------------------------------+------------------------------------------------+
    | :guilabel:`domain`     | ``oceanography``, ``seismology``, ``meteorology``, | Content that is relevant to a specific         |
    |                        | ``orography``                                      | scientific domain or discipline.               |
    +------------------------+----------------------------------------------------+------------------------------------------------+
    | :guilabel:`filter`     | ``cast``, ``contour``, ``extrude``, ``threshold``, | Content that demonstrates the use of           |
    |                        | ``triangulate``, ``warp``                          | specific `filtering`_ techniques.              |
    +------------------------+----------------------------------------------------+------------------------------------------------+
    | :guilabel:`load`       | ``curvilinear``, ``geotiff``, ``points``,          | Demonstrates use of the :mod:`geovista.bridge` |
    |                        | ``rectilinear``, ``unstructured``                  | to load various types of geospatial data.      |
    +------------------------+----------------------------------------------------+------------------------------------------------+
    | :guilabel:`plot`       | ``camera``, ``subplots``                           | Content that showcases various `plotting`_     |
    |                        |                                                    | techniques.                                    |
    +------------------------+----------------------------------------------------+------------------------------------------------+
    | :guilabel:`projection` | ``crs``, ``transform``                             | Content that demonstrates the use of           |
    |                        |                                                    | geospatial projections or transformations.     |
    +------------------------+----------------------------------------------------+------------------------------------------------+
    | :guilabel:`resolution` | ``high``                                           | Content using high-resolution or high-volume   |
    |                        |                                                    | geospatial data.                               |
    +------------------------+----------------------------------------------------+------------------------------------------------+
    | :guilabel:`sample`     | ``curvilinear``, ``geotiff``, ``points``,          | Content that leverages the convenience of      |
    |                        | ``rectilinear``, ``unstructured``                  | pre-canned geospatial sample data available    |
    |                        |                                                    | from the :mod:`geovista.pantry`.               |
    +------------------------+----------------------------------------------------+------------------------------------------------+
    | :guilabel:`style`      | ``colormap``, ``lighting``, ``opacity``,           | Content that includes customization of         |
    |                        | ``shading``                                        | various render styles and aesthetics.          |
    +------------------------+----------------------------------------------------+------------------------------------------------+
    | :guilabel:`widget`     | ``checkbox``, ``logo``                             | Content that demonstrates the use of           |
    |                        |                                                    | interactive `widgets`_.                        |
    +------------------------+----------------------------------------------------+------------------------------------------------+


.. comment

    Page link URL resources in alphabetical order:


.. _Builds: https://app.readthedocs.org/projects/geovista/builds/
.. _CPY001: https://docs.astral.sh/ruff/rules/missing-copyright-notice/
.. _Creative Commons Attribution 4.0 International License: https://creativecommons.org/licenses/by/4.0/
.. _Font Awesome: https://fontawesome.com/
.. _GNU make: https://www.gnu.org/software/make/
.. _Jupyter Notebooks: https://jupyter.org/
.. _La Machine Company: https://www.dafont.com/la-machine-company.font
.. _ReadtheDocs: https://app.readthedocs.org/projects/geovista/
.. _Versions: https://app.readthedocs.org/projects/geovista/
.. _ci-docs.yml: https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-docs.yml
.. _filtering: https://docs.pyvista.org/examples/01-filter/
.. _include directive: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#include-directive
.. _myst-nb configuration: https://myst-nb.readthedocs.io/en/latest/configuration.html
.. _plotting: https://docs.pyvista.org/examples/02-plot/#
.. _.readthedocs.yml: https://github.com/bjlittle/geovista/blob/main/.readthedocs.yml
.. _single preview rule: https://docs.astral.sh/ruff/preview/#selecting-single-preview-rules
.. _sphinx linkcheck builder: https://www.sphinx-doc.org/en/master/usage/builders/index.html#sphinx.builders.linkcheck.CheckExternalLinksBuilder
.. _widgets: https://docs.pyvista.org/examples/03-widgets/
