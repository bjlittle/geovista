.. include:: ../common.txt

.. _gv-reference-environment:
.. _tippy-gv-reference-environment:

:fab:`envira` Environment Variables
===================================

Internal and external (third-party) environment variables for either a
``user``, a ``developer``, or are set by default on a specific host
``platform`` e.g., a GitHub runner.


:fa:`square-caret-down` Internal
--------------------------------

Package environment variables that influence the behaviour of ``geovista``:

.. table:: Internal Variables
    :align: center
    :widths: auto

    +--------------------------------------+---------------+-----------------------------------------------------------+
    | Name                                 | Type          | Description                                               |
    +======================================+===============+===========================================================+
    | :guilabel:`GEOVISTA_CACHEDIR`        | ``User``      | Configures the root directory (absolute path) where       |
    |                                      |               | ``geovista`` resources will be downloaded and cached.     |
    |                                      |               | See :data:`~geovista.cache.GEOVISTA_CACHEDIR`.            |
    |                                      |               |                                                           |
    |                                      |               | Defaults to the ``geovista`` sub-directory under the user |
    |                                      |               | and platform specific cache directory returned by         |
    |                                      |               | :func:`platformdirs.user_cache_dir`.                      |
    +--------------------------------------+---------------+-----------------------------------------------------------+
    | :guilabel:`GEOVISTA_DATA_VERSION`    | ``User``      | Configures the version of data resources to be downloaded |
    |                                      |               | and cached from the :data:`~geovista.cache.BASE_URL`. See |
    |                                      |               | :data:`~geovista.cache.GEOVISTA_DATA_VERSION`.            |
    |                                      |               |                                                           |
    |                                      |               | Defaults to the specific                                  |
    |                                      |               | :data:`~geovista.cache.DATA_VERSION` bundled with the     |
    |                                      |               | version of ``geovista``.                                  |
    +--------------------------------------+---------------+-----------------------------------------------------------+
    | :guilabel:`GEOVISTA_IMAGE_TESTING`   | ``Developer`` | When set, the :mod:`geovista.theme` will not be loaded    |
    |                                      |               | and :mod:`geovista.gridlines` will not show labels.       |
    |                                      |               |                                                           |
    |                                      |               | This allows image testing to be more robust, particularly |
    |                                      |               | by being independent of any ``geovista`` theme changes.   |
    |                                      |               |                                                           |
    |                                      |               | Image tests default to using the                          |
    |                                      |               | :doc:`pyvista <pyvista:index>` testing theme.             |
    +--------------------------------------+---------------+-----------------------------------------------------------+
    | :guilabel:`GEOVISTA_POOCH_MUTE`      | ``User``      | Controls the verbosity level of the ``geovista``          |
    |                                      |               | :data:`~geovista.cache.CACHE` manager. Set to ``True`` to |
    |                                      |               | silence the :mod:`pooch` logger diagnostic warnings.      |
    |                                      |               | See :data:`~geovista.cache.GEOVISTA_POOCH_MUTE` and also  |
    |                                      |               | :func:`~geovista.cache.pooch_mute`.                       |
    |                                      |               |                                                           |
    |                                      |               | Defaults to ``False``.                                    |
    +--------------------------------------+---------------+-----------------------------------------------------------+
    | :guilabel:`GEOVISTA_SPHX_GLR_SERIAL` | ``Developer`` | When set, disables ``parallel`` building of               |
    |                                      |               | `sphinx-gallery`_.                                        |
    +--------------------------------------+---------------+-----------------------------------------------------------+
    | :guilabel:`GEOVISTA_VTK_WARNINGS`    | ``User``      | Set to ``True`` to enable backend `VTK`_ diagnostic       |
    |                                      |               | warnings.                                                 |
    |                                      |               |                                                           |
    |                                      |               | Defaults to ``False``.                                    |
    +--------------------------------------+---------------+-----------------------------------------------------------+


:far:`square-caret-up` Third-Party
----------------------------------

Notable third-party environment variables that influence the behaviour of
``geovista``:

.. table:: External Variables
    :align: center
    :widths: auto

    +--------------------------------------+---------------+---------------------------------------------------------+
    | Name                                 | Type          | Description                                             |
    +======================================+===============+=========================================================+
    | :guilabel:`CI`                       | ``Platform``  | Default environment variable set on a `GitHub Action`_  |
    |                                      |               | runner.                                                 |
    |                                      |               |                                                         |
    |                                      |               | Used by ``geovista`` to start an X virtual frame buffer |
    |                                      |               | display server via :func:`pyvista.start_xvfb`.          |
    +--------------------------------------+---------------+---------------------------------------------------------+
    | :guilabel:`EAGER_IMPORT`             | ``User``      | Set this environment variable to **disable** lazy       |
    |                                      |               | loading of ``geovista`` subpackages and external        |
    |                                      |               | libraries.                                              |
    |                                      |               |                                                         |
    |                                      |               | Deferred imports are **enabled** by default in          |
    |                                      |               | ``geovista``.                                           |
    |                                      |               |                                                         |
    |                                      |               | For further details see `lazy-loader`_ and `SPEC 1`_.   |
    +--------------------------------------+---------------+---------------------------------------------------------+
    | :guilabel:`PYVISTA_BUILDING_GALLERY` | ``Developer`` | Set to ``true`` when building the documentation         |
    |                                      |               | `sphinx-gallery`_.                                      |
    +--------------------------------------+---------------+---------------------------------------------------------+
    | :guilabel:`READTHEDOCS`              | ``Platform``  | Default environment variable set on a `Read the Docs`_  |
    |                                      |               | runner.                                                 |
    |                                      |               |                                                         |
    |                                      |               | Used by ``geovista`` to start an X virtual frame buffer |
    |                                      |               | display server via :func:`pyvista.start_xvfb`.          |
    +--------------------------------------+---------------+---------------------------------------------------------+
    | :guilabel:`XDG_CACHE_HOME`           | ``User``      | Configures the root directory (absolute path) where     |
    |                                      |               | ``geovista`` resources will be downloaded and cached.   |
    |                                      |               |                                                         |
    |                                      |               | Overrides :data:`~geovista.cache.GEOVISTA_CACHEDIR`.    |
    |                                      |               |                                                         |
    |                                      |               | For further details see                                 |
    |                                      |               | `XDG Base Directory Specification`_.                    |
    +--------------------------------------+---------------+---------------------------------------------------------+


.. comment

   🔗 URL resources in alphabetical order:


.. _SPEC 1: https://scientific-python.org/specs/spec-0001/
.. _XDG Base Directory Specification: https://specifications.freedesktop.org/basedir/latest/
.. _lazy-loader: https://github.com/scientific-python/lazy-loader
.. _GitHub Action: https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#default-environment-variables
.. _Read the Docs: https://docs.readthedocs.io/en/stable/reference/environment-variables.html#envvar-READTHEDOCS
