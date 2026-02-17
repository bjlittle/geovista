.. include:: ../common.txt

.. _gv-developer-packaging:
.. _tippy-gv-developer-packaging:

:fa:`box-archive` Packaging
===========================

.. |Pixi| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/prefix-dev/pixi/main/assets/badge/v0.json
   :target: https://pixi.prefix.dev
.. |SPEC0| image:: https://img.shields.io/badge/SPEC-0-green?labelColor=%23004811&color=%235CA038
   :target: https://scientific-python.org/specs/spec-0000/

|Pixi| |SPEC0|

.. image:: ../_static/images/pixi-banner.svg
   :align: center
   :target: https://pixi.prefix.dev
   :alt: Pixi

.. raw:: html

   <hr>

.. note::
   :class: margin, dropdown, toggle-shown

   We follow *Scientific Python Ecosystem Coordination* (`SPEC`_)
   recommendation for *Minimum Supported Dependencies* (`SPEC 0`_), and
   typically support the latest **2-3** distributions of ``python``.

Package management is orchestrated and performed by `pixi`_.

Our ``pixi`` :term:`environments <Environment>`, :term:`features <Feature>`,
and :term:`tasks <Task>` are defined within the :bash:`pyproject.toml` manifest.

``pixi`` offers `fast`_, reproducible, cross-platform environment management that
enables us to `resolve`_ and provision robust, consistent environments
blended with packages from both ``conda`` and ``PyPI`` ecosystems.

We offer several similar **collections** of ``pixi`` environments for each
supported distribution of ``python``. Each environment within a collection belongs
to the same `solve-group`_ i.e., environments within the **same** solve-group
have their **dependencies resolved at the same time**, which means that all
those environments share the exact same dependencies but may also include
additional dependencies compatible within the solve-group.

.. tip::
   :class: dropdown, toggle-shown

   We've adopted the following format convention to help clarify each type of
   ``pixi`` component:

   - :guilabel:`environment-name`
   - ``{feature-name}``
   - ``task-name``
   - :guilabel:`&s&o&l&v&e&-&g&r&o&u&p&-&n&a&m&e`


.. _gv-developer-packaging-pixi-solve-groups:
.. _tippy-gv-developer-packaging-pixi-solve-groups:

:fa:`group-arrows-rotate` Pixi Solve-Groups
-------------------------------------------

Our ``pixi`` **environments** are organized into collections by `solve-group`_.
See the :toml:`[tool.pixi.environments]` table defined in the :bash:`pyproject.toml`
manifest.

The **primary** solve-group is called :guilabel:`&d&e&f&a&u&l&t` and will always
contain the **latest** supported distribution of ``python``. This is denoted by
the ``{py}`` feature which represents the **latest** distribution of ``python``
as recommended by `SPEC 0`_.

.. table:: Pixi :guilabel:`&d&e&f&a&u&l&t` Solve-Group
   :align: center
   :widths: 1 2 5

   +----------------------+-----------------------------+--------------------------------------------------+
   | Environment          | Features                    | Description                                      |
   +======================+=============================+==================================================+
   | :guilabel:`default`  | ``{default}``, ``{py}``     | This environment contains the **core**           |
   |                      |                             | dependencies of ``geovista`` along with the      |
   |                      |                             | **latest** supported distribution of ``python``. |
   |                      |                             | See the :toml:`[tool.pixi.dependencies]` table   |
   |                      |                             | in the :bash:`pyproject.toml` manifest.          |
   +----------------------+-----------------------------+--------------------------------------------------+
   | :guilabel:`devs`     | ``{default}``, ``{devs}``,  | As per the :guilabel:`default` environment plus  |
   |                      | ``{py}``                    | additional **development** dependencies.         |
   +----------------------+-----------------------------+--------------------------------------------------+
   | :guilabel:`docs`     | ``{default}``, ``{devs}``,  | As per the :guilabel:`devs` environment plus     |
   |                      | ``{docs}``, ``{py}``        | additional **documentation** dependencies.       |
   +----------------------+-----------------------------+--------------------------------------------------+
   | :guilabel:`geovista` | ``{default}``, ``{devs}``,  | This environment is the **union** of all         |
   |                      | ``{docs}``, ``{geovista}``, | environments in the :guilabel:`&d&e&f&a&u&l&t`   |
   |                      | ``{py}``, ``{test}``        | solve-group.                                     |
   +----------------------+-----------------------------+--------------------------------------------------+
   | :guilabel:`test`     | ``{default}``, ``{devs}``,  | As per the :guilabel:`devs` environment plus     |
   |                      | ``{py}``, ``{test}``        | additional **test** dependencies.                |
   +----------------------+-----------------------------+--------------------------------------------------+

