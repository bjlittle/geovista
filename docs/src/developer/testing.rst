.. include:: ../common.txt

.. _gv-developer-testing:
.. _tippy-gv-developer-testing:

:fa:`flask-vial` Testing
========================

.. |codecov| image:: https://codecov.io/gh/bjlittle/geovista/branch/main/graph/badge.svg?token=RVVXGP1SD3
   :target: https://codecov.io/gh/bjlittle/geovista

|codecov|

Here we provide some high-level guidelines for contributors on how-to test
``geovista`` with `pytest`_, along with a summary of the automated quality assurance
infrastructure.

.. note::
   :class: dropdown, toggle-shown

   The unit tests are not bundled within the ``geovista`` package distributed
   on ``conda-forge`` or ``PyPI``.


:fab:`github` Continuous Integration
------------------------------------

.. |ci-test| image:: https://github.com/bjlittle/geovista/actions/workflows/ci-tests.yml/badge.svg
    :target: https://github.com/bjlittle/geovista/actions/workflows/ci-tests.yml
.. |ci-lock| image:: https://github.com/bjlittle/geovista/actions/workflows/ci-tests-lock.yml/badge.svg
    :target: https://github.com/bjlittle/geovista/actions/workflows/ci-tests-lock.yml
.. |ci-pypi| image:: https://github.com/bjlittle/geovista/actions/workflows/ci-tests-pypi.yml/badge.svg
    :target: https://github.com/bjlittle/geovista/actions/workflows/ci-tests-pypi.yml

.. note::
   :class: dropdown, toggle-shown

   We follow *Scientific Python Ecosystem Coordination* (`SPEC`_)
   recommendation for *Minimum Supported Dependencies* (`SPEC 0`_), and
   typically support the latest **2-3** distributions of ``python``.

The following testing workflows are available:

.. table:: Testing Workflows
   :widths: 1 3
   :align: center

   +-----------+---------------------------------------------------------------------------------------------------------------+
   | Workflow  | Description                                                                                                   |
   +===========+===============================================================================================================+
   | |ci-test| | The `ci-tests.yml`_ :fab:`github` Action executes both the :ref:`tippy-gv-developer-testing-image-tests`      |
   |           | and :ref:`tippy-gv-developer-testing-unit-tests` for each `SPEC 0`_ supported distribution of ``python``.     |
   |           |                                                                                                               |
   |           | A `codecov`_ report is generated only for the **latest** supported distribution of ``python``.                |
   |           |                                                                                                               |
   |           | Also see the testing :ref:`tippy-gv-developer-testing-pixi-workflow` :guilabel:`tests-unit` task.             |
   |           |                                                                                                               |
   |           | .. note::                                                                                                     |
   |           |    :class: dropdown                                                                                           |
   |           |                                                                                                               |
   |           |    Failed :ref:`tippy-gv-developer-testing-image-tests` are captured via the ``pytest-pyvista`` plugin option |
   |           |    ``--failed_image_dir`` (see :ref:`tippy-gv-developer-testing-image-tests-generation`), and uploaded and    |
   |           |    archived as a :fab:`github` `Workflow Artifact`_ for the CI job. The failed unit test images may then be   |
   |           |    downloaded for analysis and investigation.                                                                 |
   +-----------+---------------------------------------------------------------------------------------------------------------+
   | |ci-lock| | The `ci-tests-lock.yml`_ ``cron`` based :fab:`github` Action regularly schedules the execution of both the    |
   |           | :ref:`tippy-gv-developer-testing-image-tests` and :ref:`tippy-gv-developer-testing-unit-tests` for the        |
   |           | **latest** `SPEC 0`_ supported distribution of ``python``.                                                    |
   |           |                                                                                                               |
   |           | Prior to running the tests ``pixi`` performs an **ephemeral** refresh of the :bash:`pixi.lock` file based on  |
   |           | the :bash:`pyproject.toml` manifest and the **latest** package versions available from the ``conda`` and      |
   |           | ``PyPI`` ecosystems.                                                                                          |
   |           |                                                                                                               |
   |           | The purpose of this :fab:`github` Action is to preemptively test against the **latest** resolved ``python``   |
   |           | variant of the :guilabel:`geovista-py3xx` environment to uncover and highlight any issues prior to            |
   |           | refreshing the :bash:`pixi.lock` file with the scheduled `ci-locks.yml`_ :fab:`github` Action. See the        |
   |           | packaging :ref:`tippy-gv-developer-packaging-continuous-integration` section for further details.             |
   |           |                                                                                                               |
   |           | Any subsequent test failures will result in a bespoke :fab:`github` Issue being raised for contributors to    |
   |           | investigate referencing the :fab:`github` Action ``run-id`` of the failed job.                                |
   +-----------+---------------------------------------------------------------------------------------------------------------+
   | |ci-pypi| | The `ci-tests-pypi.yml`_ ``cron`` based :fab:`github` Action regularly schedules the execution of both the    |
   |           | :ref:`tippy-gv-developer-testing-image-tests` and :ref:`tippy-gv-developer-testing-unit-tests` for the        |
   |           | **latest** `SPEC 0`_ supported distribution of ``python``.                                                    |
   |           |                                                                                                               |
   |           | Prior to running the tests ``pip`` installs the **latest** package dependencies from the ``PyPI`` ecosystem.  |
   |           | See the packaging :ref:`tippy-gv-developer-packaging-python-package-index` section for further details.       |
   |           |                                                                                                               |
   |           | The purpose of this :fab:`github` Action is to preemptively test against the **latest** resolved ``PyPI``     |
   |           | environment to uncover and highlight any issues prior to the scheduled :fab:`github` `dependabot.yml`_        |
   |           | orchestrated refresh of our ``PyPI`` package dependencies.                                                    |
   |           |                                                                                                               |
   |           | Any subsequent test failures will result in a bespoke :fab:`github` Issue being raised for contributors to    |
   |           | investigate referencing the :fab:`github` Action ``run-id`` of the failed job.                                |
   |           |                                                                                                               |
   |           | .. attention::                                                                                                |
   |           |    :class: dropdown                                                                                           |
   |           |                                                                                                               |
   |           |    `pyvista`_ performs a :fab:`github` ``pull-request`` integration test against the ``main`` branch of       |
   |           |    ``geovista`` using the ``PyPI`` ecosystem. This :fab:`github` Action provides a critical early warning     |
   |           |    of potential upstream issues that should be resolved as a priority.                                        |
   |           |                                                                                                               |
   +-----------+---------------------------------------------------------------------------------------------------------------+


