---
orphan: true
---

# type coverage change 1 — the hook and the ratchet

```{readingtime}
```

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** make `mypy` check `geovista` against the real third-party types, from both a
`pre-commit` hook and a CI job, with the 642 errors that check finds held in an explicit
per-module ratchet that a test only ever lets shrink.

**Architecture:** the `mirrors-mypy` hook is replaced by a `local` hook invoking the
locked pixi environment's own `mypy`, and skipped on `pre-commit.ci`, which has no `pixi`;
`.github/workflows/ci-typing.yml` runs the identical command so that coverage is not lost.
Every module carrying errors is listed once under `ignore_errors`, which makes the check
green today and leaves each module to be retired by its own later change.

**Tech Stack:** `mypy` 1.x in strict mode, `pixi` (conda-forge), `pre-commit`, GitHub
Actions, `pytest`, `tomllib`, `PyYAML`.

**Spec:** `docs/src/developer/specs/2026-10-06-type-coverage-design.md` — cited throughout
as `typing spec §…`. This plan implements change 1 of {ref}`§4 <typing-spec-4>`.

## Global Constraints

- **Copyright header.** Every Python file opens with the four-line BSD header given in the
  root `AGENTS.md`, followed by `from __future__ import annotations`. Both are ruff-enforced.
- **Line length 88.** `[tool.ruff]` in `pyproject.toml`.
- **Docstrings.** NumPy style. `numpydoc-validation` is `files: "^src/"`, so it does not
  reach `tests/`, but `--doctest-modules` is on: a `>>>` in any docstring is executed.
- **`taplo-format` sorts keys, not arrays.** `reorder_keys=true`, `reorder_arrays=false`,
  so within each `[[tool.mypy.overrides]]` block the keys land alphabetically while the
  `module` list keeps the order written.
- **No source lines are fixed here.** Change 1 is 0 lines of library correction. Anything
  that changes behaviour belongs to changes 2 to 7.
- **The strictness settings stay as they are** — `strict`, `warn_unreachable` and the three
  `enable_error_code` entries (typing spec {ref}`§7 <typing-spec-7>`).
- **`mypy`'s `python_version` stays `3.13`**, the support floor, held there by
  `tests/test_python_support.py`.
- **Changelog.** One towncrier fragment named `{PR}.contributor.rst`, signed
  ``:user:`claude` ``. The `agentic` label must be passed explicitly to `gh pr create`;
  the `debt/` branch prefix earns `type: tech-debt` automatically.
- **Pinned actions.** Workflows pin third-party actions by commit SHA, matching the
  existing `ci-*.yml` files; `zizmor` checks this on commit.

## Two corrections this plan makes to the spec

Both were measured on 2026-10-06 against current `main` and both contradict the spec as
written. The spec is a living document, so change 1 corrects it (task 5).

1. **The ratchet needs 23 entries, not 22.** With the 22 library modules ignored and the
   {ref}`§3.4 <typing-spec-3-4>` suppression applied, `mypy` still reports **28 errors**
   in `examples/` — 8 `import-untyped` and the 20 genuine lines the roadmap assigns to
   change 7. Change 1 is specified as fixing 0 lines, so it cannot be green without
   `geovista.examples.*` in the ratchet. That entry is removed by change 7.
2. **The two legacy overrides are not redundant.** Spec {ref}`§3.1 <typing-spec-3-1>` says
   both "produce zero errors" once the real types are installed. Deleting them raises the
   total from 642 to **648**: three `untyped-decorator` errors in `cli.py` (`click`'s
   `main.command` decorator is untyped even though `click` ships `py.typed`), and three
   `misc` "cannot subclass … has type Any" errors in `qt.py`, because `pyvistaqt` is not
   installed in the locked environment at all. Both overrides stay. The subclassing one is
   *narrowed*: `geovista.geoplotter` and `geovista.report` report an identical 36 and 5
   errors with or without it, so only `geovista.qt` keeps it.

## Review Focus

Five failure modes the spec implies but does not pin. Each gets a test in the task that
owns the code.