.. seealso::
   :class: dropdown, toggle-shown

   The :bash:`pixi info` command provides key information about the system, environments,
   solve-groups, dependencies and tasks in the workspace.

Given the above :guilabel:`&d&e&f&a&u&l&t` solve-group we have the following
inheritance relationship between its environments:

.. mermaid::
   :align: center
   :caption: Environment Hierarchy for :guilabel:`&d&e&f&a&u&l&t` Solve-Group

   ---
   config:
      theme: base
      themeVariables:
         lineColor: "#F8B229"
         nodeBorder: "#2569E9"
         primaryColor: "#DCE7FC"
         secondaryColor: "#F4DDFF"
   ---
   graph LR
      default(["`**default**`"])
      devs(["`**devs**`"])
      docs(["`**docs**`"])
      test(["`**test**`"])
      geovista(["`**geovista**`"])
      default -. "`*core*`" .-> devs
      devs ---> docs
      devs ---> test
      docs ---> geovista
      test ---> geovista

.. note::
   :class: dropdown, toggle-shown

   As its name suggests, the :guilabel:`default` environment is used
   **by default** when no explicit environment name is specified to ``pixi``.
   e.g., the :bash:`pixi shell` command starts a shell with the :guilabel:`default`
   environment activated, whereas the :bash:`pixi shell -e devs` command will
   activate the :guilabel:`devs` environment instead.

Several **secondary** solve-groups are available, each of which are named
after the distribution of ``python`` that they support e.g., :guilabel:`&p&y&3&1&3`.

The number of different ``python`` distribution solve-groups on offer at any
given time is dictated by `SPEC 0`_.

The generic :guilabel:`&p&y&3&x&x` solve-group is used here as a convenience to
represent each of the different ``python`` distribution solve-groups available,
all of which are **identical** in structure and content apart from the specific
distribution of ``python`` that they support.

Also note that each :guilabel:`&p&y&3&x&x` solve-group will always contain the
similarly named ``{py3xx}`` feature e.g., the :guilabel:`&p&y&3&1&3` solve-group
will contain the ``{py313}`` feature which in turn defines the ``python=3.13``
dependency to be included in all ``py313`` environments.

.. table:: Pixi :guilabel:`&p&y&3&x&x` Solve-Groups
   :align: center
   :widths: 2 2 6

   +----------------------------+-----------------------------+-----------------------------------------------+
   | Environment                | Feature                     | Description                                   |
   +============================+=============================+===============================================+
   | :guilabel:`devs-py3xx`     | ``{default}``, ``{devs}``,  | As per the :guilabel:`py3xx` environment      |
   |                            | ``{py3xx}``                 | plus additional **development** dependencies. |
   +----------------------------+-----------------------------+-----------------------------------------------+
   | :guilabel:`docs-py3xx`     | ``{default}``, ``{devs}``,  | As per the :guilabel:`devs-py3xx` environment |
   |                            | ``{docs}`` , ``{py3xx}``    | plus additional **documentation**             |
   |                            |                             | dependencies.                                 |
   +----------------------------+-----------------------------+-----------------------------------------------+
   | :guilabel:`geovista-py3xx` | ``{default}``, ``{devs}``,  | This environment is the **union** of all      |
   |                            | ``{docs}``, ``{geovista}``, | environments in the same                      |
   |                            | ``{py3xx}``, ``{test}``     | :guilabel:`&p&y&3&x&x` solve-group.           |
   +----------------------------+-----------------------------+-----------------------------------------------+
   | :guilabel:`py3xx`          | ``{default}``, ``{py3xx}``  | This environment contains the **core**        |
   |                            |                             | dependencies of ``geovista`` along with       |
   |                            |                             | ``python`` distribution ``py3xx`` e.g.,       |
   |                            |                             | ``py313``.                                    |
   +----------------------------+-----------------------------+-----------------------------------------------+
   | :guilabel:`test-py3xx`     | ``{default}``, ``{devs}``,  | As per the :guilabel:`devs-py3xx` environment |
   |                            | ``{py3xx}``, ``{test}``     | plus additional **test** dependencies.        |
   +----------------------------+-----------------------------+-----------------------------------------------+