.. _gv-developer-testing-image-tests:
.. _tippy-gv-developer-testing-image-tests:

:fa:`images` Image Tests
------------------------

The image unit tests are located within the :bash:`tests/plotting` directory.


.. _gv-developer-testing-image-tests-markers:
.. _tippy-gv-developer-testing-image-tests-markers:

Markers
~~~~~~~

The following ``pytest`` markers are configured for image unit tests:

.. table:: Image Unit Test Markers
   :align: center
   :widths: 1 4

   +---------------------+-------------------------------------------------------------+
   | Marker              | Description                                                 |
   +=====================+=============================================================+
   | :guilabel:`image`   | Generic marker to be used on **all** image unit tests.      |
   +---------------------+-------------------------------------------------------------+
   | :guilabel:`example` | Specific marker only to be used on :ref:`tippy-gv-examples` |
   |                     | gallery unit tests.                                         |
   +---------------------+-------------------------------------------------------------+

.. seealso::
   :class: dropdown, toggle-shown

   For further details see the ``markers`` array entry in the :toml:`[tool.pytest.ini_options]`
   table of the :bash:`pyproject.toml` manifest.

The following marker expressions can be used for finer-grained control of unit test
selection for execution:

.. table:: Marker Expressions
   :align: center
   :widths: 3 4

   +-------------------------------------------+--------------------------------------------------------+
   | Marker Expression                         | Description                                            |
   +-------------------------------------------+--------------------------------------------------------+
   | :bash:`pytest -m image`                   | Execute all image unit tests.                          |
   +-------------------------------------------+--------------------------------------------------------+
   | :bash:`pytest -m "not image"`             | Execute all unit tests except the image unit tests.    |
   +-------------------------------------------+--------------------------------------------------------+
   | :bash:`pytest -m example`                 | Execute only the gallery unit tests.                   |
   +-------------------------------------------+--------------------------------------------------------+
   | :bash:`pytest -m "not example"`           | Execute all unit tests except the gallery unit tests.  |
   +-------------------------------------------+--------------------------------------------------------+
   | :bash:`pytest -m "image and not example"` | Execute all image unit tests that are not gallery unit |
   |                                           | tests.                                                 |
   +-------------------------------------------+--------------------------------------------------------+

.. seealso::
   :class: dropdown, toggle-shown

   Refer to the :ref:`tippy-gv-developer-testing-pixi-workflow` :guilabel:`tests-unit` task.