1. **A second `[[tool.mypy.overrides]]` block carrying `ignore_errors = true`** bypasses
   the ratchet entirely without touching its list. The test must scan every override block
   in the manifest, not the ratchet block alone. → task 2, `test_ratchet_only_shrinks`.
2. **`module` accepts a bare string as well as an array.** The existing `geovista.cli`
   override is written `module = "geovista.cli"`, so a reader that assumes a list iterates
   the characters of the string and compares `"g"`, `"e"`, `"o"` against the baseline. →
   task 2, `test_ratchet_reads_a_bare_module_string`.
3. **A ratchet entry naming a module that no longer exists** keeps the list from shrinking
   and nothing reports it: `mypy` does not warn on an override that matches nothing. →
   task 2, `test_ratchet_entry_resolves`.
4. **A `local` hook present but absent from `ci.skip`** fails every `pre-commit.ci` run
   with `pixi: command not found`, which reads as infrastructure flake rather than a
   configuration error. → task 3, `test_mypy_hook_is_skipped_on_pre_commit_ci`.
5. **`ci-typing.yml` naming a pixi environment that is not declared** fails at setup, after
   the cache restore, with a message about the environment rather than about the manifest.
   → task 4, `test_ci_typing_names_a_declared_environment`.

---

### Task 1: The ratchet and the manifest

The whole of the `[tool.mypy]` configuration change, verified by `mypy` itself. No test
file yet — the deliverable is a green check, and `mypy` is what reports it.

**Files:**
- Modify: `pyproject.toml:84-99` (the three existing `[[tool.mypy.overrides]]` blocks)

**Interfaces:**
- Consumes: nothing.
- Produces: the 23-entry ratchet list, read verbatim by task 2's `RATCHET_BASELINE`, and
  the `[[tool.mypy.overrides]]` shape task 2 parses — `ignore_errors: bool` plus
  `module: str | list[str]`.

- [ ] **Step 1: Record the failing baseline**

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, last line `Found 642 errors in 70 files (checked 86 source files)`.

If the count differs, stop: the measurement this plan rests on has moved, and the ratchet
list below needs re-deriving with

```bash
pixi run --frozen -e geovista mypy 2>&1 \
  | grep -oE '^src/geovista/[^:]+\.py' \
  | grep -v '^src/geovista/examples/' \
  | sort -u
```

- [ ] **Step 2: Replace the three override blocks**

Replace `pyproject.toml:84-99` in full. The `geovista.cli` block is unchanged; the
subclassing block loses two of its three names; two new blocks follow.

```toml
[[tool.mypy.overrides]]
# Problem caused by the click module - out of our control. "click" ships
# "py.typed", but "main.command" is still an untyped decorator: removing
# this raises three "untyped-decorator" errors. See typing spec 3.1.
disallow_untyped_decorators = false
module = "geovista.cli"


[[tool.mypy.overrides]]
# Subclassing third-party classes - out of our control. "pyvistaqt" is not
# in the locked environment at all, so its base classes are "Any". The same
# setting was redundant for "geovista.geoplotter" and "geovista.report",
# which report identically with and without it. See typing spec 3.1.
disallow_subclassing_any = false
module = ["geovista.qt"]


[[tool.mypy.overrides]]
# Problem caused by geopy being untyped.
disable_error_code = ["union-attr"]
module = ["geovista.examples.grid.*"]


[[tool.mypy.overrides]]
# typing spec 3.4 -- two "pyvista" stub defects, both verified against the
# runtime on 2026-10-06 with pyvista 0.49.0: "_Wrapped" loses the descriptor
# protocol, and "Plotter.camera" resolves only partially so ".zoom" is
# unreachable. Confined to the gallery, whose scripts are published as
# example code, so a "type: ignore" comment in one is a directive a reader
# is invited to copy. Withdraw when upstream fixes them.
disable_error_code = ["attr-defined", "call-arg"]
module = ["geovista.examples.*"]


[[tool.mypy.overrides]]
# typing spec 3.2 -- the ratchet. This list only ever shrinks, and
# "tests/test_typing_ratchet.py" holds it to that. Delete the whole block,
# and that test, when the last entry goes.
ignore_errors = true
module = [
  "geovista.bridge",
  "geovista.cache",
  "geovista.cli",
  "geovista.common",
  "geovista.config",
  "geovista.core",
  "geovista.crs",
  "geovista.filters",
  "geovista.geodesic",
  "geovista.geometry",
  "geovista.geoplotter",
  "geovista.gridlines",
  "geovista.pantry",
  "geovista.pantry.data",
  "geovista.pantry.meshes",
  "geovista.pantry.textures",
  "geovista.qt",
  "geovista.raster",
  "geovista.report",
  "geovista.search",
  "geovista.themes",
  "geovista.transform",
  "geovista.examples.*",
]
```