.. attention::
   :class: dropdown

   The generic :guilabel:`&p&y&3&x&x` solve-group does **not** exist, neither does
   the generic ``{py3xx}`` feature.

Given the above :guilabel:`&p&y&3&x&x` solve-group we have the following
inheritance relationship between its environments:

.. mermaid::
   :align: center
   :caption: Environment Hierarchy for :guilabel:`&p&y&3&x&x` Solve-Group

   ---
   config:
      theme: base
      themeVariables:
         lineColor: "#F8B229"
         nodeBorder: "#2569E9"
         primaryColor: "#DCE7FC"
         secondaryColor: "#F4DDFF"
   ---
   graph LR
      py3xx(["`**py3xx**`"])
      devs(["`**devs-py3xx**`"])
      docs(["`**docs-py3xx**`"])
      test(["`**test-py3xx**`"])
      geovista(["`**geovista-py3xx**`"])
      py3xx --> |"`*core*`"| devs
      devs --> docs
      devs --> test
      docs --> geovista
      test --> geovista


:fa:`puzzle-piece` Pixi Features
--------------------------------

A ``pixi`` :term:`environment <Environment>` is defined by combining one or
more :term:`features <Feature>`. For further details see this ``pixi`` `tutorial`_
on how to create and use features in a multi-environment scenario.

Our features are defined under the :toml:`[tool.pixi.feature]` tables in the
:bash:`pyproject.toml` manifest.

Each named `feature table`_ e.g., :toml:`[tool.pixi.feature.devs]`, may contain
various fields, such as :toml:`dependencies`, :toml:`pypi-dependencies`,
:toml:`pypi-options`, :toml:`system-requirements`, :toml:`activation`, :toml:`platforms`,
:toml:`channels`, :toml:`channel-priority`, :toml:`target` and :toml:`tasks`.

.. table:: Pixi Features
   :align: center
   :widths: 1 2 6

   +----------------+---------------------------------------+----------------------------------------------------+
   | Feature        | TOML Table                            | Description                                        |
   +================+=======================================+====================================================+
   | ``{default}``  | :toml:`[tool.pixi.dependencies]`      | This feature is used to define the **core**        |
   |                |                                       | :toml:`dependencies` and :toml:`tasks` of          |
   |                |                                       | ``geovista``. Note that the ``{default}`` feature  |
   |                |                                       | is `automatically included`_ in all environments   |
   |                |                                       | by ``pixi``.                                       |
   +----------------+---------------------------------------+----------------------------------------------------+
   | ``{devs}``     | :toml:`[tool.pixi.feature.devs]`      | This feature is used to define the **development** |
   |                |                                       | :toml:`dependencies` and                           |
   |                |                                       | :toml:`pypi-dependencies`. Note that an            |
   |                |                                       | **editable** install of ``geovista`` is performed  |
   |                |                                       | by the ``{devs}`` feature.                         |
   +----------------+---------------------------------------+----------------------------------------------------+
   | ``{docs}``     | :toml:`[tool.pixi.feature.docs]`      | This feature is used to define the                 |
   |                |                                       | **documentation** :toml:`dependencies`,            |
   |                |                                       | :toml:`pypi-dependencies` and :toml:`tasks`.       |
   +----------------+---------------------------------------+----------------------------------------------------+
   | ``{geovista}`` | :toml:`[tool.pixi.feature.geovista]`  | This feature is only used to define :toml:`tasks`. |
   +----------------+---------------------------------------+----------------------------------------------------+
   | ``{py3xx}``    | :toml:`[tools.pixi.feature.py3xx]`    | This feature is used to explicitly define the      |
   |                |                                       | distribution of ``python`` supported e.g.,         |
   |                |                                       | ``py313``. Note that the :toml:`dependencies` of   |
   |                |                                       | this feature additionally includes the ``pip``     |
   |                |                                       | package. The number of different ``python``        |
   |                |                                       | distributions supported is governed by             |
   |                |                                       | `SPEC 0`_.                                         |
   +----------------+---------------------------------------+----------------------------------------------------+
   | ``{test}``     | :toml:`[tool.pixi.feature.test]`      | This feature is used to define the **test**        |
   |                |                                       | :toml:`dependencies` and :toml:`tasks`.            |
   +----------------+---------------------------------------+----------------------------------------------------+


