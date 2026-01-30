.. include:: ../common.txt

.. _gv-developer-codecraft:
.. _tippy-gv-developer-codecraft:

:fa:`hat-wizard` Codecraft
==========================

.. |pre-commit| image:: https://results.pre-commit.ci/badge/github/bjlittle/geovista/main.svg
    :target: https://results.pre-commit.ci/latest/github/bjlittle/geovista/main

.. note::
    :class: margin, dropdown, toggle-shown

    We've just started to bank content for the :fa:`hat-wizard` **Codecraft**
    material, which will slowly grow and mature over time.

    Thanks for your patience 🙏


Here we provide some high-level maintenance guidelines, best practice and all-round sage
advice for contributors.


:fa:`code-pull-request` Dependabot
----------------------------------

:fa:`file-code` **Reference:**

- :bash:`.github/dependabot.yml`
- :bash:`.github/workflows/*.yml` (``github-actions``)
- :bash:`requirements/pypi-*.txt` (``pip``)
- :bash:`pyproject.toml` (``pip``, ``pixi``)

We use :fab:`github` `Dependabot`_ automation to maintain `cooldown period`_
dependency version updates for both the ``github-actions`` and ``pip`` ecosystems.

Note that we adhere to the **default** `unpinned-uses`_ (`zizmor`_ v1.20.0) audit
policy for ``github-actions`` which requires **hash-pinning** on **all** actions.

We adopt a ``minor`` `pinning-strategy`_ for ``pip`` ecosystem package dependencies
and ``semver`` (default) for our ``pixi`` package dependencies.

.. attention::
    :class: dropdown

    We heavily rely on ``dependabot`` to inform us of the constant version
    updates to our package dependencies available in the ``pip`` ecosystem.

    When merging an automated ``chore`` :fa:`code-pull-request` ``pull-request``
    from ``dependabot`` ensure to confirm whether any associated ``pixi``
    package version pins also require to be updated.

    If so, then raise a separate follow-on :fa:`code-pull-request` ``pull-request``.



.. comment

   🔗 URL resources in alphabetical order:


.. _cooldown period: https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference#cooldown
.. _pinning-strategy: https://pixi.prefix.dev/latest/reference/pixi_configuration/#pinning-strategy
.. _unpinned-uses: https://docs.zizmor.sh/audits/#unpinned-uses