`geovista.examples.*` sits last rather than alphabetically, because it is the one entry
that is not a library module and the one change 7 removes alongside its 20 lines.
`reorder_arrays=false` means `taplo` leaves that where it is written.

- [ ] **Step 3: Verify the check is green**

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 0, `Success: no issues found in 86 source files`.

- [ ] **Step 4: Verify the ratchet is doing the work, not the suppressions**

Temporarily delete the `"geovista.transform",` line and re-run.

Expected: exits 1 with errors in `src/geovista/transform.py` only. Restore the line and
confirm the check returns to `Success`. This proves the entry is live rather than shadowed
by a broader override.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "deps: ratchet the mypy errors per module"
```

---

### Task 2: The ratchet test

**Files:**
- Create: `tests/test_typing_ratchet.py`

**Interfaces:**
- Consumes: the `[[tool.mypy.overrides]]` blocks written by task 1.
- Produces: `RATCHET_BASELINE: frozenset[str]` (23 entries), `_ignored() -> frozenset[str]`,
  `_modules(override: dict[str, Any]) -> tuple[str, ...]` and
  `_resolve(module: str) -> Path | None`. Task 3 adds a test to this same file and reuses
  its `ROOT` constant.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_typing_ratchet.py`:

```python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that the "mypy" ratchet only ever shrinks.

GeoVista type checks in strict mode against the locked pixi environment, where
the third-party types are real. That check reports errors in 22 of the 25
library modules and in the example gallery, which cannot be corrected in one
reviewable change, so the affected modules are listed once under
``ignore_errors`` and retired one change at a time.

A ratchet with nothing holding it becomes a dumping ground. These tests read
the manifest as text and hold the list to shrinking: an entry may be removed,
and nothing may be added. They are deleted along with the override block when
the last entry goes.

See "docs/src/developer/specs/2026-10-06-type-coverage-design.md", section 3.2.

"""

from __future__ import annotations

from functools import cache
from pathlib import Path
import tomllib
from typing import Any

import pytest

#: The repository root, holding the manifest the ratchet lives in.
ROOT = Path(__file__).parents[1]
#: The manifest declaring the "mypy" configuration and its overrides.
PYPROJECT = ROOT / "pyproject.toml"
#: The package root, against which each ratchet entry is resolved.
SOURCE = ROOT / "src"

#: Every module "mypy" was told to ignore when the ratchet was banked, on
#: 2026-10-06. Entries come off as each change retires a module; none may be
#: added. "geovista.examples.*" is the one entry that is not a library module,
#: and goes with change 7 of the roadmap.
RATCHET_BASELINE = frozenset(
    {
        "geovista.bridge",
        "geovista.cache",
        "geovista.cli",
        "geovista.common",
        "geovista.config",
        "geovista.core",
        "geovista.crs",
        "geovista.examples.*",
        "geovista.filters",
        "geovista.geodesic",
        "geovista.geometry",
        "geovista.geoplotter",
        "geovista.gridlines",
        "geovista.pantry",
        "geovista.pantry.data",
        "geovista.pantry.meshes",
        "geovista.pantry.textures",
        "geovista.qt",
        "geovista.raster",
        "geovista.report",
        "geovista.search",
        "geovista.themes",
        "geovista.transform",
    }
)


def _modules(override: dict[str, Any]) -> tuple[str, ...]:
    """Return the modules an override applies to.

    Parameters
    ----------
    override : dict
        One ``[[tool.mypy.overrides]]`` block, as parsed.

    Returns
    -------
    tuple of str
        The modules named, however they were written. "mypy" accepts a bare
        string as well as an array, and the "geovista.cli" override uses one,
        so iterating the value directly would yield its characters.

    """
    module = override.get("module", ())
    return (module,) if isinstance(module, str) else tuple(module)


@cache
def _ignored() -> frozenset[str]:
    """Return every module "mypy" is told to ignore errors in.

    Returns
    -------
    frozenset of str
        Collected from *all* override blocks rather than from the ratchet
        alone, so that a second block carrying ``ignore_errors`` cannot route
        around the baseline.

    """
    manifest = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    overrides = manifest["tool"]["mypy"].get("overrides", [])
    return frozenset(
        module
        for override in overrides
        if override.get("ignore_errors", False)
        for module in _modules(override)
    )


def _resolve(module: str) -> Path | None:
    """Return the file a ratchet entry names, if it still exists.

    Parameters
    ----------
    module : str
        A dotted module name, optionally ending in the ``.*`` wildcard.

    Returns
    -------
    Path or None
        The module file, or the package's "__init__.py", or ``None`` when the
        entry names nothing.

    """
    relative = Path(*module.removesuffix(".*").split("."))
    for candidate in (
        SOURCE / relative.with_suffix(".py"),
        SOURCE / relative / "__init__.py",
    ):
        if candidate.is_file():
            return candidate
    return None


def test_ratchet_only_shrinks():
    """An entry may be removed from the ratchet; none may be added."""
    added = _ignored() - RATCHET_BASELINE
    assert not added, f"added to the typing ratchet: {sorted(added)}"


@pytest.mark.parametrize("module", sorted(_ignored()))
def test_ratchet_entry_resolves(module):
    """Every entry names a module that still exists.

    "mypy" does not warn on an override matching nothing, so a renamed or
    deleted module leaves an entry that can never be retired.

    """
    assert _resolve(module) is not None, f"{module!r} names nothing under 'src'"


def test_ratchet_reads_a_bare_module_string():
    """A "module" written as a string yields the module, not its characters."""
    assert _modules({"module": "geovista.cli"}) == ("geovista.cli",)
    assert _modules({"module": ["geovista.qt"]}) == ("geovista.qt",)
    assert _modules({}) == ()


def test_ratchet_is_not_empty():
    """Guard the suite against passing vacuously once the list is gone.

    ``test_ratchet_only_shrinks`` is satisfied by an empty ratchet, which is
    the intended end state. Reaching it must delete this module rather than
    leave three tests quietly asserting nothing.

    """
    assert _ignored(), "the ratchet is empty: delete this module and the override"
```

