.. include:: ../common.txt

.. _gv-developer-checks:
.. _tippy-gv-developer-checks:

:fa:`shield-halved` Repository Checks
=====================================

If a check has failed, find it below. Each section says what the check holds
the repository to, why, and whether there is a way to declare an exception.

``geovista`` holds its own repository to a handful of rules that no third-party
tool knows about. A failure of any of them ends with a link to its section on
this page.

.. note::
   :class: dropdown

   This page covers the checks ``geovista`` wrote itself. Exceptions to
   third-party tools, such as a ``# noqa`` comment, a type-ignore comment, a
   ``filterwarnings`` entry or a ``nitpick_ignore_regex`` pattern, are
   documented by those tools, and may join this page later, as row 2 of
   :ref:`checks spec §4 <checks-spec-4>` describes.


Where It Failed
---------------

.. rubric:: A Test Failed

.. list-table::
    :header-rows: 1
    :widths: 35 65

    * - Check
      - Where an exception goes
    * - :ref:`Image Marker <gv-developer-checks-image-marker>`
      - ``EXEMPT`` in :bash:`tests/test_image_marker.py`
    * - :ref:`Reading-Time Banner <gv-developer-checks-reading-time-banner>`
      - ``EXEMPT`` in :bash:`tests/docs/test_readingtime_coverage.py`
    * - :ref:`Strict Typing <gv-developer-checks-strict-typing>`
      - ``RELAXED`` in :bash:`tests/test_ci_typing.py`
    * - :ref:`Python Support <gv-developer-checks-python-support>`
      - none
    * - :ref:`Dependency Ceilings <gv-developer-checks-dependency-ceilings>`
      - none
    * - :ref:`Parallel-Safe Extensions <gv-developer-checks-parallel-safe-extensions>`
      - none
    * - :ref:`Specification Conventions <gv-developer-checks-spec-conventions>`
      - none
    * - :ref:`Projection Coverage <gv-developer-checks-projection-coverage>`
      - none
    * - :ref:`Repository Checks <gv-developer-checks-repository-checks>`
      - none

.. rubric:: A CI Job Failed

.. list-table::
    :header-rows: 1
    :widths: 35 65

    * - Check
      - Where an exception goes
    * - :ref:`Changelog Fragment <gv-developer-checks-changelog-fragment>`
      - the ``skip-changelog`` label
    * - :ref:`Specification Statuses <gv-developer-checks-spec-statuses>`
      - none


.. _gv-developer-checks-image-marker:
.. _tippy-gv-developer-checks-image-marker:

Image Marker
------------

**The rule:** Every test that renders, by showing, plotting, screenshotting or
exporting a scene, carries ``@pytest.mark.image``, on the test, its class or
its module.

**Why:** Rendering needs a display or a GPU, and without one it can crash the
process, taking its ``pytest-xdist`` worker with it. ``pytest -m "not image"``
is how a contributor without either runs the suite, which is only safe if every
test that draws is marked. CI renders under a virtual display, so a missing
marker never fails a test there.

**What enforces it:** :bash:`tests/test_image_marker.py`, which reads the source
of every test module, in every run of the unit tests.

**When it fails:** The message names each test that renders unmarked. Add the
marker. Two other faults are reported too: a test marked ``example`` but not
``image``, as the gallery image tests are a subset of the image tests, so mark
it ``image`` as well; and an entry in ``EXEMPT`` naming a test that no longer
exists, which you remove.

**Declaring an exception:** A test that only appears to draw goes in ``EXEMPT``
in :bash:`tests/test_image_marker.py`, with the reason as its value. A reviewer
will ask about it.

**More:** :ref:`Image test markers <gv-developer-testing-image-tests-markers>`.


.. _gv-developer-checks-reading-time-banner:
.. _tippy-gv-developer-checks-reading-time-banner:

Reading-Time Banner
-------------------

**The rule:** Every page a reader reads from start to finish opens with one
``readingtime`` banner, after its title and before its first section.

**Why:** The banner tells a reader how long the page will take. A page without
one would be ambiguous between a page that needs none and a page nobody got
round to.

**What enforces it:** :bash:`tests/docs/test_readingtime_coverage.py`, which
reads every page under :bash:`docs/src` as text, so a new page is covered the
day it lands. It needs neither ``sphinx`` nor a build, so it runs in every run of
the unit tests and never skips.

**When it fails:** Add the banner to the page named, or remove a second one.

**Declaring an exception:** A page that is navigated rather than read, such as
a landing page, a generated body, a lookup table or an include of another page,
goes in ``EXEMPT`` in :bash:`tests/docs/test_readingtime_coverage.py`, with the
reason as a comment beside it. ``EXCLUDED_DIRS`` is not for exceptions: it names
trees that ``sphinx`` does not publish as written.

**More:** :ref:`The readingtime directive <gv-developer-documentation-sphinx-directives-readingtime>`.


.. _gv-developer-checks-strict-typing:
.. _tippy-gv-developer-checks-strict-typing:

