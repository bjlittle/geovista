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
    * - ``bench spec §…``
      - :doc:`2026-11-09-benchmarks-design`
    * - ``checks spec §…``
      - :doc:`2026-10-23-repository-checks-design`
    * - ``crs spec §…``
      - :doc:`2026-10-23-globe-first-crs-design`
    * - └─ ``globe spec §…``
      - :doc:`2026-10-26-globe-heights-layers-design`
    * - |indent| └─ ``heights spec §…``
      - :doc:`2026-10-28-heights-as-data-design`
    * - |indent| └─ ``layers spec §…``
      - :doc:`2026-11-12-layers-design`
    * - |indent| └─ ``scene spec §…``
      - :doc:`2026-10-27-globe-scene-design`
    * - ``docs spec §…``
      - :doc:`2026-10-06-published-specs-design`
    * - └─ ``citation spec §…``
      - :doc:`2026-10-26-citation-links-design`
    * - └─ ``ledger spec §…``
      - :doc:`2026-10-30-decision-ledger-design`
    * - |indent| └─ ``items spec §…``
      - :doc:`2026-11-02-open-items-design`
    * - |indent| |indent| └─ ``order spec §…``
      - :doc:`2026-11-17-row-order-design`
    * - ``floors spec §…``
      - :doc:`2026-11-15-dependency-floors-design`
    * - ``positions spec §…``
      - :doc:`2026-11-06-missing-positions-design`
    * - ``typing spec §…``
      - :doc:`2026-10-06-type-coverage-design`
    * - ``zlevel spec §…``
      - :doc:`2026-10-08-planar-zlevel-design`

The Status column sums each specification's roadmap: 📋 not started, 🚧 how many of
its rows have landed, or ✅ complete, with any 💡 candidates counted beside it. The
build writes it, as docs spec §3.8 sets out.

A specification that extends another sits beneath it, and the specifications
of a family are listed root first, each child under its parent and siblings in
the order of their prefixes. Every specification names its family in its own
header banner: its **Lineage**, from the root of its family down to itself, and
its **Children**, the specifications that directly extend it. docs spec §3.7
sets out how a new specification takes its place in the table, and in the
banners of its family.

.. |indent| unicode:: 0xA0 0xA0 0xA0
   :trim:


.. note::

    The implementation plans derived from these specifications are tracked in
    the repository under `docs/src/developer/plans
    <https://github.com/bjlittle/geovista/tree/main/docs/src/developer/plans>`__,
    but deliberately not published here. A plan records what was intended
    before implementation and is not updated afterwards.

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


.. _gv-developer-specs-decisions:
.. _tippy-gv-developer-specs-decisions:

Decisions and Verification
--------------------------

Each specification records what was agreed in its Decisions section, and shows
in its Verification section whether each decision was delivered. Together they
are its ledger, which ledger spec §3.2, §3.3, §3.4 set out.

**Adding a decision.** Append it to the end of the list, never between two
others: a decision keeps its number for as long as the specification exists.
Open it with its state and its provenance, then its title:

.. code:: markdown

   7. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`1234`) — **The title.**
      Its reasoning.

In the same pull request, add its row to the Verification table, naming the
decision by its citation, as ``| §2 decision 7 | ⏳ pending | |``. The build
links the citation to the decision. A bare ``7`` is refused, since it reads as
any row, item or decision that the Evidence column cites
(ledger spec §2 decision 17).

**Citing a decision.** Write ``heights spec §2 decision 3``, or
``§2 decision 3`` inside the specification itself. One citation names one
decision, so two decisions take two citations. The build links each to the
decision.

**Retiring a decision.** A decision that no longer holds is retired, never
deleted. Change its state to ``🗄️ Retired``, with the retirement's date, who
retired it and its pull request, then ``; agreed`` and the original date and pull
request. Keep its text, and add a sentence saying why it was retired and what
replaced it, citing the replacement. Its row becomes ``🗄️ retired``. A correction
or a clarification that keeps a decision's meaning is an edit, not a retirement.

**Verifying a decision.** When a test exercises the decision, cite the decision
in the test's docstring or a comment, and make its row
``✅ verified (date, {pull}`1234`)``, naming the test file in the Evidence column.
The conventions test checks that the file exists and cites the decision. On the
rendered page, each test file the Evidence column names links to the first line
in it that cites the decision, at the commit or the release tag the
documentation was built from (ledger spec §2 decision 18).

**Signing off a decision.** Where no test can honestly show a decision, a
reviewer signs it off. The row becomes
``✍️ signed off (date, {user}`reviewer`, {pull}`1234`)``, and its Evidence says
what the reviewer checked. The reviewer named then adds the ``signed-off`` label
to the pull request. An agent never adds that label, since GitHub records the
account and not the person (ledger spec §2 decision 7). The pull request's
checks fail until the reviewer named adds it, and pass once they do. A pull
request merged without it is reported each night, and the reviewer can still
add the label to the merged pull request.

**The verification report.** To see the whole ledger at once, run:

.. code:: console

   $ pixi run -e test verification-report
   $ pixi run -e test verification-report heights

For every specification, or the one a prefix names, it shows the roadmap with
each row's status, then each decision with its state and every place in the
repository that cites it, grouped as source, tests, documentation,
specifications and plans, and last the open items, each with its state, the row
that owes it and how often it has moved. It flags a verified row whose test no
longer cites its decision, and a decision in force that nothing cites. It also
flags an item on its last move, which must settle or graduate when its row
lands, and an item owed by a row in progress, which that row's pull request
must answer. It is a view, never a check: it exits 0 whatever it finds
(ledger spec §3.8, items spec §3.9).

