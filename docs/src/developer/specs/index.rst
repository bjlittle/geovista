.. include:: ../../common.txt

.. _gv-developer-specs:
.. _tippy-gv-developer-specs:

:fa:`compass-drafting` Specifications
=====================================

These are ``geovista``'s design specifications. Each is a living document,
maintained alongside the code it describes rather than archived behind it, so
read it as current. Where a specification and the code disagree, the
specification is what gets corrected, and the disagreement is worth reporting
as a defect in it.

The repository cites them by section. You will meet ``typing spec §3.2`` in
``pyproject.toml`` and ``docs spec §3.1`` in ``conf.py``, and each names a
section on one of the pages below. The prefix names the document, and it is
load-bearing: ``typing spec §3.2`` and ``docs spec §3.2`` are unrelated sections
of different documents. Wherever the documentation renders a citation in prose, in
a page, a specification or the API reference, it is a link to the section it names.

.. list-table::
    :header-rows: 1
    :widths: 35 65

    * - Citation
      - Document
    * - ``checks spec §…``
      - :doc:`2026-10-23-repository-checks-design`
    * - ``crs spec §…``
      - :doc:`2026-10-23-globe-first-crs-design`
    * - └─ ``globe spec §…``
      - :doc:`2026-10-26-globe-heights-layers-design`
    * - |indent| └─ ``heights spec §…``
      - :doc:`2026-10-28-heights-as-data-design`
    * - |indent| └─ ``scene spec §…``
      - :doc:`2026-10-27-globe-scene-design`
    * - ``docs spec §…``
      - :doc:`2026-10-06-published-specs-design`
    * - └─ ``citation spec §…``
      - :doc:`2026-10-26-citation-links-design`
    * - └─ ``ledger spec §…``
      - :doc:`2026-10-30-decision-ledger-design`
    * - ``typing spec §…``
      - :doc:`2026-10-06-type-coverage-design`
    * - ``zlevel spec §…``
      - :doc:`2026-10-08-planar-zlevel-design`

A specification that extends another sits beneath it, and the specifications
of a family are listed root first, each child under its parent and siblings in
the order of their prefixes. Every specification names its family in its own
header banner: its **Lineage**, from the root of its family down to itself, and
its **Children**, the specifications that directly extend it. docs spec §3.7
sets out how a new specification takes its place in the table, and in the
banners of its family.

.. |indent| unicode:: 0xA0 0xA0 0xA0
   :trim:


.. _gv-developer-specs-statuses:
.. _tippy-gv-developer-specs-statuses:

Statuses
--------

Every roadmap row and open item in a specification carries a status, and a
finished one names the work that finished it, as in
``✅ landed (2026-10-06, {pull}`2565`)``.
docs spec §3.6 sets out the vocabulary, and what each
status must cite.

When you change a status, check it against GitHub before you push, giving the
number of your pull request so that a status may cite it while it is still
open, e.g., for pull request ``1234``:

.. code:: console

   $ pixi run -e test check-spec-status 1234

The check confirms that a ``landed`` row cites merged pull requests on its
date, and that a **Resolved** or **Abandoned** item cites work that exists. The
``ci-spec-status.yml`` workflow runs it on every pull request that changes a
specification. Each night it also runs with ``drift``, to report a status the
work has moved past, such as an **Open** item whose issue has closed.

.. tip::
   :class: dropdown, toggle-shown

   Without a token, GitHub allows 60 requests an hour. Set ``GH_TOKEN`` to
   raise the limit, e.g., ``GH_TOKEN="$(gh auth token)"``.

.. note::

    The implementation plans derived from these specifications are tracked in
    the repository under `docs/src/developer/plans
    <https://github.com/bjlittle/geovista/tree/main/docs/src/developer/plans>`__,
    but deliberately not published here. A plan records what was intended
    before implementation and is not updated afterwards.

.. toctree::
    :hidden:

    2026-10-06-published-specs-design
    2026-10-06-type-coverage-design
    2026-10-08-planar-zlevel-design
    2026-10-23-globe-first-crs-design
    2026-10-23-repository-checks-design
    2026-10-26-citation-links-design
    2026-10-26-globe-heights-layers-design
    2026-10-27-globe-scene-design
    2026-10-28-heights-as-data-design
    2026-10-30-decision-ledger-design
