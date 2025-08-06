.. include:: ../common.txt

.. _gv-developer-packaging:
.. _tippy-gv-developer-packaging:

:fa:`box-archive` Packaging
===========================

.. |Pixi| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/prefix-dev/pixi/main/assets/badge/v0.json
   :target: https://pixi.sh
.. |SPEC0| image:: https://img.shields.io/badge/SPEC-0-green?labelColor=%23004811&color=%235CA038
   :target: https://scientific-python.org/specs/spec-0000/

|Pixi| |SPEC0|

.. tip::
  :class: margin, dropdown, toggle-shown

  See the ``pixi``
  `Installation <https://pixi.sh/latest/installation/>`_ instructions.

Package management is orchestrated and performed by `pixi`_.

Our ``pixi`` :term:`features <Feature>`, :term:`tasks <Task>` and
:term:`environments <Environment>` are defined within the ``pyproject.toml``
manifest file.

``pixi`` offers `fast`_, reproducible, cross-platform environment management that
enables us to `resolve`_ and provision robust, consistent environments
blended from both ``conda`` and ``PyPI`` ecosystems.

.. note::
  :class: margin, dropdown, toggle-shown

  We follow *Scientific Python Ecosystem Coordination* (`SPEC`_)
  recommendation for *Minimum Supported Dependencies* (`SPEC 0`_), and
  typically support the latest **2-3** distributions of ``python``.

We offer several similar **collections** of ``pixi`` environments for each
supported version of ``python``. Each environment within a collection belongs
to the same `solve-group`_ i.e., environments within the **same** solve-group
have their **dependencies resolved at the same time**, which means that all
those environments share the exact same dependencies but may also include
additional dependencies compatible with the solve-group.


:fa:`circle-nodes` Pixi Solve-Groups
------------------------------------

Our ``pixi`` **environments** are organized into collections by `solve-group`_.
See the ``[tool.pixi.environments]`` table defined in the ``pyproject.toml``
manifest file.

The **primary** solve-group is called :guilabel:`&d&e&f&a&u&l&t` and will always
contain the **latest** supported version of ``python``.

Several **secondary** solve-groups are available, each of which are named
after the version of ``python`` that they support e.g., :guilabel:`&p&y&3&1&1`,
:guilabel:`&p&y&3&1&2`, and :guilabel:`&p&y&3&1&3`.

The number of ``python`` versioned solve-groups on offer at any given
time is dictated by `SPEC 0`_.

.. table:: Solve-Group: :guilabel:`&d&e&f&a&u&l&t`
   :widths: 1 2 5
   :align: center

   +----------------------+------------------------+--------------------------------------------------+
   | Environment          | Features               | Description                                      |
   +======================+========================+==================================================+
   | :guilabel:`default`  | ``default``, ``py3xx`` | This environment contains the **core**           |
   |                      |                        | dependencies of ``geovista`` along with the      |
   |                      |                        | **latest** version of ``python``. See the        |
   |                      |                        | ``[tool.pixi.dependencies]`` table in the        |
   |                      |                        | ``pyproject.toml`` manifest file.                |
   +----------------------+------------------------+--------------------------------------------------+
   | :guilabel:`devs`     | ``default``, ``devs``, | As per the :guilabel:`default` environment plus  |
   |                      | ``py3xx``              | additional **development** dependencies.         |
   +----------------------+------------------------+--------------------------------------------------+
   | :guilabel:`docs`     | ``default``, ``devs``, | As per the :guilabel:`devs` environment plus     |
   |                      | ``docs``, ``py3xx``    | additional **documentation** dependencies.       |
   +----------------------+------------------------+--------------------------------------------------+
   | :guilabel:`geovista` | ``default``, ``devs``, | This environment is the **union** of all         |
   |                      | ``docs``, ``py3xx``,   | environments in the :guilabel:`&d&e&f&a&u&l&t`   |
   |                      | ``test``               | solve-group.                                     |
   +----------------------+------------------------+--------------------------------------------------+
   | :guilabel:`test`     | ``default``, ``devs``, | As per the :guilabel:`devs` environment plus     |
   |                      | ``py3xx``, ``test``    | additional **test** dependencies.                |
   +----------------------+------------------------+--------------------------------------------------+

