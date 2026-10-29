# Repository Checks Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the code, not archived
> behind it. It states how `geovista` documents the checks it enforces on its own
> repository, and how a contributor gets from a failing check to the reason for it. Read it
> as current; the roadmap states what has actually landed.

- **Date:** 2026-10-23 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `checks spec §…`
- **Scope:** the checks `geovista` wrote to hold its own repository to a rule, the page that
  documents them, and the gate that keeps the two in step. Third-party tools are out of
  scope for now, and §4 keeps a row for them
- **Lineage:** **checks spec**
- **Children:** none
- **Published:** in the specifications index

(checks-spec-1)=
## 1. Purpose

`geovista` holds its repository to a number of rules that no third-party tool knows about.
A test that renders must carry the `image` marker. A page a reader reads start to finish
must open with a reading-time banner. No `mypy` override may relax strict mode beyond the
three the type coverage specification gives reasons for. When this specification was
written there were eight such rules, each enforced by a test or a script, and several
allowed an exception, declared in a list beside the check:

| check | enforced by | where an exception goes |
|---|---|---|
| image marker | `tests/test_image_marker.py` | `EXEMPT`, in that module |
| reading-time banner | `tests/docs/test_readingtime_coverage.py` | `EXEMPT`, in that module |
| strict typing | `tests/test_ci_typing.py` | `RELAXED`, in that module |
| Python support | `tests/test_python_support.py` | none |
| parallel-safe extensions | `tests/docs/test_ext_parallel.py` | none |
| specification conventions | `tests/test_spec_conventions.py` | none |
| changelog fragment | `.github/scripts/changelog.py`, run by `ci-changelog.yml` | the `skip-changelog` label |
| specification statuses | `.github/scripts/check_status_references.py`, run by `ci-spec-status.yml` | none |

`EXCLUDED_DIRS`, beside `EXEMPT`, is not an exception: it names trees that Sphinx does not
publish as written. `NUMBERED_CEILING`, in the specification conventions, is not one
either. It is the trigger of row 5 of citation spec §9, and raising
it is a change to that specification. It replaced `CEILING`, the trigger of rows 2 to 4 of
docs spec §4, which retired when those rows were built.

A contributor usually meets one of these checks by failing it. The failure says what is
wrong but not why the rule exists, or whether an exception is allowed and where it goes.
Three are written up in the developer guide: the image marker under testing, the
reading-time banner under documentation, and the changelog fragment under changelog
quality assurance, which `changelog.py` already links to. The Python support test is
mentioned where the guide describes the documentation workflows. The rest are explained
in their own docstrings, in `AGENTS.md`, or nowhere a contributor would look.

This specification gives every one of them a section on a single page, and makes every
failure point at its section.

The table above is where the design started, and is not kept current. The
{ref}`repository checks page <gv-developer-checks>` is the inventory, and the gate of
§3.4 fails whenever a check has no section there, so a new check
needs no change here. The first added since is dependency ceilings, in
`tests/test_dependency_ceilings.py` ({pull}`2729`).

(checks-spec-2)=
## 2. Decisions

- **One page, for a reader who has just failed a check.** The page is
  `docs/src/developer/checks.rst`, titled "Repository Checks". A reader arrives from a
  failure and reads one section, so the page is built to be dipped into rather than read
  through. Chosen by {user}`bjlittle` on 2026-10-23, over a page per kind of failure,
  because separate pages make it harder to find a similar check in another group.
- **Only `geovista`'s own checks, for now.** Exceptions to third-party tools, such as a
  `# noqa`, a `filterwarnings` entry or a `nitpick_ignore_regex` pattern, are documented by
  those tools. They may join later, and §4 keeps a row for them, so
  nothing in the first version may assume they never will.
- **A check with no exception still gets a section.** Knowing there is no way round a rule
  saves a contributor looking for one.
- **The breadcrumb points at `latest`.** That is the documentation of `main`, which is what
  a contributor's branch is compared against.
- **The page is written by hand, and a gate keeps it honest.** Generating the table from
  the checks would need a Sphinx extension reading test modules, which is more machinery
  than the nine rows it began with justify. See §5.
