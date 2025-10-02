.. include:: ../common.txt

.. _gv-developer-testing:
.. _tippy-gv-developer-testing:

:fa:`flask-vial` Testing
========================

.. |codecov| image:: https://codecov.io/gh/bjlittle/geovista/branch/main/graph/badge.svg?token=RVVXGP1SD3
   :target: https://codecov.io/gh/bjlittle/geovista

|codecov|

Here we provide some high-level guidelines for contributors on how-to test
``geovista``, along with a summary of the automated quality assurance
infrastructure.


:fab:`github` Continuous Integration
------------------------------------

.. |ci-test| image:: https://github.com/bjlittle/geovista/actions/workflows/ci-tests.yml/badge.svg
    :target: https://github.com/bjlittle/geovista/actions/workflows/ci-tests.yml
.. |ci-lock| image:: https://github.com/bjlittle/geovista/actions/workflows/ci-tests-lock.yml/badge.svg
    :target: https://github.com/bjlittle/geovista/actions/workflows/ci-tests-lock.yml
.. |ci-pypi| image:: https://github.com/bjlittle/geovista/actions/workflows/ci-tests-pypi.yml/badge.svg
    :target: https://github.com/bjlittle/geovista/actions/workflows/ci-tests-pypi.yml

.. note::
  :class: margin, dropdown, toggle-shown

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
    +-----------+---------------------------------------------------------------------------------------------------------------+
    | |ci-lock| | The `ci-tests-lock.yml`_ ``cron`` based :fab:`github` Action regularly schedules the execution of both the    |
    |           | :ref:`tippy-gv-developer-testing-image-tests` and :ref:`tippy-gv-developer-testing-unit-tests` for the        |
    |           | **latest** `SPEC 0`_ supported distribution of ``python``.                                                    |
    |           |                                                                                                               |
    |           | Prior to running the tests ``pixi`` performs an **ephemeral** refresh of the ``pixi.lock`` file based on the  |
    |           | ``pyproject.toml`` manifest and the **latest** package versions available from the ``conda`` and ``PyPI``     |
    |           | ecosystems.                                                                                                   |
    |           |                                                                                                               |
    |           | The purpose of this :fab:`github` Action is to preemptively test against the **latest** resolved ``python``   |
    |           | variant of the :guilabel:`geovista-py3xx` environment to uncover and highlight any issues prior to            |
    |           | refreshing the ``pixi.lock`` file with the scheduled `ci-locks.yml`_ :fab:`github` Action. See the packaging  |
    |           | :ref:`tippy-gv-developer-packaging-continuous-integration` section for further details.                       |
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
    |           |                                                                                                               |
    |           |     `pyvista`_ performs a :fab:`github` Pull-Request integration test against the ``main`` branch of          |
    |           |     ``geovista`` using the ``PyPI`` ecosystem. This :fab:`github` Action provides a critical early warning    |
    |           |     of potential upstream issues that should be resolved as a priority.                                       |
    |           |                                                                                                               |
    +-----------+---------------------------------------------------------------------------------------------------------------+


.. _gv-developer-testing-image-tests:
.. _tippy-gv-developer-testing-image-tests:

:fa:`images` Image Tests
------------------------

Blah.


.. _gv-developer-testing-pixi-workflow:
.. _tippy-gv-developer-testing-pixi-workflow:

:fa:`lines-leaning` Pixi Workflow
---------------------------------

.. admonition:: Pixi Environment

    Testing ``pixi`` :term:`tasks <Task>` are available in the :guilabel:`test`,
    :guilabel:`geovista` and :guilabel:`py3xx` variant of those ``pixi`` environments
    e.g., :guilabel:`geovista-py313`. See :ref:`tippy-gv-developer-packaging`
    for further details.

Testing may be performed using the convenience of
`pixi run <https://pixi.sh/latest/reference/cli/pixi/run/>`__ tasks, all of
which **do not** require to be executed from within the ``geovista`` root directory
e.g.,

.. code:: console

    $ pixi run <pixi-task>

.. table:: Pixi Tasks
    :align: center
    :widths: 1 3

    +-------------------------+---------------------------------------------------------------+
    | Pixi Task               | Description                                                   |
    +=========================+===============================================================+
    | :guilabel:`tests-clean` | Purge both the documentation and unit test image caches,      |
    |                         | along with any images generated from previous test sessions   |
    |                         | e.g.,                                                         |
    |                         |                                                               |
    |                         | .. code:: console                                             |
    |                         |                                                               |
    |                         |     $ pixi run tests-clean                                    |
    |                         |                                                               |
    +-------------------------+---------------------------------------------------------------+
    | :guilabel:`tests-unit`  | Perform unit tests.                                           |
    |                         |                                                               |
    |                         | This task calls the ``pytest`` command. Defaults to executing |
    |                         | all unit tests discoverable from the ``geovista`` root        |
    |                         | directory.                                                    |
    |                         |                                                               |
    |                         | Accepts a valid ``pytest`` marker expression as an optional   |
    |                         | argument. Refer to the ``[tool.pytest.ini_options]`` table    |
    |                         | entry in the ``pyproject.toml`` manifest for configured       |
    |                         | ``markers`` e.g.,                                             |
    |                         |                                                               |
    |                         | .. code:: console                                             |
    |                         |                                                               |
    |                         |     $ pixi run tests-unit "not image"                         |
    |                         |                                                               |
    |                         | Note that the ``tests-clean`` task is called prior to running |
    |                         | this task.                                                    |
    +-------------------------+---------------------------------------------------------------+

.. tip::
    :class: dropdown, toggle-shown

    Apply the ``--frozen`` option to avoid `pixi`_ checking and updating the ``pixi.lock`` file.

    e.g., To execute all non-image based unit tests:

    .. code:: console

        $ pixi run --frozen tests-unit "not image"


.. _gv-developer-testing-unit-tests:
.. _tippy-gv-developer-testing-unit-tests:

:fa:`vial-circle-check` Unit Tests
----------------------------------

Blah.


.. comment

    Page link URL resources in alphabetical order:


.. _ci-locks.yml: https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-locks.yml
.. _ci-tests.yml: https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-tests.yaml
.. _ci-tests-lock.yml: https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-tests-lock.yml
.. _ci-tests-pypi.yml: https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-tests-pypi.yml
.. _codecov: https://app.codecov.io/gh/bjlittle/geovista
.. _dependabot.yml: https://github.com/bjlittle/geovista/blob/main/.github/dependabot.yml
