.. include:: ../common.txt

.. _gv-reference-about:
.. _tippy-gv-reference-about:

:fa:`circle-info` About
=======================

Assorted package metadata about ``geovista``.


:fa:`feather-pointed` Citation
------------------------------

.. |zenodo| image:: https://zenodo.org/badge/DOI/10.5281/zenodo.7608302.svg
    :target: https://zenodo.org/doi/10.5281/zenodo.7608302

|zenodo|

If ``geovista`` has assisted with your academic research or work, then please
remember to cite us:

.. literalinclude:: ../../../CITATION.cff
    :language: text


.. _gv-reference-about-community:
.. _tippy-gv-reference-about-community:

:fa:`heart-circle-plus` Community
---------------------------------

Head over to our :fab:`github` `Discussions`_ to engage with the
``geovista`` community. Feel free to ask questions, share ideas, discuss topics,
and even showcase your work in our :fab:`github` `🍬 Candy Store`_. Go for it!

And add a touch of panache to your :bash:`README.md` with our badge |geovista-badge|:

.. tab-set::

    .. tab-item:: html

        .. code:: html

            <a href="https://geovista.readthedocs.io/" >
            <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/bjlittle/geovista/main/docs/assets/badge/v0.json" />
            </a>

    .. tab-item:: markdown
        :selected:

        .. code:: markdown

            [![geovista](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/bjlittle/geovista/main/docs/assets/badge/v0.json)](https://geovista.readthedocs.io/)

    .. tab-item:: rst

        .. code:: rst

            .. |geovista-badge| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/bjlittle/geovista/main/docs/assets/badge/v0.json
                :target: https://geovista.readthedocs.io/

.. tip::
   :class: dropdown

   Customize the look and feel of the badge by appending :bash:`&style=<option>`
   to the endpoint URL.

   See the `shields.io documentation`_ for further details.


:fa:`file-code` Packages
~~~~~~~~~~~~~~~~~~~~~~~~

Share and discover projects using ``geovista``:

- `aeolus <https://github.com/exoclim/aeolus>`__: A library for analysing and visualising atmospheric model output.
- `geovista-slam <https://github.com/bjlittle/geovista-slam>`__: Generating Structured Local Area Model (SLAM) grids from unstructured meshes.
- `iris <https://github.com/SciTools/iris>`__: A powerful, format-agnostic, and community-driven Python package for analysing and visualising Earth science data.
- `uraster <https://github.com/changliao1025/uraster>`__: Transform raster datasets to unstructured meshes.

.. admonition:: Share with the community!
    :class: dropdown

    Click `here <https://github.com/bjlittle/geovista/edit/main/docs/src/reference/about.rst>`__ to
    add your project details and raise a :fa:`code-pull-request` `Pull-Request`_.


:fa:`users-line` Contributors
-----------------------------

.. |all-contributors| image:: https://img.shields.io/github/all-contributors/bjlittle/geovista?color=ee8449)

|all-contributors|

.. tip::
    :class: margin, dropdown, toggle-shown

    Anyone can use the |icon| `all-contributors bot 🤖`_  to acknowledge
    the efforts of others (or yourself 😉).


We follow the |icon| `all-contributors`_ specification. Contributions of
any kind to ``geovista`` are welcome!

It's important that we recognise and acknowledge **all** our contributors, not
just the ones who push code. So no matter how large or small, we're grateful
for your contribution and caring enough to make a difference.

A massive thank-you to all our awesome contributors (`Emoji Key ✨`_):

.. include:: ../../../CONTRIBUTORS.md
    :parser: myst_parser.sphinx_


:fa:`file-contract` License
---------------------------

.. |bsd-3-clause| image:: https://img.shields.io/github/license/bjlittle/geovista
    :target: https://github.com/bjlittle/geovista/blob/main/LICENSE

|bsd-3-clause|

``geovista`` is an open-source package distributed under the terms of the
`BSD-3-Clause`_ license.

.. literalinclude:: ../../../LICENSE
    :language: text


.. comment

    Page link URL resources in alphabetical order:


.. |icon| image:: https://raw.githubusercontent.com/all-contributors/all-contributors-cli/1b8533af435da9854653492b1327a23a4dbd0a10/assets/logo-small.svg
.. _all-contributors: https://github.com/all-contributors/allcontributors.org
.. _all-contributors bot 🤖: https://allcontributors.org/bot/usage/#all-contributors-add
.. _BSD-3-Clause: https://spdx.org/licenses/BSD-3-Clause.html
.. _🍬 Candy Store: https://github.com/bjlittle/geovista/discussions/1033
.. _Emoji Key ✨: https://allcontributors.org/emoji-key/
.. _shields.io documentation: https://shields.io/