.. _gv-developer-packaging-pixi-tasks:
.. _tippy-gv-developer-packaging-pixi-tasks:

:fa:`clapperboard` Pixi Tasks
-----------------------------

A ``pixi`` :term:`task <Task>` is a custom `cross-platform workflow command`_
that is defined as part of a :term:`feature <Feature>` within an
:term:`environment <Environment>`.

All our tasks are defined within the :bash:`pyproject.toml` manifest.

Tasks expose a convenient and easy to use entry-point to commands that allow
streamlined and automated custom workflows.

The following tasks are defined for each of our features:

.. table:: Pixi Tasks
   :align: center
   :widths: 1 1 6

   +----------------+-----------------+---------------------------------------------------------------------------------------+
   | Feature        | Task            | Description                                                                           |
   +================+=================+=======================================================================================+
   | ``{default}``  | ``download``    | Download and cache offline assets.                                                    |
   |                |                 |                                                                                       |
   |                |                 | This task calls the :ref:`tippy-gv-reference-cli-download` command. Provide optional  |
   |                |                 | argument ``all``, ``clean``, ``doc-images``, ``dry-run``, ``images``, ``list``,       |
   |                |                 | ``natural-earth``, ``operational``, ``pantry``, ``rasters``, ``unit-images`` or       |
   |                |                 | ``verify``. Defaults to ``all`` e.g.,                                                 |
   |                |                 |                                                                                       |
   |                |                 | .. code:: console                                                                     |
   |                |                 |                                                                                       |
   |                |                 |    $ pixi run download operational                                                    |
   |                |                 |                                                                                       |
   +----------------+-----------------+---------------------------------------------------------------------------------------+
   | ``{docs}``     | ``clean``       | Purge all `sphinx-autoapi`_, `sphinx-gallery`_ `sphinx-tags`_, carousel, and other    |
   |                |                 | `sphinx-build`_ artifacts e.g.,                                                       |
   |                |                 |                                                                                       |
   |                |                 | .. code:: console                                                                     |
   |                |                 |                                                                                       |
   |                |                 |    $ pixi run clean                                                                   |
   |                |                 |                                                                                       |
   |                |                 | This task is an alias for the :bash:`make clean` command.                             |
   |                +-----------------+---------------------------------------------------------------------------------------+
   |                | ``clean-all``   | Perform both the ``clean`` and ``clean-cache`` tasks e.g.,                            |
   |                |                 |                                                                                       |
   |                |                 | .. code:: console                                                                     |
   |                |                 |                                                                                       |
   |                |                 |    $ pixi run clean-all                                                               |
   |                |                 |                                                                                       |
   |                |                 | This task is an alias for the :bash:`make clean-all` command.                         |
   |                +-----------------+---------------------------------------------------------------------------------------+
   |                | ``clean-cache`` | Purge the `myst-nb`_ Jupyter cache. See `myst-nb configuration`_ for further details  |
   |                |                 | e.g.,                                                                                 |
   |                |                 |                                                                                       |
   |                |                 | .. code:: console                                                                     |
   |                |                 |                                                                                       |
   |                |                 |    $ pixi run clean-cache                                                             |
   |                |                 |                                                                                       |
   |                |                 | This task is an alias for the :bash:`make clean-cache` command.                       |
   |                +-----------------+---------------------------------------------------------------------------------------+
   |                | ``doctest``     | Execute `sphinx.ext.doctest`_ to test code snippets within the documentation i.e.,    |
   |                |                 |                                                                                       |
   |                |                 | .. code:: console                                                                     |
   |                |                 |                                                                                       |
   |                |                 |    $ pixi run doctest                                                                 |
   |                |                 |                                                                                       |
   |                |                 | Note that the ``clean`` task is called prior to running this task.                    |
   |                |                 |                                                                                       |
   |                |                 | This task is an alias for the :bash:`make doctest` command.                           |
   |                +-----------------+---------------------------------------------------------------------------------------+
   |                | ``make``        | Build the documentation.                                                              |
   |                |                 |                                                                                       |
   |                |                 | Provide optional argument ``html``, ``html-docstring``, ``html-docstring-inline``,    |
   |                |                 | ``html-gallery``, ``html-inline`` or ``html-noplot``. Defaults to ``html-noplot``     |
   |                |                 | e.g.,                                                                                 |
   |                |                 |                                                                                       |
   |                |                 | .. code:: console                                                                     |
   |                |                 |                                                                                       |
   |                |                 |    $ pixi run make html-gallery                                                       |
   |                |                 |                                                                                       |
   |                |                 | Note that the ``clean`` task is called prior to running this task.                    |
   |                |                 |                                                                                       |
   |                |                 | This task is an alias for the :bash:`make` command.                                   |
   |                +-----------------+---------------------------------------------------------------------------------------+
   |                | ``serve-html``  | Build the documentation and start a local ``HTTP`` server on port ``11000`` to view   |
   |                |                 | the rendered documentation. This is necessary in order to support interactive scenes. |
   |                |                 |                                                                                       |
   |                |                 | Note that the ``clean`` and ``make`` tasks are called prior to running this task.     |
   |                |                 |                                                                                       |
   |                |                 | Defaults to passing ``html-noplot`` to the ``make`` task. Override this behaviour by  |
   |                |                 | providing an alternative optional argument as per the ``make`` task e.g.,             |
   |                |                 |                                                                                       |
   |                |                 | .. code:: console                                                                     |
   |                |                 |                                                                                       |
   |                |                 |    $ pixi run serve-html html                                                         |
   |                |                 |                                                                                       |
   |                |                 | This task is an alias for the :bash:`make serve-html` command.                        |
   +----------------+-----------------+---------------------------------------------------------------------------------------+
   | ``{geovista}`` | ``tests-docs``  | Perform documentation image tests of ``pyvista-plot`` directive static scenes e.g.,   |
   |                |                 |                                                                                       |
   |                |                 | .. code:: console                                                                     |
   |                |                 |                                                                                       |
   |                |                 |    $ pixi run tests-docs                                                              |
   |                |                 |                                                                                       |
   |                |                 | This task calls :bash:`pytest --doc_mode` to perform the documentation image tests    |
   |                |                 | using the `pytest-pyvista`_ plugin. Refer to the :toml:`[tool.pytest.ini_options]`    |
   |                |                 | table entry in the :bash:`pyproject.toml` manifest for default configuration options. |
   |                |                 |                                                                                       |
   |                |                 | Note that the ``download doc-images`` and ``make html-docstring-inline`` tasks are    |
   |                |                 | called prior to running this task.                                                    |
   |                |                 |                                                                                       |
   |                |                 | This task is only available in the :guilabel:`geovista` and                           |
   |                |                 | :guilabel:`geovista-py3xx` environments.                                              |
   +----------------+-----------------+---------------------------------------------------------------------------------------+
   | ``{test}``     | ``tests-clean`` | Purge both the documentation and unit test image caches, along with any images        |
   |                |                 | generated from previous test sessions e.g.,                                           |
   |                |                 |                                                                                       |
   |                |                 | .. code:: console                                                                     |
   |                |                 |                                                                                       |
   |                |                 |    $ pixi run tests-clean                                                             |
   |                |                 |                                                                                       |
   |                +-----------------+---------------------------------------------------------------------------------------+
   |                | ``tests-unit``  | Perform the unit tests.                                                               |
   |                |                 |                                                                                       |
   |                |                 | This task calls the ``pytest`` command. Defaults to executing all unit tests          |
   |                |                 | discoverable from the :bash:`geovista` root directory.                                |
   |                |                 |                                                                                       |
   |                |                 | Accepts a valid ``pytest`` marker expression as an optional argument. Refer to the    |
   |                |                 | :toml:`[tool.pytest.ini_options]` table entry in the :bash:`pyproject.toml` manifest  |
   |                |                 | for configured ``markers`` e.g.,                                                      |
   |                |                 |                                                                                       |
   |                |                 | .. code:: console                                                                     |
   |                |                 |                                                                                       |
   |                |                 |    $ pixi run tests-unit "not image"                                                  |
   |                |                 |                                                                                       |
   |                |                 | Note that the ``tests-clean`` task is called prior to running this task.              |
   |                |                 |                                                                                       |
   |                |                 | .. note::                                                                             |
   |                |                 |    :class: dropdown                                                                   |
   |                |                 |                                                                                       |
   |                |                 |    Failed :ref:`tippy-gv-developer-testing-image-tests` are captured via the          |
   |                |                 |    ``pytest-pyvista`` plugin option ``--failed_image_dir`` (see                       |
   |                |                 |    :ref:`Image Tests Generation <tippy-gv-developer-testing-image-tests-generation>`) |
   |                |                 |    within the :bash:`test_images_failed` directory for analysis and investigation.    |
   +----------------+-----------------+---------------------------------------------------------------------------------------+

