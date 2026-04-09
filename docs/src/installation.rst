.. include:: common.txt

.. _gv-installation:
.. _tippy-gv-installation:

:fa:`circle-down` Installation
==============================

:fa:`heart-circle-check` Stable
-------------------------------

The latest **stable release** of ``geovista`` is available on `conda-forge`_
and `PyPI`_, and can be easily installed:

.. tab-set::

    .. tab-item:: :iconify:`vscode-icons:file-type-conda` conda

        .. code:: console

            $ conda create --name myenv --channel conda-forge geovista
            $ conda activate myenv

        :iconify:`twemoji:information` Consult the ``conda``
        `Installation <https://docs.conda.io/projects/conda/en/stable/>`__
        instructions.

    .. tab-item:: :iconify:`devicon:pypi` pip

        .. code:: console

            $ pip install geovista

        :iconify:`twemoji:information` Consult the ``pip``
        `Installation <https://pip.pypa.io/en/stable/installation/#>`__
        instructions.

    .. tab-item:: :fa:`puzzle-piece` pixi
        :selected:

        .. code:: console

            $ pixi init myenv
            $ cd myenv
            $ pixi add geovista

        :iconify:`twemoji:information` Consult the ``pixi``
        `Installation <https://pixi.prefix.dev/latest/installation/>`__
        instructions.

    .. tab-item:: :iconify:`material-icon-theme:uv` uv

        .. code:: console

            $ uv pip install geovista

        :iconify:`twemoji:information` Consult the ``uv``
        `Installation <https://docs.astral.sh/uv/getting-started/installation/>`__
        instructions.

Additional package dependencies will be required by some of the
``geovista`` gallery :ref:`tippy-gv-examples`. If these are required
then instead install the latest **stable release** as follows:

.. tab-set::

    .. tab-item:: :iconify:`vscode-icons:file-type-conda` conda

        .. code:: console

            $ conda create --name myenv --channel conda-forge geovista pip
            $ conda activate myenv
            $ pip install geovista[exam]

        :iconify:`twemoji:information` `conda`_ users
        must also install `pip`_ into their environment.

    .. tab-item:: :iconify:`devicon:pypi` pip

        .. code:: console

            $ pip install geovista[exam]

    .. tab-item:: :fa:`puzzle-piece` pixi
        :selected:

        .. code:: console

            $ pixi init myenv
            $ cd myenv
            $ pixi add python
            $ pixi add --pypi geovista[exam]

    .. tab-item:: :iconify:`material-icon-theme:uv` uv

        .. code:: console

            $ uv pip install "geovista[exam]"


:fa:`heart-circle-plus` Latest
------------------------------

If you simply can't wait for the next **stable release** of ``geovista``, then
install the latest **development version** from the :fab:`github` ``main``
branch:

.. tab-set::

    .. tab-item:: :iconify:`vscode-icons:file-type-conda` conda

        .. code:: console

            $ conda create --name myenv --channel conda-forge pip
            $ conda activate myenv
            $ pip install git+https://github.com/bjlittle/geovista.git@main

    .. tab-item:: :iconify:`devicon:pypi` pip

        .. code:: console

            $ pip install git+https://github.com/bjlittle/geovista.git@main

    .. tab-item:: :fa:`puzzle-piece` pixi
        :selected:

        .. code:: console

            $ pixi init myenv
            $ cd myenv
            $ pixi add python
            $ pixi add --git https://github.com/bjlittle/geovista.git geovista --branch main --pypi

    .. tab-item:: :iconify:`material-icon-theme:uv` uv

        .. code:: console

            $ uv pip install "git+https://github.com/bjlittle/geovista.git@main"


:fa:`heart-circle-bolt` Developer
---------------------------------

.. image:: https://vhs.charm.sh/vhs-6tXpDhss6UKkT7lTOb1MDp.gif
   :class: only-light


.. image:: https://vhs.charm.sh/vhs-4uiTU9kKjpOVIOagaTNEQl.gif
   :class: only-dark


.. raw:: html

   <hr>


To configure a full **developer environment**, first clone the :fab:`github`
``geovista`` repository:

.. code:: console

    $ git clone git@github.com:bjlittle/geovista.git

Change to the ``geovista`` root directory of the cloned repository:

.. code:: console

    $ cd geovista

Now install ``geovista`` and all its dependencies:

.. tab-set::

    .. tab-item:: :iconify:`vscode-icons:file-type-conda` conda

        .. code:: console

            $ conda env create --file requirements/geovista.yml
            $ conda activate geovista

    .. tab-item:: :iconify:`devicon:pypi` pip

        .. code:: console

            $ pip install --editable .[all]

    .. tab-item:: :fa:`puzzle-piece` pixi
        :selected:

        .. code:: console

            $ pixi shell --environment geovista

    .. tab-item:: :iconify:`material-icon-theme:uv` uv

        .. code:: console

            $ uv pip install --editable ".[all]"

For extra credit, install our developer `pre-commit`_ git-hooks:

.. code:: console

    $ pre-commit install

Finally, you're good to roll 🥳
