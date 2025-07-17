.. include:: common.txt

.. _gv-installation:
.. _tippy-gv-installation:

:fa:`circle-down` Installation
==============================

Stable
------

The latest **stable release** of ``geovista`` is available on `conda-forge`_
and `PyPI`_, and can be easily installed:

.. tab-set::

    .. tab-item:: conda-forge

        .. code:: console

            conda create --name myenv --channel conda-forge geovista

    .. tab-item:: pip

        .. code:: console

            pip install geovista

    .. tab-item:: pixi
        :selected:

        .. code:: console

            pixi init myenv
            cd myenv
            pixi add geovista

Additional package dependencies will be required by some of the
``geovista`` :ref:`examples <tippy-gv-examples>`. If these are required
then instead install the latest **stable release** as follows:

.. tab-set::

    .. tab-item:: conda-forge

        .. code:: console

            conda create --name myenv --channel conda-forge geovista pip
            conda activate myenv
            pip install geovista[exam]

    .. tab-item:: pip

        .. code:: console

            pip install geovista[exam]

    .. tab-item:: pixi
        :selected:

        .. code:: console

            pixi init myenv
            cd myenv
            pixi add python
            pixi add --pypi geovista[exam]

.. note::
    :class: dropdown

    `conda`_ users must also install `pip`_ into their environment.


Development
-----------

If you simply can't wait for the next **stable release** of ``geovista``, then
install the latest **development version** from the :fab:`github` ``main``
branch:

.. tab-set::

    .. tab-item:: conda

        .. code:: console

            conda create --name myenv --channel conda-forge pip
            conda activate myenv
            pip install git+https://github.com/bjlittle/geovista.git@main

    .. tab-item:: pip

        .. code:: console

            pip install git+https://github.com/bjlittle/geovista.git@main

    .. tab-item:: pixi
        :selected:

        .. code:: console

            pixi init myenv
            cd myenv
            pixi add python
            pixi add --git https://github.com/bjlittle/geovista.git geovista --branch main --pypi


Developer
^^^^^^^^^

To configure a full **developer environment**, first clone the :fab:`github`
``geovista`` repository:

.. code:: console

    git clone git@github.com:bjlittle/geovista.git

Change to the root directory of the cloned repository:

.. code:: console

    cd geovista

Now install ``geovista`` and all its dependencies:

.. tab-set::

    .. tab-item:: conda

        .. code:: console

            conda env create --file requirements/geovista.yml

    .. tab-item:: pip

        .. code:: console

            pip install --editable .[all]

    .. tab-item:: pixi
        :selected:

        .. code:: console

            pixi shell --environment geovista

For extra credit, install our developer `pre-commit`_ git-hooks:

.. code:: console

    pre-commit install

Finally, you're good to roll 🥳