The generic solve-group :guilabel:`&p&y&3&x&x` is used here as a convenience to
represent each of the ``python`` versioned solve-groups available, which are identical
in structure and content apart from the version of ``python`` that they
support.

.. attention::
   :class: dropdown, toggle-shown

   The :guilabel:`&p&y&3&x&x` solve-group does **not** exist.

.. note::
   :class: dropdown, toggle-shown

   The :guilabel:`&d&e&f&a&u&l&t` solve-group will always mirror the
   :guilabel:`&p&y&3&x&x` solve-group containing the **latest** supported
   version of ``python``.

.. table:: Solve-Group: :guilabel:`&p&y&3&x&x`
   :widths: 2 2 6
   :align: center

   +----------------------------+------------------------+-----------------------------------------------+
   | Environment                | Features               | Description                                   |
   +============================+========================+===============================================+
   | :guilabel:`devs-py3xx`     | ``default``, ``devs``, | As per the :guilabel:`py3xx` environment      |
   |                            | ``py3xx``              | plus additional **development** dependencies. |
   +----------------------------+------------------------+-----------------------------------------------+
   | :guilabel:`docs-py3xx`     | ``default``, ``devs``, | As per the :guilabel:`devs-py3xx` environment |
   |                            | ``docs`` , ``py3xx``   | plus additional **documentation**             |
   |                            |                        | dependencies.                                 |
   +----------------------------+------------------------+-----------------------------------------------+
   | :guilabel:`geovista-py3xx` | ``default``, ``devs``, | This environment is the **union** of all      |
   |                            | ``docs``, ``py3xx``,   | environments in the same                      |
   |                            | ``test``               | :guilabel:`&p&y&3&x&x` solve-group.           |
   +----------------------------+------------------------+-----------------------------------------------+
   | :guilabel:`py3xx`          | ``default``, ``py3xx`` | This environment contains the **core**        |
   |                            |                        | dependencies of ``geovista`` along with       |
   |                            |                        | ``python`` version ``py3xx`` e.g., ``py313``. |
   +----------------------------+------------------------+-----------------------------------------------+
   | :guilabel:`test-py3xx`     | ``default``, ``devs``, | As per the :guilabel:`devs-py3xx` environment |
   |                            | ``py3xx``, ``test``    | plus additional **test** dependencies.        |
   +----------------------------+------------------------+-----------------------------------------------+


:fa:`puzzle-piece` Pixi Features
--------------------------------

A ``pixi`` environment is defined by combining one or more :term:`features <Feature>`.
For further details see this ``pixi`` `tutorial`_ on how to create and use
features in a multi-environment scenario.

Our features are defined under the ``[tool.pixi.feature.<feature-name>.*]``
table in the ``pyproject.toml`` manifest file.

Each named `feature table`_ e.g., ``[tool.pixi.feature.devs]``, may contain
various fields, such as ``dependencies``, ``pypi-dependencies``,
``pypi-options``, ``system-requirements``, ``activation``, ``platforms``,
``channels``, ``channel-priority``, ``target`` and ``tasks``.

