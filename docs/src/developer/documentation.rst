.. include:: ../common.txt

.. _gv-developer-documentation:
.. _tippy-gv-developer-documentation:

:fa:`square-pen` Documentation
==============================

Here we provide some high-level guidelines and best practice advice for authors and
contributors wishing to build and render the documentation.


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
the ``docs`` directory.


:fa:`pump-medical` Hygiene
~~~~~~~~~~~~~~~~~~~~~~~~~~

Start afresh by performing documentation hygiene to purge various build artifacts.

.. table:: Housekeeping Commands
    :widths: 1 3
    :align: center

    +-------------------------+----------------------------------------------------------------------------------+
    | Make Command            | Description                                                                      |
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

.. table:: Build Commands
    :widths: 1 3
    :align: center

    +----------------------------+-------------------------------------------------------------------------+
    | Make Command               | Description                                                             |
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

.. table:: Render Commands
    :widths: 1 3
    :align: center

    +------------------------+-------------------------------------------------------------------------------------+
    | Make Command           | Description                                                                         |
    +========================+=====================================================================================+
    | :guilabel:`serve-html` | Start a local ``HTTP`` server on port ``11000`` to view the rendered documentation. |
    |                        | This is necessary in order to support interactive scenes.                           |
    +------------------------+-------------------------------------------------------------------------------------+


:fa:`vial-circle-check` Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Perform documentation quality assurance.

.. table:: Test Commands
    :widths: 1 3
    :align: center

    +-----------------------+----------------------------------------------------------------------------------+
    | Make Command          | Description                                                                      |
    +=======================+==================================================================================+
    | :guilabel:`doctest`   | Execute `sphinx.ext.doctest`_ to test snippets within the documentation.         |
    +-----------------------+----------------------------------------------------------------------------------+


.. _gv-developer-documentation-pixi-workflow:
.. _tippy-gv-developer-documentation-pixi-workflow:

:fa:`share-nodes` Pixi Workflow
-------------------------------

The documentation may be built and rendered using the following ``docs`` feature
`pixi run <https://pixi.sh/latest/reference/cli/pixi/run>`__ tasks, all of which do not require to be run within
the ``docs`` directory, unlike the above ``make`` commands.

.. table:: Pixi Commands
    :widths: 1 3
    :align: center

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
    | :guilabel:`doctest`     | Execute `sphinx.ext.doctest`_ to test snippets within the documentation. Note    |
    |                         | that the ``clean`` task is called prior to running this task.                    |
    +-------------------------+----------------------------------------------------------------------------------+
    | :guilabel:`make`        | Build the documentation using ``html-noplot`` by default. Pass either ``html``,  |
    |                         | ``html-docstring``, ``html-gallery``, ``html-inline`` or ``html-tutorial`` as an |
    |                         | argument to override the default behaviour. Note that the ``clean`` task is      |
    |                         | called prior to running this task.                                               |
    +-------------------------+----------------------------------------------------------------------------------+
    | :guilabel:`serve-html`  | Build the documentation using ``html-noplot`` by default and start a local       |
    |                         | ``HTTP`` server on port ``11000`` to view the rendered documentation. This is    |
    |                         | necessary in order to support interactive scenes. Pass either ``html``,          |
    |                         | ``html-docstring``, ``html-gallery``, ``html-inline`` or ``html-tutorial`` as an |
    |                         | argument to override the default behaviour. Note that the ``clean`` and ``make`` |
    |                         | tasks are called prior to running this task.                                     |
    +-------------------------+----------------------------------------------------------------------------------+

.. note::
    :class: dropdown

    Alternatively, apply the ``--frozen`` option to avoid `pixi`_ checking and updating the ``pixi.lock`` file.

    For example, to build and only render the Examples Gallery:

    .. code:: console

        $ pixi run --frozen serve-html html-gallery


.. comment

    Page link URL resources in alphabetical order:


.. _GNU make: https://www.gnu.org/software/make/
.. _Jupyter Notebooks: https://jupyter.org/
.. _myst-nb configuration: https://myst-nb.readthedocs.io/en/latest/configuration.html
.. _sphinx linkcheck builder: https://www.sphinx-doc.org/en/master/usage/builders/index.html#sphinx.builders.linkcheck.CheckExternalLinksBuilder