- **The gate is a check too.** A contributor who adds or removes a check and fails the gate
  has just failed a check, so the gate has a name and a section of its own, which made
  nine when it landed.
- **Existing write-ups stay where they are.** The image marker, reading-time and changelog
  quality assurance sections of the developer guide are linked from the new page, not
  moved, so links to them keep working.
- **The page carries no reading-time banner.** It is a lookup, consulted for one entry, so
  it joins `EXEMPT` in `tests/docs/test_readingtime_coverage.py` with that reason, as the
  rule it documents requires.

(checks-spec-3)=
## 3. Design

(checks-spec-3-1)=
### 3.1 The Page

The page opens with one line telling a reader who has just failed a check to find it
below. A lookup table follows, split by where the failure is seen: a test, a pre-commit
hook, a CI job or the documentation build. Each row names the check, where an exception to
it goes, and links to its section. The first version has rows in two of those groups, a
test and a CI job. The hook and documentation build groups fill when third-party tools
join, so the table's shape does not change when they do. Every check is on the one page,
so a browser's find searches all of them at once.

Each check has a section, in the order of the table, and every section has the same parts:

1. **The rule**, in a sentence.
2. **Why**, which is what the failure message cannot say.
3. **What enforces it**, the test module or script, and when it runs.
4. **When it fails**, what to do in the usual case.
5. **Declaring an exception**, where it goes and what it must carry, or that there is none.
6. **More**, a link to the fuller write-up or specification, where one exists.

The page joins the developer guide's toctree, with a card on its index like its
neighbours. The page states that third-party tools are not yet covered.

(checks-spec-3-2)=
### 3.2 Naming a Check

Each check declares its name once, as a module-level constant in the module that enforces
it:

```python
#: The section of the repository checks page that documents this check.
CHECK = "image-marker"
```

The name is lower case words joined by hyphens, and is the stem of the section's labels,
`gv-developer-checks-<name>` and `tippy-gv-developer-checks-<name>`, following the labels
of the rest of the developer guide. One module enforces one check, as each of the eight
of §1 does, and only the module that enforces a check declares its
name. A module that tests a check's script, such as `tests/test_status_references.py`,
declares none. The gate of §3.4 is named `repository-checks`.

(checks-spec-3-3)=
### 3.3 The Breadcrumb

Every failure of a check ends with the same two lines, naming its section:

```text
Why this check exists, and how to declare an exception:
https://geovista.readthedocs.io/en/latest/developer/checks.html#gv-developer-checks-image-marker
```

For the six checks that are test modules, a `pytest_runtest_makereport` hook in
`tests/conftest.py` adds the breadcrumb to the report of any failed test whose module
declares `CHECK`. The individual assertions are left alone. That covers every assertion in
a module, including those added later, without a contributor having to remember to add the
breadcrumb. It also covers a module's tests of its own helpers, which is right, since a
fault there is a fault in the check.

The two scripts print the breadcrumb themselves, built from the same text. That text is
defined once, in a module that needs nothing beyond the standard library, because
`ci-changelog.yml` runs `changelog.py` from `.github/scripts` with only `click` and
`towncrier` installed. `tests/conftest.py` and the scripts load it by path, as
`check_status_references.py` already loads `tests/test_spec_conventions.py`.

A script prints the breadcrumb only for a finding, a rule the pull request breaks. A
failure to run the check is not a finding, so a `towncrier` configuration error, a missing
pull request number, or GitHub being unreachable prints none. `changelog.py` writes its
findings to the job summary as well as the log, and the breadcrumb goes to both. Its
existing link to the changelog quality assurance section is replaced by the breadcrumb,
whose section links on to it. The nightly drift run files what the status script prints as
an issue, so the breadcrumb reaches that issue too.

(checks-spec-3-4)=
### 3.4 The Gate

A test reads every `CHECK` declared under `tests/` and `.github/scripts/`, and the page,
and fails unless the two agree:

- every declared name has a row in the table and a section carrying its labels;
- every row and section on the page belongs to a name that is declared;
- no name is declared twice.

The second rule is what retires a section. Deleting a check deletes its `CHECK`, and the
gate then fails until its row and section go too. The gate reads the source as text,
needing neither `sphinx` nor a build, as `tests/docs/test_readingtime_coverage.py` does,
so it never skips.