- [ ] **Step 2: Run the tests to verify they pass against task 1**

Run: `pixi run --frozen -e geovista pytest tests/test_typing_ratchet.py -v`

Expected: PASS — 23 parametrized `test_ratchet_entry_resolves` cases plus three others.

- [ ] **Step 3: Prove `test_ratchet_only_shrinks` can fail**

Add `"geovista.bogus",` to the `module` list in `pyproject.toml` and re-run.

Expected: FAIL with `added to the typing ratchet: ['geovista.bogus']`, and
`test_ratchet_entry_resolves[geovista.bogus]` also FAILs with
`'geovista.bogus' names nothing under 'src'`. Remove the line and confirm both pass again.

- [ ] **Step 4: Prove the scan covers every override block**

Append a separate block to `pyproject.toml`, then re-run:

```toml
[[tool.mypy.overrides]]
ignore_errors = true
module = ["geovista.sneaky"]
```

Expected: FAIL with `added to the typing ratchet: ['geovista.sneaky']`. Delete the block
and confirm the suite is green.

- [ ] **Step 5: Commit**

```bash
git add tests/test_typing_ratchet.py
git commit -m "tests: hold the mypy ratchet to shrinking only"
```

---

### Task 3: The local hook

**Files:**
- Modify: `.pre-commit-config.yaml:6-10` (the `ci` block) and `:51-56` (the `mirrors-mypy` repo)
- Modify: `tests/test_typing_ratchet.py` (add one test and two imports)

