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
    | :guilabel:`doctest`   | Execute `sphinx.ext.doctest`_ to test snippets within the documentation.         |
    +-----------------------+----------------------------------------------------------------------------------+


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


.. comment

    Page link URL resources in alphabetical order:


.. _GNU make: https://www.gnu.org/software/make/
.. _Jupyter Notebooks: https://jupyter.org/
.. _myst-nb configuration: https://myst-nb.readthedocs.io/en/latest/configuration.html
.. _sphinx linkcheck builder: https://www.sphinx-doc.org/en/master/usage/builders/index.html#sphinx.builders.linkcheck.CheckExternalLinksBuilder
.. _include directive: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#include-directive