.. table:: Features
   :widths: 1 2 6
   :align: center

   +-------------+----------------------------------+------------------------------------------------+
   | Feature     | TOML Table                       | Field Description                              |
   +=============+==================================+================================================+
   | ``default`` | ``[tool.pixi.dependencies]``     | This feature is used to define the **core**    |
   |             |                                  | dependencies of ``geovista``. Note that the    |
   |             |                                  | ``default`` feature is                         |
   |             |                                  | `automatically included`_ in all environments  |
   |             |                                  | by ``pixi``.                                   |
   +-------------+----------------------------------+------------------------------------------------+
   | ``devs``    | ``[tool.pixi.feature.devs.*]``   | This feature is used to define the             |
   |             |                                  | **development** ``dependencies``,              |
   |             |                                  | ``pypi-dependencies`` and ``tasks``. Note      |
   |             |                                  | that an **editable** install of ``geovista``   |
   |             |                                  | is performed by the ``devs`` feature.          |
   +-------------+----------------------------------+------------------------------------------------+
   | ``docs``    | ``[tool.pixi.feature.docs.*]``   | This feature is used to define the             |
   |             |                                  | **documentation** ``dependencies``,            |
   |             |                                  | ``pypi-dependencies`` and ``tasks``.           |
   +-------------+----------------------------------+------------------------------------------------+
   | ``py3xx``   | ``[tools.pixi.feature.py3xx.*]`` | This feature is used to explicitly define the  |
   |             |                                  | version of ``python`` supported e.g.,          |
   |             |                                  | ``py313``. Note that the ``dependencies`` of   |
   |             |                                  | this feature additionally includes the ``pip`` |
   |             |                                  | package.                                       |
   +-------------+----------------------------------+------------------------------------------------+
   | ``test``    | ``[tool.pixi.feature.test.*]``   | This feature is used to define the **test**    |
   |             |                                  | ``dependencies`` and ``tasks``.                |
   +-------------+----------------------------------+------------------------------------------------+


:fab:`github` Continuous Integration
------------------------------------

The `ci-locks.yml`_ workflow regularly schedules ``pixi`` to refresh the
``pixi.lock`` file based on the ``pyproject.toml`` manifest and the
latest package versions available from the ``conda`` and ``PyPI`` ecosystems.

Only the **latest** :guilabel:`geovista-py3xx` environment will be exported to
a ``conda`` explicit specification file (``*.txt``) and converted to an equivalent explicit environment YAML file (``*.yml``). These resources are available in the `requirements/locks`_ directory.

The :guilabel:`geovista-py3xx` environment will also be exported to the ``conda``
environment YAML file `requirements/geovista.yml`_ containing only the top-level
dependencies of the environment, as defined by its features.


:fab:`python` Python Package Index
----------------------------------

The ``PyPI`` dependencies are configured in the ``pyproject.toml`` manifest file
under the ``[tool.setuptools.dynamic]`` and
``[tool.setuptools.dynamic.optional-dependencies]`` tables.

The version management of ``pip`` package-ecosystem dependencies is orchestrated
by :fab:`github` `Dependabot`_. Refer to the `.github/dependabot.yml`_ file for
further details.


.. _Dependabot: https://docs.github.com/en/code-security/getting-started/dependabot-quickstart-guide
.. _SPEC: https://scientific-python.org/specs/
.. _SPEC 0: https://scientific-python.org/specs/spec-0000/
.. _.github/dependabot.yml: https://github.com/bjlittle/geovista/blob/main/.github/dependabot.yml
.. _automatically included: https://pixi.sh/latest/tutorials/multi_environment/#default
.. _ci-locks.yml: https://github.com/bjlittle/geovista/blob/main/.github/workflows/ci-locks.yml
.. _fast: https://prefix.dev/blog/sharded_repodata
.. _feature table: https://pixi.sh/latest/reference/pixi_manifest/#the-feature-table
.. _requirements/geovista.yml: https://github.com/bjlittle/geovista/blob/main/requirements/geovista.yml
.. _requirements/locks: https://github.com/bjlittle/geovista/tree/main/requirements/locks
.. _resolve: https://pixi.sh/latest/workspace/environment/#solving-environments
.. _solve-group: https://pixi.sh/latest/workspace/multi_environment/#feature-environment-set-definitions
.. _tutorial: https://pixi.sh/latest/tutorials/multi_environment/