.. seealso::
   :class: dropdown, toggle-shown

   The :bash:`pixi task list` command describes each task available within the workspace.

   Whereas the :bash:`pixi task list --summary` command enumerates the tasks available per environment.


.. _gv-developer-packaging-continuous-integration:
.. _tippy-gv-developer-packaging-continuous-integration:

:fab:`github` Continuous Integration
------------------------------------

.. |ci-locks| image:: https://github.com/bjlittle/geovista/actions/workflows/ci-locks.yml/badge.svg
   :target: https://github.com/bjlittle/geovista/actions/workflows/ci-locks.yml
.. |ci-wheels| image:: https://github.com/bjlittle/geovista/actions/workflows/ci-wheels.yml/badge.svg
   :target: https://github.com/bjlittle/geovista/actions/workflows/ci-wheels.yml

The following packaging workflows are available:

.. table:: Packaging Workflows
   :align: center
   :widths: 1 4

   +-------------+-------------------------------------------------------------------------------------+
   | Workflow    | Description                                                                         |
   +=============+=====================================================================================+
   | |ci-locks|  | The `ci-locks.yml`_ ``cron`` based :term:`GHA workflow <GHA>` regularly schedules   |
   |             | ``pixi`` to refresh the :bash:`pixi.lock` file based on the :bash:`pyproject.toml`  |
   |             | manifest and the latest package versions available from the ``conda`` and ``PyPI``  |
   |             | ecosystems.                                                                         |
   |             |                                                                                     |
   |             | Only the **latest** ``python`` variant of the :guilabel:`geovista-py3xx`            |
   |             | environment e.g., :guilabel:`geovista-py313`, will be exported to a ``conda``       |
   |             | explicit specification file (:bash:`.txt`) and also converted to an equivalent      |
   |             | explicit environment YAML file (:bash:`.yml`). These resources are available in the |
   |             | `requirements/locks`_ directory.                                                    |
   |             |                                                                                     |
   |             | Additionally, the :guilabel:`geovista-py3xx` environment will be exported           |
   |             | to the ``conda`` environment YAML file `requirements/geovista.yml`_ containing      |
   |             | only the top-level dependencies of that environment, as defined by its              |
   |             | :ref:`features <tippy-gv-developer-packaging-pixi-solve-groups>`.                   |
   +-------------+-------------------------------------------------------------------------------------+
   | |ci-wheels| | The `ci-wheels.yml`_ :term:`GHA workflow <GHA>` builds, tests and publishes the     |
   |             | source distribution (``sdist``) and binary ``wheel`` of ``geovista``.               |
   |             |                                                                                     |
   |             | We have adopted `PyPI Trusted Publishing`_ with `OpenID Connect (OIDC)`_ for secure |
   |             | deployments of assets.                                                              |
   |             |                                                                                     |
   |             | Note that the ``sdist`` and ``wheel`` assets are automatically published to         |
   |             | `Test PyPI`_ for each :fa:`code-pull-request` ``pull-request`` merged to the        |
   |             | ``main`` branch, and `PyPI`_ for each ``tag`` release.                              |
   +-------------+-------------------------------------------------------------------------------------+