The gate does not check the breadcrumb itself. The hook adds it to every test module that
declares `CHECK`, so only the two scripts could leave it out, and a test of each script
that drives a failure covers them.

(checks-spec-4)=
## 4. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | The page, the nine `CHECK` names, the breadcrumb hook and script output, and the gate | ✅ landed (2026-10-23, {pull}`2707`) |
| 2 | Third-party tools: `ruff`, `mypy` type-ignore comments, `filterwarnings`, `nitpick_ignore_regex`, `zizmor`, `codespell`, `numpydoc` and `repo-review` | candidate |

Statuses follow docs spec §3.6.

Row 2 is wanted when contributors are blocked by third-party exceptions often enough that
the tools' own documentation is not enough. That cannot be observed mechanically, so the
row is **revisited by hand**, when an issue or review asks how to declare such an
exception. Adding it fills the hook and documentation build groups of
§3.1. A third-party tool has no module of `geovista`'s to declare a
`CHECK` in, so row 2 also decides where its name is declared for the gate to find, and how
a breadcrumb reaches a failure the tool reports itself.

(checks-spec-5)=
## 5. Alternatives Considered

- **A page per kind of failure.** Grouping by where a check fails is useful, but on
  separate pages a reader in one group would not see a similar check in another.
  {user}`bjlittle` chose one page, with the groups inside it.
- **A generated table.** A Sphinx extension could read every `CHECK` and build the table,
  so it could not go stale. It would need to import or parse test modules during the
  build, and it would only save the work of the nine rows it began with. The gate gives
  the same guarantee for less.
- **A breadcrumb in every assertion message.** It works without a hook, but the checks
  hold 192 assertions between them, every new one would need it, and nothing would
  notice one without it.
- **A central registry of checks**, such as a TOML file listing them. It separates a check
  from its name, so deleting a check would leave the registry entry behind unless the gate
  read both anyway. A constant in the check's own module goes when the module does.

(checks-spec-6)=
## 6. Testing

- The gate of §3.4 runs against the repository, and against a
  small tree of its own showing that it fails for an undeclared section, a section whose
  check is gone, and a name declared twice.
- The hook is tested with `pytester`: a failing test in a module declaring `CHECK` reports
  the breadcrumb, and one in a module without it does not.
- Each script's findings are tested to print the breadcrumb, and its failures to run to
  print none. `check_status_references.py` is tested in `tests/test_status_references.py`.
  `changelog.py` is tested in `tests/test_changelog_script.py`, against `towncrier`
  itself, which the `test` feature carries for it, in a project the tests build and
  against this repository's own configuration.
- The page is built with `--fail-on-warning`, which checks its labels and links.

(checks-spec-7)=
## 7. Scope

In scope are the page, its card, toctree entry and `EXEMPT` entry, the `CHECK` constants
of the eight checks of §1 and of the gate, the hook, the scripts'
output, the gate and its tests. Out of scope are third-party tools, which row 2 of
§4 holds, and moving the existing write-ups of the image marker, the
reading-time banner and the changelog fragment. So is changing what any check enforces:
this specification documents the rules as they stand.

(checks-spec-8)=
## 8. Open Items

Each carries the status grammar of docs spec §3.6.

1. **Resolved** (2026-10-23, {pull}`2716`) — **`changelog.py` is tested only for its
   breadcrumb.** A stub let a test drive a finding without `towncrier`, but left the
   script's reading of `[tool.towncrier]`, and the findings themselves, untested.
   {user}`bjlittle` agreed to add `towncrier` to the `test` feature, so the script is now
   tested against it for every finding and both failures to run, and the stub is gone.
   Raised as {issue}`2704`.

(checks-spec-9)=
## 9. References

- {pull}`2703`, whose `RELAXED` table prompted this specification
- `tests/test_spec_conventions.py`, whose test of the specifications index against the
  specifications is the model for the gate of §3.4
- `tests/docs/test_readingtime_coverage.py`, which derives the pages it governs rather
  than listing them, the model for finding every `CHECK`
- `pytest`'s `pytest_runtest_makereport` hook:
  <https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_runtest_makereport>