Strict Typing
-------------

**The rule:** ``mypy`` checks the whole package in strict mode. No override may
ignore a module's errors, nothing at the top of ``[tool.mypy]`` may silence one,
no module may configure ``mypy`` with a ``# mypy:`` comment, and the only
per-module relaxations of strict mode are those listed in ``RELAXED``.

**Why:** The package became fully type checked one module at a time. A single
line of configuration could hand that coverage back, and nothing in a passing
``mypy`` run would show it.

**What enforces it:** :bash:`tests/test_ci_typing.py`, in every run of the unit
tests. It also holds :bash:`.github/workflows/ci-typing.yml` to running the
``mypy`` hook that ``pre-commit.ci`` skips.

**When it fails:** Fix the type error rather than silence it. Where the cause is
upstream, bind an annotated local, as the type coverage specification describes.

**Declaring an exception:** A per-module relaxation goes in ``RELAXED`` in
:bash:`tests/test_ci_typing.py` and in ``pyproject.toml``, only with a reason the
type coverage specification gives. There is no exception to the other rules.

**More:** :ref:`typing spec §6 <typing-spec-6>`.


.. _gv-developer-checks-python-support:
.. _tippy-gv-developer-checks-python-support:

Python Support
--------------

**The rule:** Every place that states which versions of Python ``geovista``
supports agrees with the trove classifiers in ``pyproject.toml``.

**Why:** Support is stated in ten places: ``requires-python``, the ``pixi``
features and environments, the exported ``conda`` environment, the version
``mypy`` assumes, and the matrices of the workflows. Nothing else ties them
together, so a version bump that misses one leaves the repository advertising
one thing and testing another.

**What enforces it:** :bash:`tests/test_python_support.py`, in every run of the
unit tests.

**When it fails:** The message names the place that disagrees. Bring it into
line with the classifiers, then run ``pixi lock``.

**Declaring an exception:** None.

**More:** `SPEC 0`_, the support policy ``geovista`` follows.


.. _gv-developer-checks-dependency-ceilings:
.. _tippy-gv-developer-checks-dependency-ceilings:

Dependency Ceilings
-------------------

**The rule:** Every package in :bash:`requirements/pypi-*.txt` is also a ``pixi``
dependency in ``pyproject.toml``, and its ``pixi`` ceiling admits every version
its ``pip`` ceiling does.

**Why:** ``dependabot`` raises the ``pip`` ceilings and never touches the ``pixi``
ones, which have to follow by hand. A ``pixi`` ceiling left behind keeps the lock
on the old release, so CI never tests the version a ``pip`` user may install.
The ``pixi`` ceilings may be looser, since they pin the major version rather than
the minor, so a ``dependabot`` bump beneath one needs nothing more.

**What enforces it:** :bash:`tests/test_dependency_ceilings.py`, in every run of
the unit tests, including those on a ``dependabot`` pull request.

**When it fails:** The message names the package and both ceilings. Raise the
``pixi`` ceiling to match, on the same pull request, then run ``pixi update
<package>`` and confirm the new version with ``pixi list``. ``pixi lock`` alone
keeps the version already locked. A package conda-forge distributes under
another name, such as ``h3-py`` for ``h3``, goes in ``RENAMED``. That is a
mapping, not an exception.

**Declaring an exception:** None.

**More:** :ref:`Dependabot <gv-developer-codecraft-dependabot>`.


.. _gv-developer-checks-parallel-safe-extensions:
.. _tippy-gv-developer-checks-parallel-safe-extensions:

Parallel-Safe Extensions
------------------------

**The rule:** Every local ``sphinx`` extension, under :bash:`docs/src/_ext`,
declares that it is safe to read and to write in parallel.

**Why:** ``sphinx`` assumes an extension that does not declare it is unsafe, so
``sphinx-build --jobs``, as Read the Docs runs it, warns and reads serially,
which fails a build run with ``--fail-on-warning``.

**What enforces it:** :bash:`tests/docs/test_ext_parallel.py`, which discovers
the extensions, so a new one is covered the day it lands. It needs ``sphinx``, so
it skips in the unit test environments and runs where ``sphinx`` is installed: in
the :guilabel:`test docs chrome` job of ``ci-tests-docs.yml``, and locally with
``pixi run -e geovista``. Run it there before you push a change to an extension.

**When it fails:** Return ``parallel_read_safe`` and ``parallel_write_safe`` from
the extension's ``setup``.

**Declaring an exception:** None.

**More:** :ref:`Parallel builds <gv-developer-documentation-parallel>`.


.. _gv-developer-checks-spec-conventions:
.. _tippy-gv-developer-checks-spec-conventions:

Specification Conventions
-------------------------

**The rule:** The design specifications keep their conventions: every numbered
heading carries an anchor, a citation such as ``typing spec §3.2`` carries its
section sign and names an anchor that exists, and a status names the work that
produced it.