.. attention::
   :class: dropdown

   ``pytest`` must be executed from within the :bash:`geovista` root directory.


.. _gv-developer-testing-image-tests-fixtures:
.. _tippy-gv-developer-testing-image-tests-fixtures:

Fixtures
~~~~~~~~

All image unit tests require to use the following ``pytest`` `fixtures`_:

.. table:: Image Unit Test Fixtures
   :align: center
   :widths: 1 4

   +------------------------+---------------------------------------------------------------------+
   | Fixture                | Description                                                         |
   +------------------------+---------------------------------------------------------------------+
   | ``plot_nodeid``        | This fixture generates the unique dotted ``nodeid`` to identify     |
   |                        | the unit test relative to the :bash:`tests` root directory e.g.,    |
   |                        | ``geodesic.test_BBox.test_outline`` is the ``nodeid`` of the        |
   |                        | :python:`test_outline` unit test defined within the                 |
   |                        | :bash:`test_BBox.py` file located within the :bash:`tests/geodesic` |
   |                        | directory.                                                          |
   |                        |                                                                     |
   |                        | The fixture also ensures that the baseline image for the unit       |
   |                        | test is available in the image cache. See                           |
   |                        | :ref:`tippy-gv-developer-testing-image-tests-caching` for           |
   |                        | further details.                                                    |
   +------------------------+---------------------------------------------------------------------+
   | ``verify_image_cache`` | The `pytest-pyvista`_ ``pytest`` plugin is used to perform the      |
   |                        | image comparison between a unit test baseline image (expected)      |
   |                        | against its `pyvista`_ rendered image (actual).                     |
   |                        |                                                                     |
   |                        | This fixture requires the unit test to call the                     |
   |                        | :meth:`~pyvista.Plotter.show` method as a hook so that it can       |
   |                        | initiate the image comparison.                                      |
   |                        |                                                                     |
   |                        | .. seealso::                                                        |
   |                        |    :class: dropdown                                                 |
   |                        |                                                                     |
   |                        |    For further details see :toml:`[tool.pytest.ini_options]` table  |
   |                        |    in the :bash:`pyproject.toml` manifest.                          |
   +------------------------+---------------------------------------------------------------------+


Template
~~~~~~~~

Image unit tests should adopt the following usage pattern of
:ref:`tippy-gv-developer-testing-image-tests-markers` and
:ref:`tippy-gv-developer-testing-image-tests-fixtures` e.g.,

.. code-block:: python
   :linenos:
   :caption: Image Unit Test Template
   :emphasize-lines: 6, 7, 9, 12

   import pytest

   import geovsita as gv


   @pytest.mark.image
   def test(plot_nodeid, verify_image_cache):
       """Single line doc-string."""
       verify_image_cache.test_name = plot_nodeid
       p = gv.GeoPlotter()
       ...
       p.show()

Note that:

- :bash:`line:  6` - The :python:`@pytest.mark.image` marker must always decorate
  the unit test
- :bash:`line:  7` - Both the :python:`plot_nodeid` and :python:`verify_image_cache`
  fixures are used
- :bash:`line:  9` - The :python:`verify_image_cache` fixure is configured with
  the name of the unit test baseline image
- :bash:`line: 12` - The :meth:`~pyvista.Plotter.show` method of the plotter is
  called to render the unit test scene and then invoke image comparison via the
  ``pytest-pyvista`` plugin configured by its :python:`verify_image_cache` fixture.
  Be aware that the :meth:`~pyvista.Plotter.show` method **must only be invoked once**
  within the unit test. However the test itself may be decorated with the
  :python:`@pytest.mark.parametrize` marker to execute it multiple times.



.. _gv-developer-testing-image-tests-caching:
.. _tippy-gv-developer-testing-image-tests-caching:

Caching
~~~~~~~

The ``pytest-pyvista`` plugin performs the image comparison between a
unit test baseline image (expected) and rendered image (actual) via its
``verify_image_cache`` fixture.

Unit test baseline images are automatically fetched and cached by the `pooch`_
:data:`~geovista.cache.CACHE` manager on request by the ``plot_nodeid`` fixture.

.. seealso::
   :class: margin, dropdown, toggle-shown

   The :ref:`tippy-gv-reference-cli-download` command may be used to cache
   offline assets.

