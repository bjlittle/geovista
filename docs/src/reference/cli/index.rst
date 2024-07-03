.. _gv-cli:

:fa:`terminal` CLI
==================

Once ``geovista`` has been :ref:`installed <gv-installation>`, a
:ref:`console script <gv-cli-geovista>` [#]_ will be available with
several convenience commands to assist with the management of ``geovista``
and its resources.


.. _gv-cli-geovista:

.. click:: geovista.cli:main
    :prog: geovista
    :nested: none



Commands
--------

The following :ref:`geovista console script <gv-cli-geovista>` commands are
available:

.. toctree::

    download
    examples
    plot


.. comment

    Page link URL resources in alphabetical order:

.. [#] See `entry-points`_ for further information.

.. _entry-points: https://setuptools.pypa.io/en/latest/userguide/entry_point.html