**Interfaces:**
- Consumes: `ROOT` from task 2.
- Produces: a `local` hook with `id: mypy`, and `ci.skip` containing `mypy`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_typing_ratchet.py` — `import yaml` beside `import pytest`, and this
constant beside `PYPROJECT`:

```python
#: The hook configuration, which must skip "mypy" on "pre-commit.ci".
PRE_COMMIT = ROOT / ".pre-commit-config.yaml"
```

Then append:

```python
def test_mypy_hook_is_skipped_on_pre_commit_ci():
    """The local "mypy" hook needs "pixi", which "pre-commit.ci" has not got.

    Without the skip every "pre-commit.ci" run fails with "pixi: command not
    found", which reads as infrastructure flake rather than configuration.
    The coverage moves to ".github/workflows/ci-typing.yml".

    """
    config = yaml.safe_load(PRE_COMMIT.read_text(encoding="utf-8"))
    local = {
        hook["id"]
        for repo in config["repos"]
        if repo["repo"] == "local"
        for hook in repo["hooks"]
    }
    assert "mypy" in local, "the mypy hook is no longer local: is the skip needed?"
    assert "mypy" in config["ci"]["skip"]
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pixi run --frozen -e geovista pytest tests/test_typing_ratchet.py::test_mypy_hook_is_skipped_on_pre_commit_ci -v`

Expected: FAIL on the first assertion — `the mypy hook is no longer local` — because the
hook is still `mirrors-mypy`.

- [ ] **Step 3: Add the skip to the `ci` block**

In `.pre-commit-config.yaml`, the `ci` block gains one key:

```yaml
ci:
  autofix_prs: false
  autofix_commit_msg: "style: pre-commit.ci auto-fixes"
  autoupdate_commit_msg: "chore: update pre-commit hooks"
  autoupdate_schedule: "weekly"
  # typing spec 3.1 -- "mypy" runs against the locked pixi environment, which
  # "pre-commit.ci" has no way to build. Covered by "ci-typing.yml" instead.
  skip: [mypy]
```

- [ ] **Step 4: Replace the `mirrors-mypy` repo with a local hook**

Replace the whole `- repo: https://github.com/pre-commit/mirrors-mypy` entry, keeping its
position in the file so the hook's place in the run order does not move:

```yaml
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        # typing spec 3.1 -- an isolated "mirrors-mypy" venv installs "mypy"
        # and nothing else, so every third-party import resolves to "Any" and
        # the check succeeds against anything. "--frozen" resolves strictly
        # from "pixi.lock", so this is exactly the environment CI installs.
        # https://github.com/python/mypy/issues/13916 is why no filenames pass.
        entry: pixi run --frozen -e geovista mypy
        language: system
        pass_filenames: false
        types: [python]
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `pixi run --frozen -e geovista pytest tests/test_typing_ratchet.py -v`

Expected: PASS, all cases.

- [ ] **Step 6: Verify the hook itself runs**

Run: `pre-commit run mypy --all-files`

Expected: `mypy....Passed`. If it reports `pixi: command not found`, `pixi` is not on the
PATH `pre-commit` inherits — that is the hook working as designed and the developer's
environment that needs fixing, not the hook.

Then confirm the meta hooks still hold:

Run: `pre-commit run check-hooks-apply --all-files`

Expected: `Passed`. `types: [python]` keeps the hook applicable despite
`pass_filenames: false`.

- [ ] **Step 7: Commit**

```bash
git add .pre-commit-config.yaml tests/test_typing_ratchet.py
git commit -m "deps: type check against the locked environment"
```

---

### Task 4: The CI companion job

**Files:**
- Create: `.github/workflows/ci-typing.yml`
- Modify: `tests/test_typing_ratchet.py` (add one test and one constant)

**Interfaces:**
- Consumes: `ROOT` and `PYPROJECT` from task 2.
- Produces: a workflow named `ci-typing` with a job whose `setup-pixi` step names the
  `geovista` environment.

- [ ] **Step 1: Write the failing test**

Add this constant to `tests/test_typing_ratchet.py` beside `PRE_COMMIT`:

```python
#: The workflow carrying the coverage "pre-commit.ci" cannot provide.
WORKFLOW = ROOT / ".github" / "workflows" / "ci-typing.yml"
```

Then append:

```python
def test_ci_typing_names_a_declared_environment():
    """The workflow's pixi environment must exist in the manifest.

    A name that does not resolve fails the job at setup, with a message about
    the environment rather than about the manifest that should have declared
    it.

    """
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    manifest = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    declared = set(manifest["tool"]["pixi"]["environments"])
    named = {
        step["with"]["environments"]
        for job in workflow["jobs"].values()
        for step in job["steps"]
        if "setup-pixi" in str(step.get("uses", ""))
    }
    assert named, "ci-typing.yml sets up no pixi environment"
    assert named <= declared, f"undeclared: {sorted(named - declared)}"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pixi run --frozen -e geovista pytest tests/test_typing_ratchet.py::test_ci_typing_names_a_declared_environment -v`

Expected: FAIL with `FileNotFoundError` — the workflow does not exist yet.

- [ ] **Step 3: Create the workflow**

Create `.github/workflows/ci-typing.yml`. The action SHAs are copied verbatim from
`ci-docs.yml`, which is what keeps them consistent for `dependabot` to bump together. No
headless display and no data caches: `mypy` analyses source and runs nothing.

```yaml
# Reference:
#   - https://github.com/actions/checkout
#   - https://github.com/prefix-dev/setup-pixi