.. _gv-developer-packaging-python-package-index:
.. _tippy-gv-developer-packaging-python-package-index:

:fab:`python` Python Package Index
----------------------------------

``PyPI`` package dependencies are configured in the :bash:`pyproject.toml` manifest
under the :toml:`[tool.setuptools.dynamic]` and
:toml:`[tool.setuptools.dynamic.optional-dependencies]` table entries.

Version management of our ``PyPI`` dependencies is orchestrated by :fab:`github`
`Dependabot`_. Refer to the ``package-ecosystem: "pip"`` key entry in the
`.github/dependabot.yml`_ file for further details.

The :fab:`github` `Dependabot`_ service is regularly scheduled to check the
versions of our dependencies and automatically increment them using maximum
capping pins via a :fa:`code-pull-request` ``pull-request`` in response to the
latest available package updates within the ``PyPI`` ecosystem.

.. attention::
   :class: dropdown

   Updates to the ``PyPI`` maximum capping pins may require to be manually
   reflected in the :bash:`pyproject.toml` manifest for similar ``pixi`` managed
   ``conda`` dependencies.

   Track native :fab:`github` `Dependabot`_ support for ``pixi`` in
   `dependabot/dependabot-core issue#2227`_ 🤞


.. _OpenID Connect (OIDC): https://openid.net/developers/how-connect-works/
.. _PyPI Trusted Publishing: https://docs.pypi.org/trusted-publishers/
.. _.github/dependabot.yml: https://github.com/bjlittle/geovista/blob/main/.github/dependabot.yml
.. _automatically included: https://pixi.prefix.dev/latest/tutorials/multi_environment/#default
.. _ci-locks.yml: https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-locks.yml
.. _ci-wheels.yml: https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-wheels.yml
.. _cross-platform workflow command: https://pixi.prefix.dev/latest/workspace/advanced_tasks/
.. _dependabot/dependabot-core issue#2227: https://github.com/dependabot/dependabot-core/issues/2227#issuecomment-1709069470
.. _fast: https://prefix.dev/blog/sharded_repodata
.. _feature table: https://pixi.prefix.dev/latest/reference/pixi_manifest/#the-feature-table
.. _myst-nb configuration: https://myst-nb.readthedocs.io/en/latest/configuration.html
.. _requirements/geovista.yml: https://github.com/bjlittle/geovista/blob/main/requirements/geovista.yml
.. _requirements/locks: https://github.com/bjlittle/geovista/tree/main/requirements/locks
.. _resolve: https://pixi.prefix.dev/latest/workspace/environment/#solving-environments
.. _solve-group: https://pixi.prefix.dev/latest/workspace/multi_environment/#feature-environment-set-definitions
.. _tutorial: https://pixi.prefix.dev/latest/tutorials/multi_environment/
