.. _gv-reference-cli:
.. _tippy-gv-reference-cli:

:fa:`code` CLI
==============

Once ``geovista`` has been :ref:`installed <tippy-gv-installation>`, a
:ref:`console script <tippy-gv-reference-cli-geovista>` [#]_ will be available with
several convenience commands to assist with the management of ``geovista``
and its resources.


.. _gv-reference-cli-geovista:
.. _tippy-gv-reference-cli-geovista:

.. click:: geovista.cli:main
    :prog: geovista
    :nested: none



Commands
--------

The following :ref:`geovista console script <tippy-gv-reference-cli-geovista>` commands are
available:

.. toctree::

    download
    examples
    plot


.. [#] See `entry-points`_ for further information.


.. comment

    🔗 URL resources in alphabetical order:


.. _entry-points: https://setuptools.pypa.io/en/latest/userguide/entry_point.html