name: ci-typing

on:
  pull_request:

  push:
    branches:
      - "main"
      - "v*x"
      - "!pixi-auto-update"
      - "!pre-commit-ci-update-config"
      - "!dependabot/*"
    tags:
      - "v*"

  workflow_dispatch:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

permissions: {}

jobs:
  typing:
    name: "mypy"
    runs-on: "ubuntu-latest"

    defaults:
      run:
        shell: bash -l {0}

    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          # "setuptools-scm" derives the version from the history, which the
          # editable install of "geovista" needs.
          fetch-depth: 0
          persist-credentials: false

      - name: "setup pixi"
        uses: prefix-dev/setup-pixi@d3f436a425481402e6a95a1d1fc10331c708cd9e
        with:
          environments: "geovista"
          frozen: true

      - name: "mypy"
        # typing spec 3.1 -- the identical command the "pre-commit" hook runs,
        # which "pre-commit.ci" skips for want of "pixi".
        run: |
          pixi run --frozen -e geovista mypy
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pixi run --frozen -e geovista pytest tests/test_typing_ratchet.py -v`

Expected: PASS, all cases.

- [ ] **Step 5: Verify the workflow parses as GitHub will read it**

Run: `pre-commit run check-github-workflows --files .github/workflows/ci-typing.yml`

Expected: `Passed`.

Run: `pre-commit run zizmor --files .github/workflows/ci-typing.yml`

Expected: `Passed`. If `zizmor` objects to the missing `permissions` on the job, add
`permissions: {}` at job level to match the strictest sibling workflow.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/ci-typing.yml tests/test_typing_ratchet.py
git commit -m "deps: add the ci-typing workflow"
```

---

### Task 5: The spec corrections and the changelog

The spec is a living document: where it and the code diverge, the spec is what gets
corrected. Both divergences are measured, and both are recorded above.

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-type-coverage-design.md` — §3.1, §3.2, §4
- Create: `changelog/{PR}.contributor.rst`

**Interfaces:**
- Consumes: the measurements in "Two corrections this plan makes to the spec".
- Produces: nothing other tasks read.

- [ ] **Step 1: Correct §3.1's claim about the existing overrides**

Replace the final paragraph of {ref}`§3.1 <typing-spec-3-1>` — the one beginning "Two of
the three existing" — with:

```markdown
The three existing `[[tool.mypy.overrides]]` blocks are narrowed, not deleted. Measured on
2026-10-06, removing them raises the total from 642 to 648. `disallow_untyped_decorators`
stays on `geovista.cli`: `click` ships `py.typed`, but `main.command` is an untyped
decorator and three commands depend on it. `disallow_subclassing_any` stays on
`geovista.qt`, where `pyvistaqt` is absent from the locked environment altogether, so its
three base classes are `Any`. The same setting is redundant for `geovista.geoplotter` and
`geovista.report`, which report an identical 36 and 5 errors either way, so those two names
come off its `module` list.
```

- [ ] **Step 2: Correct §3.2's count and the example in it**

In {ref}`§3.2 <typing-spec-3-2>`, change the opening sentence from "The twenty-two modules
carrying errors are listed once, with `ignore_errors`:" to:

```markdown
The twenty-two modules carrying errors are listed once with `ignore_errors`, alongside the
gallery. With the library ignored and the {ref}`§3.4 <typing-spec-3-4>` suppression
applied, `examples/` still reports 28 errors — 8 `import-untyped` and the 20 lines change 7
corrects — so `geovista.examples.*` joins the ratchet as a twenty-third entry and leaves
with change 7.
```

Then append `  "geovista.examples.*",` to the TOML example's `module` array, after the
`# the remaining twenty` comment.