**Why:** The repository cites the specifications by section, in code comments,
tests and documentation, so a reader following a citation has to land on the
section it means.

**What enforces it:** :bash:`tests/test_spec_conventions.py`, which reads every
file in the repository as text, in every run of the unit tests.

**When it fails:** The message names the file, line and citation or heading at
fault.

**Declaring an exception:** None. Its ``CEILING`` is not an exception: it is the
trigger of rows 2 to 4 of :ref:`docs spec §4 <docs-spec-4>`, and raising it is a
change to that specification.

**More:** :ref:`docs spec §3.5 <docs-spec-3-5>`.


.. _gv-developer-checks-projection-coverage:
.. _tippy-gv-developer-checks-projection-coverage:

Projection Coverage
-------------------

**The rule:** Every projection method PROJ offers, and every projection class of
``cartopy``, is recorded as working or failing on a global mesh, and its outcome
changes only when that record does.

**Why:** No release may break a projection that works today, by decision 12 of
the CRS specification. The record shows which projections ``geovista`` handles,
and stops that set shrinking by accident while the seam and transform code is
rebuilt.

**What enforces it:** :bash:`tests/transform/test_projection_coverage.py`, in
every run of the unit tests. Each projection takes a global 5° mesh through
``transform_mesh``, and is measured for an exception, coordinates that are not
finite or run away, folded cells and torn cells.

**When it fails:** Move a projection that now works from ``FAILS`` to ``WORKS``,
or from ``CARTOPY_FAILS`` to ``CARTOPY_WORKS``. One that no longer works is a
regression to fix. Measure a projection that a new release of PROJ or
``cartopy`` adds into the record, and put an operation that is not a projection
in ``NOT_PROJECTIONS``. A method newer than the PROJ that ``pyproj``'s wheels
bundle also goes in ``SINCE``, with the version of PROJ it arrived in.

**Declaring an exception:** None. ``PARAMETERS`` gives a method the parameters
PROJ needs to build it, which is no exception to the rule.

**More:** :ref:`crs spec §6 <crs-spec-6>`.


.. _gv-developer-checks-repository-checks:
.. _tippy-gv-developer-checks-repository-checks:

Repository Checks
-----------------

**The rule:** Every check that declares ``CHECK`` has a row and a section on
this page, and every row and section belongs to a check that declares it.

**Why:** This page is only useful while it is complete and true. A check added
without a section would fail with a link to nothing, and a check removed would
leave a section describing a rule nobody enforces.

**What enforces it:** :bash:`tests/test_repository_checks.py`, which reads every
``CHECK`` under :bash:`tests` and :bash:`.github/scripts`, and this page, as
text, in every run of the unit tests.

**When it fails:** Add a row and a section for a new check, or remove those of a
check that has gone. A section carries both of its labels,
``gv-developer-checks-<name>`` and ``tippy-gv-developer-checks-<name>``. The
gate also fails when a ``CHECK`` is not a literal string assigned at the top of
its module, since it reads the source rather than running it; when a name is not lower-case words joined by
hyphens, since it becomes the stem of the labels; and when two modules declare
the same name, since one module enforces one check.

**Declaring an exception:** None.

**More:** :ref:`checks spec §3.4 <checks-spec-3-4>`.


.. _gv-developer-checks-changelog-fragment:
.. _tippy-gv-developer-checks-changelog-fragment:

Changelog Fragment
------------------

**The rule:** Every pull request adds a ``towncrier`` news fragment, named
``<PR>.<type>.rst`` for its own number and a configured type, that carries a
``:user:`` attribution.

**Why:** The changelog of each release is built from the fragments, so a change
without one is missing from the release notes.

**What enforces it:** :bash:`.github/scripts/changelog.py`, which
``ci-changelog.yml`` runs on every pull request.

**When it fails:** Add the fragment the message asks for, or correct its name or
type.

**Declaring an exception:** A maintainer adds the ``skip-changelog`` label to a
pull request that needs no entry. Bots and automated services get it
automatically.

**More:** The quality assurance section of the :ref:`changelog guidelines <gv-developer-towncrier>`.


.. _gv-developer-checks-spec-statuses:
.. _tippy-gv-developer-checks-spec-statuses:

Specification Statuses
----------------------

**The rule:** Every status in a specification that cites work cites work that
exists and did what the status says: a ``landed`` row cites merged pull
requests on its date, and a **Resolved** item cites real work.

**Why:** A status is how a reader learns what has happened, and one citing the
wrong pull request, or one that never merged, misleads them.

**What enforces it:** :bash:`.github/scripts/check_status_references.py`, which
``ci-spec-status.yml`` runs on every pull request that changes a specification,
and each night, when it also reports a status the work has moved past.

**When it fails:** Correct the status, or the work it cites. Run the check before
pushing, with the number of your pull request:

.. code:: console

   $ pixi run -e test check-spec-status 1234

**Declaring an exception:** None.

**More:** :ref:`Statuses <gv-developer-specs-statuses>`.