The :data:`~geovista.cache.CACHE` manager fetches assets for a specific
:data:`~geovista.cache.DATA_VERSION` release tag from the `geovista-data`_ repository
and stores them according to the :mod:`resource configuration <geovista.config>`
or the :guilabel:`GEOVISTA_CACHEDIR`
:ref:`environment variable <tippy-gv-reference-environment>`.

These cached assets are made available to the ``verify_image_cache`` fixture via
the :bash:`tests/plotting/unit_image_cache` symbolic-link, as configured
within the :toml:`[tool.pytest.ini_options]` table of the :bash:`pyproject.toml` manifest.

The :bash:`tests/plotting/unit_image_cache` symbolic-link to the :data:`~geovista.cache.CACHE`
manager image cache is automatically verified and managed by the :python:`tests.plotting` module.


.. _gv-developer-testing-image-tests-generation:
.. _tippy-gv-developer-testing-image-tests-generation:

Generation
~~~~~~~~~~

Unit test rendered image (actual) generation is managed through the
``pytest-pyvista`` plugin.

For example, to serizalize all unit test rendered images to file within the
:bash:`test_images` directory e.g.,

.. code:: console

   $ pytest -m image --generated_image_dir test_images

To serialize both the baseline image (expected) and rendered image (actual) of
all unit test failures to file within the :bash:`test_images_failed` directory e.g.,

.. code:: console

   $ pytest -m image --failed_image_dir test_images_failed

.. attention::
   :class: dropdown

   ``pytest`` must be executed from within the :bash:`geovista` root directory.

Typically, we recommend the following:

- Use the ``--generated_image_dir`` option to capture the rendered image (actual)
  of any new or existing unit tests
- Use the ``--failed_image_dir`` option to capture and investigate any failed
  image unit tests

.. seealso::
   :class: dropdown, toggle-shown

   Refer to `pytest-pyvista`_ for further CLI and configuration options.

   Also see the :guilabel:`tests-unit` ``pixi`` :term:`task <Task>` in the
   following :ref:`tippy-gv-developer-testing-pixi-workflow` section, as a
   convenience.

To register a new baseline image for a unit test:

#. Generate the baseline image using the ``--generated_image_dir`` option to the
   ``pytest-pyvista`` plugin
#. Add the new baseline image to the :bash:`assets/tests/unit` directory of the
   :fab:`github` `geovista-data`_ repository via a :fa:`code-pull-request` ``pull-request``
#. Once the :fa:`code-pull-request` ``pull-request`` has been reviewed and merged,
   a new ``geovista-data`` release will be tagged automatically
#. Update the :guilabel:`DATA_VERSION` within :bash:`geovista.cache` to the new
   ``geovista-data`` release version
#. Finally, update the :bash:`registry.txt` with the unit test baseline image
   name (relative to the :bash:`assets` directory) along with the hexadecimal
   ``SHA256SUM`` of the baseline image file contents

The `pooch`_ :data:`~geovista.cache.CACHE` manager will automatically download
and cache the new baseline image from the ``geovista-data`` repository
when re-running the unit test. Alternatively, download all the new assets for
the :guilabel:`DATA_VERSION` using the CLI e.g.,

.. code:: console

   $ geovista download --all --decompress


.. _gv-developer-testing-pixi-workflow:
.. _tippy-gv-developer-testing-pixi-workflow:

:fa:`lines-leaning` Pixi Workflow
---------------------------------

.. admonition:: Pixi Environment
   :class: dropdown, toggle-shown

   The testing ``pixi`` :term:`tasks <Task>` are available in the :guilabel:`test`,
   :guilabel:`geovista` and :guilabel:`py3xx` variant of those ``pixi`` environments
   e.g., :guilabel:`geovista-py313`. See :ref:`tippy-gv-developer-packaging`
   for further details.

Testing may be performed using the convenience of
`pixi run <https://pixi.prefix.dev/latest/reference/cli/pixi/run/>`__ tasks, which
**do not** require to be executed from within :bash:`geovista` root directory
e.g.,

.. code:: console

   $ pixi run <pixi-task>