- [ ] **Step 3: Update the roadmap**

In the {ref}`§4 <typing-spec-4>` table, change row 1's Status from `not started` to
`landed`, and row 7's Scope from "`examples/`, and the ratchet retired" to
"`examples/`, its ratchet entry, and the ratchet retired".

- [ ] **Step 4: Verify the docs still build**

Run, from `docs/`:

```bash
pixi run --frozen -e docs sphinx-build -b html -W --keep-going \
  -D plot_docstring=False -D plot_gallery=False \
  -D plot_inline=False -D plot_tutorial=False \
  -d _build/doctrees src _build/html
```

Expected: `build succeeded`, exit 0. Note this plan and the spec both carry
`orphan: true`; neither is in a toctree yet, and `myst_parser` builds both regardless.

Run: `pixi run --frozen -e geovista pytest tests/docs/test_readingtime_coverage.py`

Expected: PASS. Both pages carry a `{readingtime}` banner, so neither needs an `EXEMPT`
entry.

- [ ] **Step 5: Write the changelog fragment**

`contributor` rather than `internal`: the hook now requires `pixi` on the contributor's
PATH, which changes what a clone needs in order to commit.

Create `changelog/{PR}.contributor.rst`, substituting the real PR number:

```rst
``mypy`` now runs against the locked ``geovista`` pixi environment rather than
an isolated ``mirrors-mypy`` virtual environment. That environment installed
``mypy`` and nothing else, so every import from ``pyvista``, ``numpy``,
``pyproj`` and the rest resolved to ``Any``, and a check against ``Any``
succeeds against anything. Against the real types the same configuration
reports 642 errors in 22 of the 25 library modules.

The ``pre-commit`` hook is now a ``local`` one invoking that environment, and
is skipped on ``pre-commit.ci``, which has no ``pixi``; ``ci-typing.yml``
carries the same command. Contributors need ``pixi`` on PATH for the hook to
run. The 642 errors are held in a per-module ratchet that
``tests/test_typing_ratchet.py`` only lets shrink, so the check is live today
for anything outside it and each module is retired on its own.
(:user:`claude`)
```

- [ ] **Step 6: Validate the fragment**

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py {PR} "changelog/{PR}.contributor.rst"`

Expected: `🆗 Your changelog contribution looks good to me.`

- [ ] **Step 7: Run the whole suite and the hooks**

Run: `pixi run --frozen -e test tests-unit -m "not image"`

Expected: PASS. Image tests segfault without a GPU; CI is where they are meaningfully run.

Run: `pre-commit run --all-files`

Expected: all hooks pass. Read the full output rather than its tail — a failure between
passing hooks is easy to miss.

- [ ] **Step 8: Commit**

```bash
git add docs/src/developer/specs/2026-10-06-type-coverage-design.md changelog/
git commit -m "docs: correct the spec against the measured configuration"
```

---

## Done when

- `pixi run --frozen -e geovista mypy` exits 0.
- `tests/test_typing_ratchet.py` passes, and has been seen to fail when a module is added
  to the ratchet, when an entry names nothing, and when a second override block carries
  `ignore_errors`.
- `pre-commit run --all-files` passes, with `mypy` running from the pixi environment.
- `ci-typing.yml` is green on the pull request, alongside every existing check.
- The spec's §3.1, §3.2 and §4 agree with what the manifest actually says.
- The PR carries `agentic` and `type: tech-debt`.
