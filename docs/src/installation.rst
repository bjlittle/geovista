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

            conda install -c conda-forge geovista

    .. tab-item:: PyPI

        .. code:: console

            pip install geovista

Additional package dependencies will be required by some of the
``geovista`` :ref:`Gallery Examples <tippy-gv-examples>`.

These packages may be installed with:

.. code:: console

    pip install geovista[exam]

.. note::
    :class: dropdown

    `conda`_ users should also install `pip`_ into their `conda`_ environment.


Development
-----------

If you simply can't wait for the next **stable release** of ``geovista``, then
install the latest **development version** from the ``main`` development branch
of :fab:`github`:

.. tab-set::

    .. tab-item:: conda

        Include the following in your `conda environment.yml file`_:

        .. code:: yaml

            - pip
            - pip:
              - git+https://github.com/bjlittle/geovista@main

    .. tab-item:: pip

        .. code:: console

            pip install git+https://github.com/bjlittle/geovista@main


Developer
^^^^^^^^^

To configure a full **developer environment**, first clone the ``geovista``
repository from :fab:`github`:

.. code:: console

    git clone git@github.com:bjlittle/geovista.git

Change to the root directory of cloned repository:

.. code:: console

    cd geovista

Create the ``geovista-dev`` `conda`_ environment:

.. code:: console

    conda env create --file requirements/geovista.yml


Now **activate** the environment and **install** the ``main`` development
branch of ``geovista``:

.. code:: console

    conda activate geovista-dev
    pip install --no-deps --editable .

Finally, you're good to roll 🥳

And for extra credit, install our developer `pre-commit`_ git-hooks:

.. code:: console

    pre-commit install

.. note::
    :class: dropdown

    Please ensure to install `pre-commit`_ into your environment first.