.. table:: Pixi Tasks
   :align: center
   :widths: 2 3

   +-------------------------+---------------------------------------------------------------+
   | Pixi Task               | Description                                                   |
   +=========================+===============================================================+
   | :guilabel:`download`    | Download and cache offline assets.                            |
   |                         |                                                               |
   |                         | This task calls the :ref:`tippy-gv-reference-cli-download`    |
   |                         | command. Provide optional argument ``all``, ``clean``,        |
   |                         | ``doc-images``, ``dry-run``, ``images``, ``list``,            |
   |                         | ``natural-earth``, ``operational``, ``pantry``, ``rasters``,  |
   |                         | ``unit-images`` or ``verify``. Defaults to ``all`` e.g.,      |
   |                         |                                                               |
   |                         | .. code:: console                                             |
   |                         |                                                               |
   |                         |    $ pixi run download rasters                                |
   |                         |                                                               |
   +-------------------------+---------------------------------------------------------------+
   | :guilabel:`tests-clean` | Purge both the documentation and unit test image caches,      |
   |                         | along with any images generated from previous test sessions   |
   |                         | e.g.,                                                         |
   |                         |                                                               |
   |                         | .. code:: console                                             |
   |                         |                                                               |
   |                         |    $ pixi run tests-clean                                     |
   |                         |                                                               |
   +-------------------------+---------------------------------------------------------------+
   | :guilabel:`tests-unit`  | Perform the unit tests.                                       |
   |                         |                                                               |
   |                         | This task calls the ``pytest`` command. Defaults to executing |
   |                         | all unit tests discoverable from the :bash:`geovista` root    |
   |                         | directory.                                                    |
   |                         |                                                               |
   |                         | Accepts a valid ``pytest`` marker expression as an optional   |
   |                         | argument. Refer to the :toml:`[tool.pytest.ini_options]`      |
   |                         | table entry in the :bash:`pyproject.toml` manifest for        |
   |                         | configured ``markers`` e.g.,                                  |
   |                         |                                                               |
   |                         | .. code:: console                                             |
   |                         |                                                               |
   |                         |    $ pixi run tests-unit "not image"                          |
   |                         |                                                               |
   |                         | Note that the :guilabel:`tests-clean` task is called prior to |
   |                         | running this task.                                            |
   |                         |                                                               |
   |                         | .. note::                                                     |
   |                         |    :class: dropdown                                           |
   |                         |                                                               |
   |                         |    Failed :ref:`tippy-gv-developer-testing-image-tests` are   |
   |                         |    automatically captured via the ``pytest-pyvista`` plugin   |
   |                         |    option ``--failed_image_dir`` (see                         |
   |                         |    :ref:`tippy-gv-developer-testing-image-tests-generation`)  |
   |                         |    and available within the :bash:`test_images_failed`        |
   |                         |    directory for analysis and investigation.                  |
   |                         |                                                               |
   |                         |    Additionally all generated images are captured via the     |
   |                         |    ``--generated_image_dir`` plugin option and are available  |
   |                         |    within the :bash:`test_images` directory.                  |
   +-------------------------+---------------------------------------------------------------+

.. tip::
   :class: dropdown, toggle-shown

   Apply the ``--frozen`` option to avoid `pixi`_ checking and updating the :toml:`pixi.lock` file.

   E.g., To execute all non-image based unit tests:

   .. code:: console

      $ pixi run --frozen tests-unit "not image"


.. _gv-developer-testing-unit-tests:
.. _tippy-gv-developer-testing-unit-tests:

:fa:`vial-circle-check` Unit Tests
----------------------------------

The unit tests are located within the :bash:`tests` root directory and are
organised into sub-directories, typically one for each ``geovista`` top-level
module or sub-package.

The exception to this rule is :bash:`tests/plotting` which contains the
:ref:`tippy-gv-developer-testing-image-tests`.

To execute all unit tests:

.. code:: console

   $ pytest

.. seealso::
   :class: dropdown, toggle-shown

   Refer to the :ref:`tippy-gv-developer-testing-pixi-workflow` :guilabel:`tests-unit` task.

.. attention::
   :class: dropdown

   ``pytest`` must be executed from within the :bash:`geovista` root directory.

Finer-grained control of unit test can be achieved by using our ``pytest``
:ref:`tippy-gv-developer-testing-image-tests-markers`.


.. comment

   🔗 URL resources in alphabetical order:


.. _Workflow Artifact: https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts
.. _ci-locks.yml: https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-locks.yml
.. _ci-tests.yml: https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-tests.yml
.. _ci-tests-lock.yml: https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-tests-lock.yml
.. _ci-tests-pypi.yml: https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-tests-pypi.yml
.. _codecov: https://app.codecov.io/gh/bjlittle/geovista
.. _dependabot.yml: https://github.com/bjlittle/geovista/blob/main/.github/dependabot.yml
.. _fixtures: https://docs.pytest.org/en/stable/how-to/fixtures.html#how-to-fixtures