.. _gv-developer-specs-items:
.. _tippy-gv-developer-specs-items:

Open Items
----------

A specification's Open Items section tracks a gap found while delivering it:
an input the design missed, or a decision a test only partly held. Each item
has a state, where it was found, and an issue that tracks it, set out in
items spec §3.1, §3.2, §3.3, §3.4. Every specification's items are in that
grammar.

**Raising an item.** Append it to the end of the Open Items section, in the
same pull request that raises its issue, labelled ``spec: open item``:

.. code:: markdown

   7. **❓ Open** (🔎 2026-11-02, {pull}`1234` · 🎯 row N of §M ·
      🎫 {issue}`1235`) — **The title.** Its reasoning.

An agent may add the ``spec: open item`` label itself: it records what the
issue is, not anyone's judgement, unlike ``signed-off``
(items spec §2 decision 11).

**Citing an item or a row.** Write ``typing spec §8 item 9`` or
``item 9 of typing spec §8``, and ``§8 item 9`` or ``item 9 of §8`` inside the
specification itself. Cite a row the same way, as ``row 5 of §10``, or across
specifications as ``row 5 of crs spec §10``. The build links each to the item or row it names.

**Owing it to a row.** 🎯 names a row of the item's own roadmap that has not
landed, the row whose work the gap belongs to. A row may not land while an
open or deferred item still names it: the pull request that lands it settles,
moves or promotes every item it owes.

**Moving it.** A pull request that lands a row without settling an item it
owes moves it instead, appending ⬅️ with the row it leaves and its date and
pull request, and the item becomes ``⏭️ Deferred``:

.. code:: markdown

   7. **⏭️ Deferred** (🔎 2026-11-02, {pull}`1234` · 🎯 row N of §M ·
      ⬅️ row 5, 2026-12-01, {pull}`1240` · 🎫 {issue}`1235`) —
      **The title.** Its reasoning.

An item may carry two ⬅️ and no more; at the third landing that owes it, it
must settle or graduate (items spec §3.6).

**Settling or promoting it at a landing.** The pull request that lands a row
owing an item resolves it, abandons it, or graduates it to a row of its own,
at least a ``💡 candidate``:

.. code:: markdown

   7. **🏁 Resolved** (2026-11-02, {pull}`1250` · 🔎 2026-11-02,
      {pull}`1234` · 🎫 {issue}`1235`) — **The title.** What was settled.

   7. **🚫 Abandoned** (2026-11-02, {pull}`1250` · 🔎 2026-11-02,
      {pull}`1234` · 🎫 {issue}`1235`) — **The title.** Why it was dropped.

   7. **🎓 Graduated** (2026-11-02, {pull}`1250`, to row N of §M ·
      🔎 2026-11-02, {pull}`1234` · 🎫 {issue}`1235`) — **The title.**

Resolving or abandoning closes the item's issue, by a closing keyword in the
pull request or by hand once it merges. Graduating carries the issue to the
new row instead, which cites it, and the issue keeps its label until that row
lands.

.. _gv-developer-specs-order:
.. _tippy-gv-developer-specs-order:

Ordering Roadmap Rows
---------------------

When a row depends on another, its Scope cell says so after the scope. Each
ordering opens with ``· 🔗``, and a row may carry several:

.. code:: markdown

   | # | Scope | Status |
   |---|---|---|
   | 1 | Tiers on a map | 📋 not started |
   | 2 | Tiers on the globe · 🔗 after row 1 | 📋 not started |
   | 3 | The lift · 🔗 after row 2 · 🔗 with row 2 of heights spec §9 | 📋 not started |

An ordering states one of four relations, and names one row:

.. list-table::
    :header-rows: 1
    :widths: 25 75

    * - Relation
      - The row lands
    * - ``after``
      - in a later pull request than the row it names
    * - ``before``
      - in an earlier pull request
    * - ``with``
      - in the same pull request
    * - ``with or after``
      - in the same pull request, or a later one

A bare ``row 1`` is a row of the same roadmap, and a row of another
specification is cited in full, as ``row 2 of layers spec §9``. Write each
ordering once, on the row its reason belongs to: the row that waits, or the
earlier row for ``before``. A ``with`` between two specifications goes on the
row whose work the other row does. A release takes ``before`` alone, as
``· 🔗 before 0.6``.

The reasons stay in the paragraph under the table, and the ordering never
does: the conventions test refuses one written in prose, such as *row 3 needs
row 1*, and points you at the cell.

The test also reads the orderings of every roadmap together, as one graph, and
refuses a cycle, such as row 2 after row 1 and row 1 after row 2, or a ``with``
and a ``before`` between the same two rows; a ``📋 not started`` row waiting on
a ``💡 candidate``, which may never land; and a status the order contradicts. A
row starts only once the rows it comes after have landed, and lands on their day
or later, in a pull request of its own, while two rows ``with`` each other land
in the same one.

A row ``with`` another lands in one pull request with it, and that pull request
answers the open items both rows owe. So for each row in progress, the
verification report lists any row it lands with that still owes open items, and
names those items.
order spec §4.1 sets out the form, order spec §4.5 what the test refuses, and
order spec §4.6 what the report shows.

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
    2026-11-02-open-items-design
    2026-11-06-missing-positions-design
    2026-11-09-benchmarks-design
    2026-11-12-layers-design
    2026-11-15-dependency-floors-design
    2026-11-17-row-order-design
