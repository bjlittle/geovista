.. _gv-reference-cli:

:fa:`code` CLI
==============

Once ``geovista`` has been :ref:`installed <gv-installation>`, a
:ref:`console script <gv-reference-cli-geovista>` [#]_ will be available with
several convenience commands to assist with the management of ``geovista``
and its resources.


.. _gv-reference-cli-geovista:

.. click:: geovista.cli:main
    :prog: geovista
    :nested: none



Commands
--------

The following :ref:`geovista console script <gv-reference-cli-geovista>` commands are
available:

.. toctree::

    download
    examples
    plot


.. comment

    Page link URL resources in alphabetical order:

.. [#] See `entry-points`_ for further information.

.. _entry-points: https://setuptools.pypa.io/en/latest/userguide/entry_point.html
