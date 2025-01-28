.. include:: ../common.txt

.. _gv-developer-documentation:

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

The documentation is built using `sphinx-build`_ and the `GNU make`_ tool.


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
    :widths: 2 1 3
    :align: center

    +----------------------------+---------------------+--------------------------------------------------------------+
    | Make Command               | Status              | Description                                                  |
    +============================+=====================+==============================================================+
    | :guilabel:`html`           | :fas:`square-check` | Build the full suite of documentation including all images   |
    |                            |                     | and scenes.                                                  |
    +----------------------------+---------------------+--------------------------------------------------------------+
    | :guilabel:`html-docstring` | :fas:`square-check` | Build the full suite of documentation and only the           |
    |                            |                     | ``docstring`` images and scenes.                             |
    +----------------------------+---------------------+--------------------------------------------------------------+
    | :guilabel:`html-gallery`   | :fas:`square-check` | Build the full suite of documentation and only the           |
    |                            |                     | `sphinx-gallery`_ images and scenes, which also includes the |
    |                            |                     | carousel.                                                    |
    +----------------------------+---------------------+--------------------------------------------------------------+
    | :guilabel:`html-inline`    | :fas:`square-xmark` | Build the full suite of documentation and only inline        |
    |                            |                     | documentation images and scenes. See :far:`circle-dot`       |
    |                            |                     | :issue:`1150`.                                               |
    +----------------------------+---------------------+--------------------------------------------------------------+
    | :guilabel:`html-noplot`    | :fas:`square-check` | Build the full suite of documentation with no static images  |
    |                            |                     | and no interactive scenes.                                   |
    +----------------------------+---------------------+--------------------------------------------------------------+
    | :guilabel:`html-tutorial`  | :fas:`square-check` | Build the full suite of documentation and only the tutorial  |
    |                            |                     | notebooks.                                                   |
    +----------------------------+---------------------+--------------------------------------------------------------+


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
    | :guilabel:`linkcheck` | Check the integrity of all external links referenced within the documentation    |
    |                       | using the `sphinx linkcheck builder`_.                                           |
    +-----------------------+----------------------------------------------------------------------------------+


.. comment

    Page link URL resources in alphabetical order:


.. _GNU make: https://www.gnu.org/software/make/
.. _Jupyter Notebooks: https://jupyter.org/
.. _myst-nb configuration: https://myst-nb.readthedocs.io/en/latest/configuration.html
.. _sphinx linkcheck builder: https://www.sphinx-doc.org/en/master/usage/builders/index.html#sphinx.builders.linkcheck.CheckExternalLinksBuilder
